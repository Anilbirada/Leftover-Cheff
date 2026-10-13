"""Pydantic v2 request and response schemas for Leftover Chef REST API."""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from app.core.security import sanitize_text


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    environment: str
    catalogue_recipes_count: int
    catalogue_ingredients_count: int
    developer_credit: str


class IngredientAliasOut(BaseModel):
    alias: str
    normalised_alias: str


class IngredientOut(BaseModel):
    id: str
    canonical_name: str
    category: str
    description: Optional[str] = None
    aliases: List[str] = []


class NormalisedIngredientOut(BaseModel):
    raw_input: str
    normalised_input: str
    ingredient_id: Optional[str] = None
    canonical_name: str
    category: Optional[str] = None
    is_recognised: bool
    resolution_method: str


class RecipeIngredientOut(BaseModel):
    ingredient_id: str
    canonical_name: str
    quantity: Optional[float] = None
    unit: str
    display_quantity: str
    requirement_type: str
    preparation_note: Optional[str] = None
    is_available: Optional[bool] = None


class AllergenInfoOut(BaseModel):
    allergen: str
    verification_status: str
    source_reference: Optional[str] = None


class AISuggestionOut(BaseModel):
    label: str
    explanation: str
    cooking_tip: str
    is_ai_generated: bool
    verification_status: str
    safety_disclaimer: str
    provider_status: str


class RecipeSummaryOut(BaseModel):
    id: str
    name: str
    description: str
    preparation_minutes: int
    cooking_minutes: int
    total_minutes: int
    default_servings: int
    difficulty: str
    cuisine: Optional[str] = None
    image_reference: Optional[str] = None
    dietary_attributes: List[str] = []
    allergen_summary_notice: str
    required_ingredient_count: int
    optional_ingredient_count: int


class RecipeDetailOut(BaseModel):
    id: str
    name: str
    description: str
    preparation_minutes: int
    cooking_minutes: int
    total_minutes: int
    default_servings: int
    difficulty: str
    cuisine: Optional[str] = None
    image_reference: Optional[str] = None
    source_reference: str
    licence_reference: str
    dietary_attributes: List[str] = []
    allergens: List[AllergenInfoOut] = []
    allergen_verification_notice: str
    food_safety_notice: str
    instructions: List[str]
    ingredients: List[RecipeIngredientOut]


class MatchedRecipeOut(BaseModel):
    recipe: RecipeDetailOut
    core_coverage_score: float
    score_explanation: str
    total_required_count: int
    matched_required_count: int
    missing_required_count: int
    matched_optional_count: int
    missing_optional_count: int
    matched_required_ingredients: List[RecipeIngredientOut]
    missing_required_ingredients: List[RecipeIngredientOut]
    matched_optional_ingredients: List[RecipeIngredientOut]
    missing_optional_ingredients: List[RecipeIngredientOut]
    ai_suggestion: Optional[AISuggestionOut] = None


class SearchByIngredientsRequest(BaseModel):
    ingredients: List[str] = Field(..., description="List of raw or comma-separated ingredient strings.")
    dietary_filters: Optional[List[str]] = Field(default=None)
    excluded_ingredients: Optional[List[str]] = Field(default=None)
    max_total_minutes: Optional[int] = Field(default=None, ge=1, le=600)
    difficulty: Optional[str] = Field(default=None)
    cuisine: Optional[str] = Field(default=None)
    sort_by: str = Field(default="best_match")
    include_ai_explanation: bool = Field(default=False)

    @field_validator("ingredients")
    @classmethod
    def validate_ingredients_not_oversized(cls, v: List[str]) -> List[str]:
        if len(v) > 60:
            raise ValueError("Cannot submit more than 60 ingredient entries in a single request.")
        total_len = sum(len(str(item)) for item in v if item is not None)
        if total_len > 1000:
            raise ValueError("Total ingredient text exceeds maximum length of 1000 characters.")
        return v


class SearchByIngredientsResponse(BaseModel):
    normalised_user_ingredients: List[NormalisedIngredientOut]
    recognised_ingredient_ids: List[str]
    unrecognised_inputs: List[str]
    matched_recipes: List[MatchedRecipeOut]
    no_match_guidance: Optional[str] = None
    ranking_rule_summary: str
    score_formula_description: str
    food_safety_notice: str


class ServingScaleRequest(BaseModel):
    servings: int = Field(..., ge=1, le=50, description="Requested number of servings (1 to 50).")


