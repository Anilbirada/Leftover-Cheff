"""REST API Endpoints for Leftover Chef."""
import json
from typing import List, Optional, Set
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user_id, sanitize_text
from app.models.entities import (
    Ingredient,
    IngredientAlias,
    Recipe,
    RecipeIngredient,
    ShoppingList,
    ShoppingListItem,
    UserFavourite,
    UserPantryItem,
)
from app.schemas.api_schemas import (
    AllergenInfoOut,
    FavouriteOut,
    HealthResponse,
    IngredientOut,
    MatchedRecipeOut,
    NormalisedIngredientOut,
    PantryItemCreate,
    PantryItemOut,
    PantryItemUpdate,
    RecipeDetailOut,
    RecipeIngredientOut,
    RecipeSummaryOut,
    ScaledIngredientOut,
    SearchByIngredientsRequest,
    SearchByIngredientsResponse,
    ServingScaleRequest,
    ServingScaleResponse,
    ShoppingListItemCreate,
    ShoppingListItemOut,
    ShoppingListItemUpdate,
    ShoppingListOut,
    UserProfileOut,
    UserProfileUpdate,
)
from app.services.ai_assistant import generate_recipe_match_explanation
from app.services.matcher import evaluate_recipe_match, search_recipes_by_ingredients
from app.services.normalizer import clean_ingredient_token, normalise_ingredients
from app.services.scaler import (
    can_combine_units,
    combine_compatible_quantities,
    format_quantity_display,
    scale_single_quantity,
)
from app.services.seed_service import ensure_user_exists


router = APIRouter(prefix="/api/v1")

FOOD_SAFETY_NOTICE = (
    "Food Safety Notice: Digital pantry records or best-before dates do not guarantee food safety. "
    "Always inspect ingredients for spoilage, off-odours, mould, or unsafe storage temperatures before cooking. "
    "Cooking does not make spoiled food safe to eat."
)

ALLERGEN_UNVERIFIED_DEFAULT = (
    "Allergen information not verified. Always check product packaging, cross-contamination risks, "
    "and individual ingredient labels."
)


def serialize_recipe_detail(
    recipe: Recipe,
    available_ids: Optional[Set[str]] = None,
) -> RecipeDetailOut:
    instructions = json.loads(recipe.instructions_json)
    sorted_ri = sorted(recipe.recipe_ingredients, key=lambda item: item.id)

    ing_out: List[RecipeIngredientOut] = []
    for ri in sorted_ri:
        cname = ri.ingredient.canonical_name if ri.ingredient else ri.ingredient_id
        is_avail = (ri.ingredient_id in available_ids) if available_ids is not None else None
        ing_out.append(
            RecipeIngredientOut(
                ingredient_id=ri.ingredient_id,
                canonical_name=cname,
                quantity=ri.quantity,
                unit=ri.unit,
                display_quantity=format_quantity_display(ri.quantity, ri.unit),
                requirement_type=ri.requirement_type,
                preparation_note=ri.preparation_note,
                is_available=is_avail,
            )
        )

    allergens_out: List[AllergenInfoOut] = []
    has_unverified = len(recipe.allergens) == 0
    for alg in recipe.allergens:
        if alg.verification_status != "verified":
            has_unverified = True
        allergens_out.append(
            AllergenInfoOut(
                allergen=alg.allergen,
                verification_status=alg.verification_status,
                source_reference=alg.source_reference,
            )
        )

    if has_unverified:
        allergen_notice = (
            "Allergen information not verified for all components. "
            "Substitutions, brand variations, and cross-contamination can affect allergen safety."
        )
    else:
        declared = [a.allergen for a in allergens_out if a.allergen != "none_declared_in_base_recipe"]
        if declared:
            allergen_notice = (
                f"Verified base recipe allergens: {', '.join(declared)}. "
                "Always check commercial packaging and guard against kitchen cross-contamination."
            )
        else:
            allergen_notice = (
                "No major allergens declared in base ingredients (verified against catalogue). "
                "Not a medical guarantee; verify commercial spice/oil labels for cross-contamination."
            )

    return RecipeDetailOut(
        id=recipe.id,
        name=recipe.name,
        description=recipe.description,
        preparation_minutes=recipe.preparation_minutes,
        cooking_minutes=recipe.cooking_minutes,
        total_minutes=recipe.preparation_minutes + recipe.cooking_minutes,
        default_servings=recipe.default_servings,
        difficulty=recipe.difficulty,
        cuisine=recipe.cuisine,
        image_reference=recipe.image_reference,
        source_reference=recipe.source_reference,
        licence_reference=recipe.licence_reference,
        dietary_attributes=[d.attribute for d in recipe.dietary_attributes],
        allergens=allergens_out,
        allergen_verification_notice=allergen_notice,
        food_safety_notice=FOOD_SAFETY_NOTICE,
        instructions=instructions,
        ingredients=ing_out,
    )


