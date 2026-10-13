"""
Recipe Catalogue Validation and Database Seeding Service.

Responsibilities:
- Validate raw JSON catalogue structure before inserting into the database.
- Reject missing names, malformed ingredients, missing instructions, negative times, or invalid references.
- Populate canonical ingredients, approved aliases, recipes, dietary tags, allergens, and default user profile.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Set
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_auth_secret
from app.models.entities import (
    Ingredient,
    IngredientAlias,
    Recipe,
    RecipeAllergen,
    RecipeDietaryAttribute,
    RecipeIngredient,
    ShoppingList,
    User,
)
from app.services.normalizer import clean_ingredient_token


def validate_catalogue_payload(payload: Dict[str, Any]) -> None:
    """Validate catalogue structure and raise ValueError on any data integrity violation."""
    if not isinstance(payload, dict):
        raise ValueError("Catalogue payload must be a JSON object.")

    ingredients = payload.get("ingredients")
    recipes = payload.get("recipes")

    if not isinstance(ingredients, list) or not ingredients:
        raise ValueError("Catalogue must contain a non-empty 'ingredients' list.")
    if not isinstance(recipes, list) or not recipes:
        raise ValueError("Catalogue must contain a non-empty 'recipes' list.")

    seen_ing_ids: Set[str] = set()
    seen_canonical_names: Set[str] = set()
    seen_aliases: Set[str] = set()

    for idx, ing in enumerate(ingredients):
        ing_id = (ing.get("id") or "").strip()
        cname = clean_ingredient_token(ing.get("canonical_name") or "")
        category = (ing.get("category") or "").strip()
        if not ing_id or not cname or not category:
            raise ValueError(f"Ingredient at index {idx} is missing id, canonical_name, or category.")
        if ing_id in seen_ing_ids:
            raise ValueError(f"Duplicate ingredient id: '{ing_id}'.")
        if cname in seen_canonical_names:
            raise ValueError(f"Duplicate canonical ingredient name: '{cname}'.")
        seen_ing_ids.add(ing_id)
        seen_canonical_names.add(cname)

        for raw_alias in ing.get("aliases", []):
            norm_alias = clean_ingredient_token(raw_alias)
            if not norm_alias:
                continue
            if norm_alias in seen_aliases or (norm_alias in seen_canonical_names and norm_alias != cname):
                raise ValueError(f"Conflicting alias '{raw_alias}' on ingredient '{ing_id}'.")
            seen_aliases.add(norm_alias)

    seen_recipe_ids: Set[str] = set()
    for r_idx, rec in enumerate(recipes):
        rec_id = (rec.get("id") or "").strip()
        name = (rec.get("name") or "").strip()
        desc = (rec.get("description") or "").strip()
        prep_min = rec.get("preparation_minutes")
        cook_min = rec.get("cooking_minutes")
        servings = rec.get("default_servings")
        instructions = rec.get("instructions")
        rec_ings = rec.get("ingredients")

        if not rec_id or not name or not desc:
            raise ValueError(f"Recipe at index {r_idx} is missing id, name, or description.")
        if rec_id in seen_recipe_ids:
            raise ValueError(f"Duplicate recipe id: '{rec_id}'.")
        seen_recipe_ids.add(rec_id)

        if not isinstance(prep_min, int) or prep_min < 0:
            raise ValueError(f"Recipe '{rec_id}' has invalid preparation_minutes.")
        if not isinstance(cook_min, int) or cook_min < 0 or (prep_min + cook_min) <= 0:
            raise ValueError(f"Recipe '{rec_id}' has invalid cooking_minutes.")
        if not isinstance(servings, int) or servings < 1:
            raise ValueError(f"Recipe '{rec_id}' must have default_servings >= 1.")

        if not isinstance(instructions, list) or not instructions or not all(
            isinstance(step, str) and step.strip() for step in instructions
        ):
            raise ValueError(f"Recipe '{rec_id}' must have a non-empty list of cooking instruction strings.")

        if not isinstance(rec_ings, list) or not rec_ings:
            raise ValueError(f"Recipe '{rec_id}' must have at least one ingredient.")

        has_required = False
        seen_rec_ing: Set[str] = set()
        for ri in rec_ings:
            ref_id = (ri.get("ingredient_id") or "").strip()
            req_type = (ri.get("requirement_type") or "").strip()
            unit = (ri.get("unit") or "").strip()
            qty = ri.get("quantity")

            if ref_id not in seen_ing_ids:
                raise ValueError(f"Recipe '{rec_id}' references unknown ingredient_id '{ref_id}'.")
            if ref_id in seen_rec_ing:
                raise ValueError(f"Recipe '{rec_id}' contains duplicate ingredient_id '{ref_id}'.")
            seen_rec_ing.add(ref_id)

            if req_type not in ("required", "optional"):
                raise ValueError(f"Recipe '{rec_id}' ingredient '{ref_id}' has invalid requirement_type '{req_type}'.")
            if req_type == "required":
                has_required = True
            if not unit:
                raise ValueError(f"Recipe '{rec_id}' ingredient '{ref_id}' is missing unit.")
            if qty is not None and (not isinstance(qty, (int, float)) or qty <= 0):
                raise ValueError(f"Recipe '{rec_id}' ingredient '{ref_id}' has invalid quantity '{qty}'.")

        if not has_required:
            raise ValueError(f"Recipe '{rec_id}' must have at least one required ingredient.")


def ensure_user_exists(db: Session, user_id: str, display_name: str = "Home Chef") -> User:
    """Ensure a User record and default ShoppingList exist for the specified user_id."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(
            id=user_id,
            display_name=display_name,
            login_identifier=f"{user_id}@leftoverchef.local",
            secure_authentication_reference=hash_auth_secret(f"auth_{user_id}"),
            dietary_preferences_json="[]",
            disliked_ingredients_json="[]",
            preferred_cuisine=None,
            typical_serving_size=2,
            max_cooking_minutes=None,
        )
        db.add(user)
        db.flush()

    shopping_list = db.query(ShoppingList).filter(ShoppingList.user_id == user_id).first()
    if not shopping_list:
        db.add(ShoppingList(user_id=user_id, name="My Shopping List"))
        db.flush()

    return user


