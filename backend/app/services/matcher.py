"""
Recipe Matching and Ranking Engine.

Documented Formula:
    core_coverage_score = round((matched_required_count / total_required_count) * 100, 1)

Rules:
- Required ingredients (`requirement_type == 'required'`) are included in the denominator.
- Optional ingredients (`requirement_type == 'optional'`) are excluded from the required coverage
  denominator so a recipe is not penalised for missing optional garnishes, while still reporting
  matched and missing optional ingredients transparently.
- Spices or seasonings marked as `required` in the recipe are NEVER silently omitted from the denominator.
- Never claims an ingredient is available if it is not in the user's normalised recognised ingredient set.
"""
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set
from sqlalchemy.orm import Session, joinedload

from app.models.entities import Recipe, RecipeIngredient
from app.services.normalizer import NormalisedIngredientResult, normalise_ingredients
from app.services.scaler import format_quantity_display


SCORE_FORMULA_EXPLANATION = (
    "Core ingredient coverage = (matched required ingredients / total required ingredients) × 100. "
    "Required spices and staples are included in the denominator; explicitly optional ingredients "
    "are tracked separately and excluded from the required coverage denominator."
)


@dataclass
class IngredientMatchDetail:
    ingredient_id: str
    canonical_name: str
    quantity: Optional[float]
    unit: str
    display_quantity: str
    requirement_type: str
    preparation_note: Optional[str]
    is_available: bool


@dataclass
class MatchedRecipeResult:
    recipe: Recipe
    core_coverage_score: float
    score_explanation: str
    total_required_count: int
    matched_required_count: int
    missing_required_count: int
    matched_optional_count: int
    missing_optional_count: int
    matched_required_ingredients: List[IngredientMatchDetail]
    missing_required_ingredients: List[IngredientMatchDetail]
    matched_optional_ingredients: List[IngredientMatchDetail]
    missing_optional_ingredients: List[IngredientMatchDetail]
    total_minutes: int


@dataclass
class SearchByIngredientsOutcome:
    normalised_user_ingredients: List[NormalisedIngredientResult]
    recognised_ingredient_ids: List[str]
    unrecognised_inputs: List[str]
    matched_recipes: List[MatchedRecipeResult]
    no_match_guidance: Optional[str]
    ranking_rule_summary: str
    score_formula_description: str


def evaluate_recipe_match(
    recipe: Recipe,
    available_ingredient_ids: Set[str],
) -> MatchedRecipeResult:
    """Evaluate a single recipe against a set of available canonical ingredient IDs."""
    matched_req: List[IngredientMatchDetail] = []
    missing_req: List[IngredientMatchDetail] = []
    matched_opt: List[IngredientMatchDetail] = []
    missing_opt: List[IngredientMatchDetail] = []

    # Sort recipe ingredients deterministically by id
    sorted_ri = sorted(recipe.recipe_ingredients, key=lambda item: item.id)

    for ri in sorted_ri:
        ing_name = ri.ingredient.canonical_name if ri.ingredient else ri.ingredient_id
        is_avail = ri.ingredient_id in available_ingredient_ids
        detail = IngredientMatchDetail(
            ingredient_id=ri.ingredient_id,
            canonical_name=ing_name,
            quantity=ri.quantity,
            unit=ri.unit,
            display_quantity=format_quantity_display(ri.quantity, ri.unit),
            requirement_type=ri.requirement_type,
            preparation_note=ri.preparation_note,
            is_available=is_avail,
        )
        if ri.requirement_type == "required":
            if is_avail:
                matched_req.append(detail)
            else:
                missing_req.append(detail)
        else:
            if is_avail:
                matched_opt.append(detail)
            else:
                missing_opt.append(detail)

    total_req = len(matched_req) + len(missing_req)
    matched_req_count = len(matched_req)
    missing_req_count = len(missing_req)

    if total_req > 0:
        score = round((matched_req_count / total_req) * 100.0, 1)
    else:
        score = 0.0

    total_minutes = int(recipe.preparation_minutes) + int(recipe.cooking_minutes)
    explanation = (
        f"Matched {matched_req_count} of {total_req} required ingredients ({score}%). "
        f"{missing_req_count} required ingredient(s) missing."
    )

    return MatchedRecipeResult(
        recipe=recipe,
        core_coverage_score=score,
        score_explanation=explanation,
        total_required_count=total_req,
        matched_required_count=matched_req_count,
        missing_required_count=missing_req_count,
        matched_optional_count=len(matched_opt),
        missing_optional_count=len(missing_opt),
        matched_required_ingredients=matched_req,
        missing_required_ingredients=missing_req,
        matched_optional_ingredients=matched_opt,
        missing_optional_ingredients=missing_opt,
        total_minutes=total_minutes,
    )