class ScaledIngredientOut(BaseModel):
    ingredient_id: str
    canonical_name: str
    original_quantity: Optional[float] = None
    adjusted_quantity: Optional[float] = None
    display_quantity: str
    unit: str
    requirement_type: str
    preparation_note: Optional[str] = None


class ServingScaleResponse(BaseModel):
    recipe_id: str
    recipe_name: str
    original_servings: int
    requested_servings: int
    scaling_formula: str
    unit_conversion_note: str
    ingredients: List[ScaledIngredientOut]


class PantryItemCreate(BaseModel):
    ingredient_name: str = Field(..., min_length=1, max_length=120)
    quantity: float = Field(default=1.0, gt=0, le=100000)
    unit: str = Field(default="piece", min_length=1, max_length=32)
    purchase_date: Optional[str] = Field(default=None, max_length=32)
    best_before_date: Optional[str] = Field(default=None, max_length=32)
    storage_note: Optional[str] = Field(default=None, max_length=200)

    @field_validator("ingredient_name", "unit", "storage_note")
    @classmethod
    def sanitize_fields(cls, v: Optional[str]) -> Optional[str]:
        return sanitize_text(v, max_length=200)


class PantryItemUpdate(BaseModel):
    quantity: Optional[float] = Field(default=None, gt=0, le=100000)
    unit: Optional[str] = Field(default=None, min_length=1, max_length=32)
    purchase_date: Optional[str] = Field(default=None, max_length=32)
    best_before_date: Optional[str] = Field(default=None, max_length=32)
    storage_note: Optional[str] = Field(default=None, max_length=200)

    @field_validator("unit", "storage_note")
    @classmethod
    def sanitize_fields(cls, v: Optional[str]) -> Optional[str]:
        return sanitize_text(v, max_length=200)


class PantryItemOut(BaseModel):
    id: int
    ingredient_id: str
    canonical_name: str
    category: str
    quantity: float
    unit: str
    display_quantity: str
    purchase_date: Optional[str] = None
    best_before_date: Optional[str] = None
    storage_note: Optional[str] = None
    food_safety_reminder: str


class ShoppingListItemCreate(BaseModel):
    ingredient_name: str = Field(..., min_length=1, max_length=120)
    quantity: Optional[float] = Field(default=1.0, gt=0, le=100000)
    unit: str = Field(default="piece", min_length=1, max_length=32)
    related_recipe_id: Optional[str] = Field(default=None, max_length=64)

    @field_validator("ingredient_name", "unit")
    @classmethod
    def sanitize_fields(cls, v: Optional[str]) -> Optional[str]:
        return sanitize_text(v, max_length=120)


class ShoppingListItemUpdate(BaseModel):
    quantity: Optional[float] = Field(default=None, gt=0, le=100000)
    unit: Optional[str] = Field(default=None, min_length=1, max_length=32)
    completed: Optional[bool] = Field(default=None)

    @field_validator("unit")
    @classmethod
    def sanitize_fields(cls, v: Optional[str]) -> Optional[str]:
        return sanitize_text(v, max_length=64)


class ShoppingListItemOut(BaseModel):
    id: int
    ingredient_id: Optional[str] = None
    ingredient_name: str
    quantity: Optional[float] = None
    unit: str
    display_quantity: str
    completed: bool
    related_recipe_id: Optional[str] = None
    related_recipe_name: Optional[str] = None


class ShoppingListOut(BaseModel):
    id: int
    user_id: str
    name: str
    items: List[ShoppingListItemOut]
    unit_handling_note: str


class FavouriteOut(BaseModel):
    id: int
    recipe_id: str
    recipe_name: str
    image_reference: Optional[str] = None
    total_minutes: int
    difficulty: str
    cuisine: Optional[str] = None
    created_at: str


class UserProfileOut(BaseModel):
    user_id: str
    display_name: str
    dietary_preferences: List[str]
    disliked_ingredients: List[str]
    preferred_cuisine: Optional[str] = None
    typical_serving_size: int
    max_cooking_minutes: Optional[int] = None
    medical_disclaimer: str


class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    dietary_preferences: Optional[List[str]] = None
    disliked_ingredients: Optional[List[str]] = None
    preferred_cuisine: Optional[str] = Field(default=None, max_length=64)
    typical_serving_size: Optional[int] = Field(default=None, ge=1, le=50)
    max_cooking_minutes: Optional[int] = Field(default=None, ge=5, le=600)

    @field_validator("display_name", "preferred_cuisine")
    @classmethod
    def sanitize_fields(cls, v: Optional[str]) -> Optional[str]:
        return sanitize_text(v, max_length=100)