def seed_database_from_file(db: Session, seed_path: str | Path | None = None) -> Dict[str, int]:
    """Load, validate, and idempotently seed the database from catalogue.json."""
    target_path = Path(seed_path or settings.seed_file_path)
    if not target_path.exists():
        raise FileNotFoundError(f"Seed catalogue file not found at: {target_path}")

    raw_data = json.loads(target_path.read_text(encoding="utf-8"))
    validate_catalogue_payload(raw_data)

    ing_added = 0
    rec_added = 0

    for ing_data in raw_data["ingredients"]:
        existing = db.query(Ingredient).filter(Ingredient.id == ing_data["id"]).first()
        if not existing:
            ing = Ingredient(
                id=ing_data["id"],
                canonical_name=clean_ingredient_token(ing_data["canonical_name"]),
                category=ing_data["category"].strip(),
                description=ing_data.get("description"),
                active=True,
            )
            db.add(ing)
            db.flush()
            ing_added += 1

            for raw_alias in ing_data.get("aliases", []):
                norm_alias = clean_ingredient_token(raw_alias)
                if norm_alias and norm_alias != ing.canonical_name:
                    db.add(
                        IngredientAlias(
                            ingredient_id=ing.id,
                            alias=raw_alias.strip(),
                            normalised_alias=norm_alias,
                        )
                    )

    db.flush()

    for rec_data in raw_data["recipes"]:
        existing_rec = db.query(Recipe).filter(Recipe.id == rec_data["id"]).first()
        if not existing_rec:
            recipe = Recipe(
                id=rec_data["id"],
                name=rec_data["name"].strip(),
                description=rec_data["description"].strip(),
                preparation_minutes=int(rec_data["preparation_minutes"]),
                cooking_minutes=int(rec_data["cooking_minutes"]),
                default_servings=int(rec_data["default_servings"]),
                difficulty=rec_data.get("difficulty", "Easy"),
                cuisine=rec_data.get("cuisine"),
                instructions_json=json.dumps(rec_data["instructions"], ensure_ascii=False),
                image_reference=rec_data.get("image_reference"),
                source_reference=rec_data.get("source_reference", "Leftover Chef Verified Test Kitchen Catalogue v1.0"),
                licence_reference=rec_data.get("licence_reference", "CC0-1.0"),
            )
            db.add(recipe)
            db.flush()
            rec_added += 1

            for ri in rec_data["ingredients"]:
                db.add(
                    RecipeIngredient(
                        recipe_id=recipe.id,
                        ingredient_id=ri["ingredient_id"],
                        quantity=float(ri["quantity"]) if ri.get("quantity") is not None else None,
                        unit=ri["unit"].strip(),
                        requirement_type=ri["requirement_type"].strip(),
                        preparation_note=ri.get("preparation_note"),
                    )
                )

            for attr in rec_data.get("dietary_attributes", []):
                db.add(
                    RecipeDietaryAttribute(
                        recipe_id=recipe.id,
                        attribute=attr.strip().lower(),
                    )
                )

            for alg in rec_data.get("allergens", []):
                db.add(
                    RecipeAllergen(
                        recipe_id=recipe.id,
                        allergen=alg["allergen"].strip(),
                        verification_status=alg.get("verification_status", "unverified").strip(),
                        source_reference=alg.get("source_reference"),
                    )
                )

    ensure_user_exists(db, "default_chef", "Default Home Chef")
    db.commit()

    return {
        "ingredients_seeded": ing_added,
        "recipes_seeded": rec_added,
        "total_ingredients": db.query(Ingredient).count(),
        "total_recipes": db.query(Recipe).count(),
    }
