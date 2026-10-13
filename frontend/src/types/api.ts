export interface IngredientOut {
  id: string;
  canonical_name: string;
  category: string;
  description?: string | null;
  aliases: string[];
}

export interface NormalisedIngredientOut {
  raw_input: string;
  normalised_input: string;
  ingredient_id?: string | null;
  canonical_name: string;
  category?: string | null;
  is_recognised: boolean;
  resolution_method: string;
}

export interface RecipeIngredientOut {
  ingredient_id: string;
  canonical_name: string;
  quantity?: number | null;
  unit: string;
  display_quantity: string;
  requirement_type: 'required' | 'optional' | string;
  preparation_note?: string | null;
  is_available?: boolean | null;
}

export interface AllergenInfoOut {
  allergen: string;
  verification_status: string;
  source_reference?: string | null;
}

export interface AISuggestionOut {
  label: string;
  explanation: string;
  cooking_tip: string;
  is_ai_generated: boolean;
  verification_status: string;
  safety_disclaimer: string;
  provider_status: string;
}

export interface RecipeSummaryOut {
  id: string;
  name: string;
  description: string;
  preparation_minutes: number;
  cooking_minutes: number;
  total_minutes: number;
  default_servings: number;
  difficulty: string;
  cuisine?: string | null;
  image_reference?: string | null;
  dietary_attributes: string[];
  allergen_summary_notice: string;
  required_ingredient_count: number;
  optional_ingredient_count: number;
}

export interface RecipeDetailOut {
  id: string;
  name: string;
  description: string;
  preparation_minutes: number;
  cooking_minutes: number;
  total_minutes: number;
  default_servings: number;
  difficulty: string;
  cuisine?: string | null;
  image_reference?: string | null;
  source_reference: string;
  licence_reference: string;
  dietary_attributes: string[];
  allergens: AllergenInfoOut[];
  allergen_verification_notice: string;
  food_safety_notice: string;
  instructions: string[];
  ingredients: RecipeIngredientOut[];
}

export interface MatchedRecipeOut {
  recipe: RecipeDetailOut;
  core_coverage_score: number;
  score_explanation: string;
  total_required_count: number;
  matched_required_count: number;
  missing_required_count: number;
  matched_optional_count: number;
  missing_optional_count: number;
  matched_required_ingredients: RecipeIngredientOut[];
  missing_required_ingredients: RecipeIngredientOut[];
  matched_optional_ingredients: RecipeIngredientOut[];
  missing_optional_ingredients: RecipeIngredientOut[];
  ai_suggestion?: AISuggestionOut | null;
}

export interface SearchByIngredientsResponse {
  normalised_user_ingredients: NormalisedIngredientOut[];
  recognised_ingredient_ids: string[];
  unrecognised_inputs: string[];
  matched_recipes: MatchedRecipeOut[];
  no_match_guidance?: string | null;
  ranking_rule_summary: string;
  score_formula_description: string;
  food_safety_notice: string;
}

export interface ScaledIngredientOut {
  ingredient_id: string;
  canonical_name: string;
  original_quantity?: number | null;
  adjusted_quantity?: number | null;
  display_quantity: string;
  unit: string;
  requirement_type: string;
  preparation_note?: string | null;
}

export interface ServingScaleResponse {
  recipe_id: string;
  recipe_name: string;
  original_servings: number;
  requested_servings: number;
  scaling_formula: string;
  unit_conversion_note: string;
  ingredients: ScaledIngredientOut[];
}

export interface PantryItemOut {
  id: number;
  ingredient_id: string;
  canonical_name: string;
  category: string;
  quantity: number;
  unit: string;
  display_quantity: string;
  purchase_date?: string | null;
  best_before_date?: string | null;
  storage_note?: string | null;
  food_safety_reminder: string;
}

export interface ShoppingListItemOut {
  id: number;
  ingredient_id?: string | null;
  ingredient_name: string;
  quantity?: number | null;
  unit: string;
  display_quantity: string;
  completed: boolean;
  related_recipe_id?: string | null;
  related_recipe_name?: string | null;
}

export interface ShoppingListOut {
  id: number;
  user_id: string;
  name: string;
  items: ShoppingListItemOut[];
  unit_handling_note: string;
}

export interface FavouriteOut {
  id: number;
  recipe_id: string;
  recipe_name: string;
  image_reference?: string | null;
  total_minutes: number;
  difficulty: string;
  cuisine?: string | null;
  created_at: string;
}

export interface UserProfileOut {
  user_id: string;
  display_name: string;
  dietary_preferences: string[];
  disliked_ingredients: string[];
  preferred_cuisine?: string | null;
  typical_serving_size: number;
  max_cooking_minutes?: number | null;
  medical_disclaimer: string;
}