def search_recipes_by_ingredients(
    db: Session,
    raw_ingredients: Sequence[str],
    dietary_filters: Optional[Sequence[str]] = None,
    excluded_ingredients: Optional[Sequence[str]] = None,
    max_total_minutes: Optional[int] = None,
    difficulty: Optional[str] = None,
    cuisine: Optional[str] = None,
    sort_by: str = "best_match",
    include_zero_match: bool = False,
) -> SearchByIngredientsOutcome:
    """
    Normalise user ingredients, filter the catalogue, compute transparent match scores,
    and rank matching recipes deterministically.
    """
    normalised_list = normalise_ingredients(db, raw_ingredients)
    recognised_ids: Set[str] = {
        item.ingredient_id for item in normalised_list if item.is_recognised and item.ingredient_id
    }
    unrecognised_inputs = [
        item.raw_input for item in normalised_list if not item.is_recognised
    ]

    # Resolve excluded ingredients through the same normalisation pipeline
    excluded_ids: Set[str] = set()
    excluded_names: Set[str] = set()
    if excluded_ingredients:
        norm_excluded = normalise_ingredients(db, excluded_ingredients)
        for item in norm_excluded:
            if item.ingredient_id:
                excluded_ids.add(item.ingredient_id)
            excluded_names.add(item.normalised_input)

    required_diets = {d.strip().lower() for d in (dietary_filters or []) if d and d.strip()}

    recipes: List[Recipe] = (
        db.query(Recipe)
        .options(
            joinedload(Recipe.recipe_ingredients).joinedload(RecipeIngredient.ingredient),
            joinedload(Recipe.dietary_attributes),
            joinedload(Recipe.allergens),
        )
        .all()
    )

    candidate_matches: List[MatchedRecipeResult] = []

    for recipe in recipes:
        # 1. Check dietary filter compatibility
        if required_diets:
            recipe_diets = {attr.attribute.lower() for attr in recipe.dietary_attributes}
            if not required_diets.issubset(recipe_diets):
                continue

        # 2. Check excluded ingredients
        if excluded_ids or excluded_names:
            recipe_ing_ids = {ri.ingredient_id for ri in recipe.recipe_ingredients}
            recipe_ing_names = {
                ri.ingredient.canonical_name.lower()
                for ri in recipe.recipe_ingredients
                if ri.ingredient
            }
            if (excluded_ids & recipe_ing_ids) or (excluded_names & recipe_ing_names):
                continue

        # 3. Check max_total_minutes filter
        total_time = int(recipe.preparation_minutes) + int(recipe.cooking_minutes)
        if max_total_minutes is not None and total_time > max_total_minutes:
            continue

        # 4. Check difficulty filter
        if difficulty and recipe.difficulty.lower() != difficulty.strip().lower():
            continue

        # 5. Check cuisine filter
        if cuisine and (not recipe.cuisine or recipe.cuisine.lower() != cuisine.strip().lower()):
            continue

        match_result = evaluate_recipe_match(recipe, recognised_ids)

        # Only include recipes that match at least 1 required or optional ingredient unless include_zero_match
        has_any_match = (match_result.matched_required_count > 0) or (match_result.matched_optional_count > 0)
        if has_any_match or include_zero_match:
            candidate_matches.append(match_result)

    # Ranking according to documented rules
    sort_key = (sort_by or "best_match").strip().lower()
    if sort_key == "fewest_missing":
        candidate_matches.sort(
            key=lambda m: (
                m.missing_required_count,
                -m.core_coverage_score,
                -m.matched_required_count,
                m.total_minutes,
                m.recipe.name.lower(),
            )
        )
    elif sort_key == "shortest_time":
        candidate_matches.sort(
            key=lambda m: (
                m.total_minutes,
                -m.core_coverage_score,
                m.missing_required_count,
                m.recipe.name.lower(),
            )
        )
    elif sort_key == "alphabetical":
        candidate_matches.sort(key=lambda m: m.recipe.name.lower())
    else:
        # Default: best_match
        # Priority: 1. Higher required coverage %, 2. More matched required ingredients,
        # 3. Fewer missing required ingredients, 4. Shorter total cooking time, 5. Alphabetical
        candidate_matches.sort(
            key=lambda m: (
                -m.core_coverage_score,
                -m.matched_required_count,
                m.missing_required_count,
                -m.matched_optional_count,
                m.total_minutes,
                m.recipe.name.lower(),
            )
        )

    guidance: Optional[str] = None
    if not candidate_matches:
        if not recognised_ids and unrecognised_inputs:
            guidance = (
                f"None of the entered items ({', '.join(unrecognised_inputs)}) matched our canonical ingredient "
                "catalogue. Try common staples such as potato, onion, tomato, rice, egg, garlic, or pasta."
            )
        elif required_diets or max_total_minutes or difficulty or cuisine:
            guidance = (
                "No recipes matched both your ingredients and active filters. "
                "Try relaxing dietary, time, or difficulty filters, or add staple ingredients like onion, tomato, or rice."
            )
        else:
            guidance = (
                "No recipes matched the submitted ingredients. Try adding common base ingredients "
                "such as potato, onion, tomato, rice, or cooking oil."
            )
    elif all(m.missing_required_count > 0 for m in candidate_matches):
        best = candidate_matches[0]
        missing_names = ", ".join(i.canonical_name for i in best.missing_required_ingredients[:3])
        guidance = (
            f"Showing partial matches ranked by ingredient coverage. Your closest match is "
            f"'{best.recipe.name}' ({best.core_coverage_score}% coverage), which needs: {missing_names}."
        )

    return SearchByIngredientsOutcome(
        normalised_user_ingredients=normalised_list,
        recognised_ingredient_ids=sorted(recognised_ids),
        unrecognised_inputs=unrecognised_inputs,
        matched_recipes=candidate_matches,
        no_match_guidance=guidance,
        ranking_rule_summary=(
            "Ranked by: (1) highest required ingredient coverage %, (2) most required ingredients matched, "
            "(3) fewest missing required ingredients, (4) shortest total prep + cooking time, (5) alphabetical name."
        ),
        score_formula_description=SCORE_FORMULA_EXPLANATION,
    )