@router.get("/health", response_model=HealthResponse, tags=["System"])
def get_health(db: Session = Depends(get_db)) -> HealthResponse:
    """Report application health and catalogue counts without exposing secrets."""
    recipes_count = db.query(Recipe).count()
    ingredients_count = db.query(Ingredient).filter(Ingredient.active.is_(True)).count()
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        catalogue_recipes_count=recipes_count,
        catalogue_ingredients_count=ingredients_count,
        developer_credit=settings.developer_credit,
    )


@router.get("/recipes", response_model=List[RecipeSummaryOut], tags=["Recipes"])
def list_recipes(
    dietary: Optional[str] = Query(default=None, description="Filter by dietary attribute (e.g. vegan, gluten-free)"),
    cuisine: Optional[str] = Query(default=None, description="Filter by cuisine"),
    difficulty: Optional[str] = Query(default=None, description="Filter by difficulty (Easy, Medium, Hard)"),
    max_total_minutes: Optional[int] = Query(default=None, ge=1, le=600),
    sort_by: str = Query(default="alphabetical", description="alphabetical or shortest_time"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> List[RecipeSummaryOut]:
    """Return recipe catalogue summaries with supported filtering, sorting, and pagination."""
    recipes = (
        db.query(Recipe)
        .options(
            joinedload(Recipe.recipe_ingredients),
            joinedload(Recipe.dietary_attributes),
            joinedload(Recipe.allergens),
        )
        .all()
    )

    filtered: List[Recipe] = []
    for r in recipes:
        if dietary:
            attrs = {d.attribute.lower() for d in r.dietary_attributes}
            if dietary.strip().lower() not in attrs:
                continue
        if cuisine and (not r.cuisine or r.cuisine.lower() != cuisine.strip().lower()):
            continue
        if difficulty and r.difficulty.lower() != difficulty.strip().lower():
            continue
        total_min = r.preparation_minutes + r.cooking_minutes
        if max_total_minutes is not None and total_min > max_total_minutes:
            continue
        filtered.append(r)

    if sort_by == "shortest_time":
        filtered.sort(key=lambda r: (r.preparation_minutes + r.cooking_minutes, r.name.lower()))
    else:
        filtered.sort(key=lambda r: r.name.lower())

    sliced = filtered[offset : offset + limit]
    summaries: List[RecipeSummaryOut] = []
    for r in sliced:
        req_count = sum(1 for ri in r.recipe_ingredients if ri.requirement_type == "required")
        opt_count = sum(1 for ri in r.recipe_ingredients if ri.requirement_type != "required")
        has_unverified = (len(r.allergens) == 0) or any(
            a.verification_status != "verified" for a in r.allergens
        )
        allergen_notice = (
            "Allergen information not verified"
            if has_unverified
            else "Allergen metadata verified for base ingredients"
        )
        summaries.append(
            RecipeSummaryOut(
                id=r.id,
                name=r.name,
                description=r.description,
                preparation_minutes=r.preparation_minutes,
                cooking_minutes=r.cooking_minutes,
                total_minutes=r.preparation_minutes + r.cooking_minutes,
                default_servings=r.default_servings,
                difficulty=r.difficulty,
                cuisine=r.cuisine,
                image_reference=r.image_reference,
                dietary_attributes=[d.attribute for d in r.dietary_attributes],
                allergen_summary_notice=allergen_notice,
                required_ingredient_count=req_count,
                optional_ingredient_count=opt_count,
            )
        )
    return summaries


@router.get("/recipes/{recipe_id}", response_model=RecipeDetailOut, tags=["Recipes"])
def get_recipe_by_id(
    recipe_id: str,
    available_ingredients: Optional[str] = Query(
        default=None,
        description="Optional comma-separated available ingredients to highlight matched vs missing items.",
    ),
    db: Session = Depends(get_db),
) -> RecipeDetailOut:
    """Return one recipe with structured ingredients, ordered instructions, and allergen notices."""
    recipe = (
        db.query(Recipe)
        .options(
            joinedload(Recipe.recipe_ingredients).joinedload(RecipeIngredient.ingredient),
            joinedload(Recipe.dietary_attributes),
            joinedload(Recipe.allergens),
        )
        .filter(Recipe.id == recipe_id)
        .first()
    )
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe '{recipe_id}' not found.",
        )

    avail_set: Optional[Set[str]] = None
    if available_ingredients is not None:
        norm = normalise_ingredients(db, [available_ingredients])
        avail_set = {item.ingredient_id for item in norm if item.is_recognised and item.ingredient_id}

    return serialize_recipe_detail(recipe, available_ids=avail_set)


@router.post(
    "/recipes/search-by-ingredients",
    response_model=SearchByIngredientsResponse,
    tags=["Recipes"],
)
def api_search_recipes_by_ingredients(
    payload: SearchByIngredientsRequest,
    db: Session = Depends(get_db),
) -> SearchByIngredientsResponse:
    """
    Validate and normalise submitted ingredients, match against the structured recipe catalogue,
    compute transparent coverage scores, and return ranked results.
    """
    try:
        outcome = search_recipes_by_ingredients(
            db=db,
            raw_ingredients=payload.ingredients,
            dietary_filters=payload.dietary_filters,
            excluded_ingredients=payload.excluded_ingredients,
            max_total_minutes=payload.max_total_minutes,
            difficulty=payload.difficulty,
            cuisine=payload.cuisine,
            sort_by=payload.sort_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    avail_set = set(outcome.recognised_ingredient_ids)
    matched_out: List[MatchedRecipeOut] = []

    for m in outcome.matched_recipes:
        ai_out = None
        if payload.include_ai_explanation:
            suggestion = generate_recipe_match_explanation(m)
            ai_out = {
                "label": suggestion.label,
                "explanation": suggestion.explanation,
                "cooking_tip": suggestion.cooking_tip,
                "is_ai_generated": suggestion.is_ai_generated,
                "verification_status": suggestion.verification_status,
                "safety_disclaimer": suggestion.safety_disclaimer,
                "provider_status": suggestion.provider_status,
            }

        matched_out.append(
            MatchedRecipeOut(
                recipe=serialize_recipe_detail(m.recipe, available_ids=avail_set),
                core_coverage_score=m.core_coverage_score,
                score_explanation=m.score_explanation,
                total_required_count=m.total_required_count,
                matched_required_count=m.matched_required_count,
                missing_required_count=m.missing_required_count,
                matched_optional_count=m.matched_optional_count,
                missing_optional_count=m.missing_optional_count,
                matched_required_ingredients=[
                    RecipeIngredientOut(**vars(i)) for i in m.matched_required_ingredients
                ],
                missing_required_ingredients=[
                    RecipeIngredientOut(**vars(i)) for i in m.missing_required_ingredients
                ],
                matched_optional_ingredients=[
                    RecipeIngredientOut(**vars(i)) for i in m.matched_optional_ingredients
                ],
                missing_optional_ingredients=[
                    RecipeIngredientOut(**vars(i)) for i in m.missing_optional_ingredients
                ],
                ai_suggestion=ai_out,
            )
        )

    return SearchByIngredientsResponse(
        normalised_user_ingredients=[
            NormalisedIngredientOut(**vars(item)) for item in outcome.normalised_user_ingredients
        ],
        recognised_ingredient_ids=outcome.recognised_ingredient_ids,
        unrecognised_inputs=outcome.unrecognised_inputs,
        matched_recipes=matched_out,
        no_match_guidance=outcome.no_match_guidance,
        ranking_rule_summary=outcome.ranking_rule_summary,
        score_formula_description=outcome.score_formula_description,
        food_safety_notice=FOOD_SAFETY_NOTICE,
    )


@router.post(
    "/recipes/{recipe_id}/servings",
    response_model=ServingScaleResponse,
    tags=["Recipes"],
)
def scale_recipe_servings(
    recipe_id: str,
    payload: ServingScaleRequest,
    db: Session = Depends(get_db),
) -> ServingScaleResponse:
    """
    Calculate scaled ingredient quantities for a requested serving count without mutating
    the underlying recipe record. Qualitative quantities ('to taste') are preserved.
    """
    recipe = (
        db.query(Recipe)
        .options(joinedload(Recipe.recipe_ingredients).joinedload(RecipeIngredient.ingredient))
        .filter(Recipe.id == recipe_id)
        .first()
    )
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe '{recipe_id}' not found.",
        )

    sorted_ri = sorted(recipe.recipe_ingredients, key=lambda item: item.id)
    scaled_items: List[ScaledIngredientOut] = []

    for ri in sorted_ri:
        adjusted_qty, display_qty = scale_single_quantity(
            original_quantity=ri.quantity,
            unit=ri.unit,
            original_servings=recipe.default_servings,
            requested_servings=payload.servings,
        )
        scaled_items.append(
            ScaledIngredientOut(
                ingredient_id=ri.ingredient_id,
                canonical_name=ri.ingredient.canonical_name if ri.ingredient else ri.ingredient_id,
                original_quantity=ri.quantity,
                adjusted_quantity=adjusted_qty,
                display_quantity=display_qty,
                unit=ri.unit,
                requirement_type=ri.requirement_type,
                preparation_note=ri.preparation_note,
            )
        )

    return ServingScaleResponse(
        recipe_id=recipe.id,
        recipe_name=recipe.name,
        original_servings=recipe.default_servings,
        requested_servings=payload.servings,
        scaling_formula="adjusted_quantity = original_quantity * requested_servings / original_servings",
        unit_conversion_note=(
            "Original units are preserved. Mass-to-volume conversions are never performed without density data; "
            "qualitative amounts ('to taste') remain unchanged."
        ),
        ingredients=scaled_items,
    )


@router.get("/ingredients", response_model=List[IngredientOut], tags=["Ingredients"])
def list_ingredients(
    q: Optional[str] = Query(default=None, max_length=100, description="Search query for ingredient name or alias"),
    category: Optional[str] = Query(default=None, max_length=64),
    db: Session = Depends(get_db),
) -> List[IngredientOut]:
    """Search the canonical ingredient catalogue."""
    ingredients = (
        db.query(Ingredient)
        .options(joinedload(Ingredient.aliases))
        .filter(Ingredient.active.is_(True))
        .order_by(Ingredient.canonical_name.asc())
        .all()
    )

    q_clean = clean_ingredient_token(q) if q else None
    results: List[IngredientOut] = []
    for ing in ingredients:
        if category and ing.category.lower() != category.strip().lower():
            continue
        alias_list = [a.alias for a in ing.aliases]
        if q_clean:
            match_name = q_clean in ing.canonical_name.lower()
            match_alias = any(q_clean in a.normalised_alias.lower() for a in ing.aliases)
            if not (match_name or match_alias):
                continue
        results.append(
            IngredientOut(
                id=ing.id,
                canonical_name=ing.canonical_name,
                category=ing.category,
                description=ing.description,
                aliases=alias_list,
            )
        )
    return results


@router.get("/ingredients/suggestions", response_model=List[IngredientOut], tags=["Ingredients"])
def get_ingredient_suggestions(
    prefix: Optional[str] = Query(default=None, max_length=64),
    limit: int = Query(default=12, ge=1, le=50),
    db: Session = Depends(get_db),
) -> List[IngredientOut]:
    """Return supported ingredient suggestions and aliases for quick-add chips and autocomplete."""
    all_matches = list_ingredients(q=prefix, category=None, db=db)
    return all_matches[:limit]


@router.get("/pantry/items", response_model=List[PantryItemOut], tags=["Pantry"])
def get_pantry_items(
    q: Optional[str] = Query(default=None, max_length=100),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> List[PantryItemOut]:
    """Retrieve the current user's pantry items."""
    ensure_user_exists(db, user_id)
    items = (
        db.query(UserPantryItem)
        .options(joinedload(UserPantryItem.ingredient))
        .filter(UserPantryItem.user_id == user_id)
        .order_by(UserPantryItem.id.asc())
        .all()
    )

    q_clean = clean_ingredient_token(q) if q else None
    out: List[PantryItemOut] = []
    for item in items:
        cname = item.ingredient.canonical_name if item.ingredient else item.ingredient_id
        cat = item.ingredient.category if item.ingredient else "other"
        if q_clean and q_clean not in cname.lower():
            continue
        out.append(
            PantryItemOut(
                id=item.id,
                ingredient_id=item.ingredient_id,
                canonical_name=cname,
                category=cat,
                quantity=item.quantity,
                unit=item.unit,
                display_quantity=format_quantity_display(item.quantity, item.unit),
                purchase_date=item.purchase_date,
                best_before_date=item.best_before_date,
                storage_note=item.storage_note,
                food_safety_reminder=(
                    "Stored dates are for inventory reference only and do not prove food safety. "
                    "Verify storage condition, smell, and appearance before cooking."
                ),
            )
        )
    return out


@router.post("/pantry/items", response_model=PantryItemOut, status_code=status.HTTP_201_CREATED, tags=["Pantry"])
def add_pantry_item(
    payload: PantryItemCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> PantryItemOut:
    """Add or update an ingredient in the current user's personal pantry."""
    ensure_user_exists(db, user_id)
    norm_results = normalise_ingredients(db, [payload.ingredient_name])
    if not norm_results or not norm_results[0].is_recognised or not norm_results[0].ingredient_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Ingredient '{payload.ingredient_name}' is not in the canonical catalogue. Choose a supported ingredient.",
        )

    resolved = norm_results[0]
    existing = (
        db.query(UserPantryItem)
        .filter(
            UserPantryItem.user_id == user_id,
            UserPantryItem.ingredient_id == resolved.ingredient_id,
        )
        .first()
    )

    if existing:
        if can_combine_units(existing.unit, payload.unit):
            new_qty, new_unit = combine_compatible_quantities(
                existing.quantity, existing.unit, payload.quantity, payload.unit
            )
            existing.quantity = new_qty or payload.quantity
            existing.unit = new_unit
        else:
            existing.quantity = payload.quantity
            existing.unit = payload.unit
        if payload.purchase_date is not None:
            existing.purchase_date = payload.purchase_date
        if payload.best_before_date is not None:
            existing.best_before_date = payload.best_before_date
        if payload.storage_note is not None:
            existing.storage_note = payload.storage_note
        db.commit()
        db.refresh(existing)
        target = existing
    else:
        target = UserPantryItem(
            user_id=user_id,
            ingredient_id=resolved.ingredient_id,
            quantity=payload.quantity,
            unit=payload.unit,
            purchase_date=payload.purchase_date,
            best_before_date=payload.best_before_date,
            storage_note=payload.storage_note,
        )
        db.add(target)
        db.commit()
        db.refresh(target)

    ing = db.query(Ingredient).filter(Ingredient.id == target.ingredient_id).first()
    return PantryItemOut(
        id=target.id,
        ingredient_id=target.ingredient_id,
        canonical_name=ing.canonical_name if ing else resolved.canonical_name,
        category=ing.category if ing else (resolved.category or "other"),
        quantity=target.quantity,
        unit=target.unit,
        display_quantity=format_quantity_display(target.quantity, target.unit),
        purchase_date=target.purchase_date,
        best_before_date=target.best_before_date,
        storage_note=target.storage_note,
        food_safety_reminder=(
            "Stored dates are for inventory reference only and do not prove food safety. "
            "Verify storage condition, smell, and appearance before cooking."
        ),
    )


@router.patch("/pantry/items/{item_id}", response_model=PantryItemOut, tags=["Pantry"])
def update_pantry_item(
    item_id: int,
    payload: PantryItemUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> PantryItemOut:
    """Update a pantry item belonging to the current user."""
    item = (
        db.query(UserPantryItem)
        .options(joinedload(UserPantryItem.ingredient))
        .filter(UserPantryItem.id == item_id, UserPantryItem.user_id == user_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pantry item not found.")

    if payload.quantity is not None:
        item.quantity = payload.quantity
    if payload.unit is not None:
        item.unit = payload.unit
    if payload.purchase_date is not None:
        item.purchase_date = payload.purchase_date
    if payload.best_before_date is not None:
        item.best_before_date = payload.best_before_date
    if payload.storage_note is not None:
        item.storage_note = payload.storage_note

    db.commit()
    db.refresh(item)

    return PantryItemOut(
        id=item.id,
        ingredient_id=item.ingredient_id,
        canonical_name=item.ingredient.canonical_name if item.ingredient else item.ingredient_id,
        category=item.ingredient.category if item.ingredient else "other",
        quantity=item.quantity,
        unit=item.unit,
        display_quantity=format_quantity_display(item.quantity, item.unit),
        purchase_date=item.purchase_date,
        best_before_date=item.best_before_date,
        storage_note=item.storage_note,
        food_safety_reminder=(
            "Stored dates are for inventory reference only and do not prove food safety. "
            "Verify storage condition, smell, and appearance before cooking."
        ),
    )


@router.delete("/pantry/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Pantry"])
def delete_pantry_item(
    item_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> None:
    """Remove a pantry item belonging to the current user."""
    item = (
        db.query(UserPantryItem)
        .filter(UserPantryItem.id == item_id, UserPantryItem.user_id == user_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pantry item not found.")
    db.delete(item)
    db.commit()


@router.get("/favourites", response_model=List[FavouriteOut], tags=["Favourites"])
def get_favourites(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> List[FavouriteOut]:
    """Retrieve the current user's saved favourite recipes."""
    ensure_user_exists(db, user_id)
    favs = (
        db.query(UserFavourite)
        .options(joinedload(UserFavourite.recipe))
        .filter(UserFavourite.user_id == user_id)
        .order_by(UserFavourite.id.desc())
        .all()
    )
    out: List[FavouriteOut] = []
    for f in favs:
        if not f.recipe:
            continue
        out.append(
            FavouriteOut(
                id=f.id,
                recipe_id=f.recipe_id,
                recipe_name=f.recipe.name,
                image_reference=f.recipe.image_reference,
                total_minutes=f.recipe.preparation_minutes + f.recipe.cooking_minutes,
                difficulty=f.recipe.difficulty,
                cuisine=f.recipe.cuisine,
                created_at=f.created_at.isoformat(),
            )
        )
    return out


@router.post("/favourites/{recipe_id}", response_model=FavouriteOut, status_code=status.HTTP_201_CREATED, tags=["Favourites"])
def add_favourite(
    recipe_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> FavouriteOut:
    """Save a recipe to the current user's favourites."""
    ensure_user_exists(db, user_id)
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Recipe '{recipe_id}' not found.")

    existing = (
        db.query(UserFavourite)
        .filter(UserFavourite.user_id == user_id, UserFavourite.recipe_id == recipe_id)
        .first()
    )
    if not existing:
        existing = UserFavourite(user_id=user_id, recipe_id=recipe_id)
        db.add(existing)
        db.commit()
        db.refresh(existing)

    return FavouriteOut(
        id=existing.id,
        recipe_id=recipe.id,
        recipe_name=recipe.name,
        image_reference=recipe.image_reference,
        total_minutes=recipe.preparation_minutes + recipe.cooking_minutes,
        difficulty=recipe.difficulty,
        cuisine=recipe.cuisine,
        created_at=existing.created_at.isoformat(),
    )


@router.delete("/favourites/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Favourites"])
def remove_favourite(
    recipe_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> None:
    """Remove a recipe from the current user's favourites."""
    fav = (
        db.query(UserFavourite)
        .filter(UserFavourite.user_id == user_id, UserFavourite.recipe_id == recipe_id)
        .first()
    )
    if not fav:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Favourite entry not found.")
    db.delete(fav)
    db.commit()


def _serialize_shopping_list(shopping_list: ShoppingList, db: Session) -> ShoppingListOut:
    items_out: List[ShoppingListItemOut] = []
    for item in sorted(shopping_list.items, key=lambda x: (x.completed, x.id)):
        rec_name = item.related_recipe.name if item.related_recipe else None
        items_out.append(
            ShoppingListItemOut(
                id=item.id,
                ingredient_id=item.ingredient_id,
                ingredient_name=item.ingredient_name,
                quantity=item.quantity,
                unit=item.unit,
                display_quantity=format_quantity_display(item.quantity, item.unit),
                completed=item.completed,
                related_recipe_id=item.related_recipe_id,
                related_recipe_name=rec_name,
            )
        )
    return ShoppingListOut(
        id=shopping_list.id,
        user_id=shopping_list.user_id,
        name=shopping_list.name,
        items=items_out,
        unit_handling_note=(
            "Duplicate items with identical or compatible metric units (g/kg, ml/litre) are combined automatically. "
            "Items with incompatible units (e.g., g vs cup or piece) are kept as separate lines to prevent inaccurate conversions."
        ),
    )


@router.get("/shopping-list", response_model=ShoppingListOut, tags=["Shopping List"])
def get_shopping_list(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> ShoppingListOut:
    """Retrieve the current user's shopping list."""
    ensure_user_exists(db, user_id)
    shopping_list = (
        db.query(ShoppingList)
        .options(joinedload(ShoppingList.items).joinedload(ShoppingListItem.related_recipe))
        .filter(ShoppingList.user_id == user_id)
        .first()
    )
    return _serialize_shopping_list(shopping_list, db)


@router.post(
    "/shopping-list/items",
    response_model=ShoppingListItemOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Shopping List"],
)
def add_shopping_list_item(
    payload: ShoppingListItemCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> ShoppingListItemOut:
    """
    Add an item to the user's shopping list.
    Merges quantities if an unchecked entry for the same ingredient already exists with a compatible unit;
    creates a separate entry if units are incompatible.
    """
    ensure_user_exists(db, user_id)
    shopping_list = db.query(ShoppingList).filter(ShoppingList.user_id == user_id).first()

    norm_list = normalise_ingredients(db, [payload.ingredient_name])
    resolved_id: Optional[str] = None
    canonical_display = payload.ingredient_name.strip().lower()
    if norm_list:
        resolved_id = norm_list[0].ingredient_id
        canonical_display = norm_list[0].canonical_name

    if payload.related_recipe_id:
        rec_exists = db.query(Recipe).filter(Recipe.id == payload.related_recipe_id).first()
        if not rec_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Related recipe '{payload.related_recipe_id}' not found.",
            )

    # Check if an unchecked item for the same ingredient with a compatible unit exists
    existing_candidates = (
        db.query(ShoppingListItem)
        .filter(
            ShoppingListItem.shopping_list_id == shopping_list.id,
            ShoppingListItem.completed.is_(False),
            ShoppingListItem.ingredient_name == canonical_display,
        )
        .all()
    )

    target_item: Optional[ShoppingListItem] = None
    for cand in existing_candidates:
        if can_combine_units(cand.unit, payload.unit):
            combined_qty, combined_unit = combine_compatible_quantities(
                cand.quantity, cand.unit, payload.quantity, payload.unit
            )
            cand.quantity = combined_qty
            cand.unit = combined_unit
            if payload.related_recipe_id and not cand.related_recipe_id:
                cand.related_recipe_id = payload.related_recipe_id
            db.commit()
            db.refresh(cand)
            target_item = cand
            break

    if not target_item:
        target_item = ShoppingListItem(
            shopping_list_id=shopping_list.id,
            ingredient_id=resolved_id,
            ingredient_name=canonical_display,
            quantity=payload.quantity if payload.unit.strip().lower() != "to taste" else None,
            unit=payload.unit,
            completed=False,
            related_recipe_id=payload.related_recipe_id,
        )
        db.add(target_item)
        db.commit()
        db.refresh(target_item)

    rec_name = target_item.related_recipe.name if target_item.related_recipe else None
    return ShoppingListItemOut(
        id=target_item.id,
        ingredient_id=target_item.ingredient_id,
        ingredient_name=target_item.ingredient_name,
        quantity=target_item.quantity,
        unit=target_item.unit,
        display_quantity=format_quantity_display(target_item.quantity, target_item.unit),
        completed=target_item.completed,
        related_recipe_id=target_item.related_recipe_id,
        related_recipe_name=rec_name,
    )


@router.patch("/shopping-list/items/{item_id}", response_model=ShoppingListItemOut, tags=["Shopping List"])
def update_shopping_list_item(
    item_id: int,
    payload: ShoppingListItemUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> ShoppingListItemOut:
    """Update quantity, unit, or completion status of a shopping list item."""
    ensure_user_exists(db, user_id)
    shopping_list = db.query(ShoppingList).filter(ShoppingList.user_id == user_id).first()
    item = (
        db.query(ShoppingListItem)
        .filter(
            ShoppingListItem.id == item_id,
            ShoppingListItem.shopping_list_id == shopping_list.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shopping list item not found.")

    if payload.quantity is not None:
        item.quantity = payload.quantity
    if payload.unit is not None:
        item.unit = payload.unit
    if payload.completed is not None:
        item.completed = payload.completed

    db.commit()
    db.refresh(item)
    rec_name = item.related_recipe.name if item.related_recipe else None
    return ShoppingListItemOut(
        id=item.id,
        ingredient_id=item.ingredient_id,
        ingredient_name=item.ingredient_name,
        quantity=item.quantity,
        unit=item.unit,
        display_quantity=format_quantity_display(item.quantity, item.unit),
        completed=item.completed,
        related_recipe_id=item.related_recipe_id,
        related_recipe_name=rec_name,
    )


@router.delete("/shopping-list/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Shopping List"])
def delete_shopping_list_item(
    item_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> None:
    """Remove an item from the current user's shopping list."""
    ensure_user_exists(db, user_id)
    shopping_list = db.query(ShoppingList).filter(ShoppingList.user_id == user_id).first()
    item = (
        db.query(ShoppingListItem)
        .filter(
            ShoppingListItem.id == item_id,
            ShoppingListItem.shopping_list_id == shopping_list.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shopping list item not found.")
    db.delete(item)
    db.commit()


@router.delete("/shopping-list/completed", response_model=ShoppingListOut, tags=["Shopping List"])
def clear_completed_shopping_items(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> ShoppingListOut:
    """Clear all completed/purchased items from the current user's shopping list."""
    ensure_user_exists(db, user_id)
    shopping_list = db.query(ShoppingList).filter(ShoppingList.user_id == user_id).first()
    (
        db.query(ShoppingListItem)
        .filter(
            ShoppingListItem.shopping_list_id == shopping_list.id,
            ShoppingListItem.completed.is_(True),
        )
        .delete()
    )
    db.commit()
    db.refresh(shopping_list)
    return _serialize_shopping_list(shopping_list, db)


@router.get("/profile", response_model=UserProfileOut, tags=["Profile"])
def get_user_profile(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> UserProfileOut:
    """Retrieve the current user's preferences and profile."""
    user = ensure_user_exists(db, user_id)
    db.commit()
    return UserProfileOut(
        user_id=user.id,
        display_name=user.display_name,
        dietary_preferences=json.loads(user.dietary_preferences_json),
        disliked_ingredients=json.loads(user.disliked_ingredients_json),
        preferred_cuisine=user.preferred_cuisine,
        typical_serving_size=user.typical_serving_size,
        max_cooking_minutes=user.max_cooking_minutes,
        medical_disclaimer=(
            "Dietary preferences and excluded ingredients are culinary filters only and must not be treated "
            "as medical advice or a guarantee of allergen safety."
        ),
    )


@router.put("/profile", response_model=UserProfileOut, tags=["Profile"])
def update_user_profile(
    payload: UserProfileUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> UserProfileOut:
    """Update the current user's culinary preferences."""
    user = ensure_user_exists(db, user_id)
    if payload.display_name is not None:
        user.display_name = payload.display_name
    if payload.dietary_preferences is not None:
        cleaned_diets = [sanitize_text(d, 64).lower() for d in payload.dietary_preferences if d and d.strip()]
        user.dietary_preferences_json = json.dumps(cleaned_diets)
    if payload.disliked_ingredients is not None:
        cleaned_disliked = [sanitize_text(i, 64).lower() for i in payload.disliked_ingredients if i and i.strip()]
        user.disliked_ingredients_json = json.dumps(cleaned_disliked)
    if payload.preferred_cuisine is not None:
        user.preferred_cuisine = payload.preferred_cuisine or None
    if payload.typical_serving_size is not None:
        user.typical_serving_size = payload.typical_serving_size
    if payload.max_cooking_minutes is not None:
        user.max_cooking_minutes = payload.max_cooking_minutes

    db.commit()
    db.refresh(user)
    return UserProfileOut(
        user_id=user.id,
        display_name=user.display_name,
        dietary_preferences=json.loads(user.dietary_preferences_json),
        disliked_ingredients=json.loads(user.disliked_ingredients_json),
        preferred_cuisine=user.preferred_cuisine,
        typical_serving_size=user.typical_serving_size,
        max_cooking_minutes=user.max_cooking_minutes,
        medical_disclaimer=(
            "Dietary preferences and excluded ingredients are culinary filters only and must not be treated "
            "as medical advice or a guarantee of allergen safety."
        ),
    )
