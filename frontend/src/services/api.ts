import type {
  FavouriteOut,
  IngredientOut,
  PantryItemOut,
  RecipeDetailOut,
  RecipeSummaryOut,
  SearchByIngredientsResponse,
  ServingScaleResponse,
  ShoppingListItemOut,
  ShoppingListOut,
  UserProfileOut,
} from '../types/api';

const API_BASE = '/api/v1';

let activeUserId = 'default_chef';

export function setActiveUserId(userId: string) {
  activeUserId = userId.trim() || 'default_chef';
}

export function getActiveUserId(): string {
  return activeUserId;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-User-ID': activeUserId,
    ...(options.headers as Record<string, string> | undefined),
  };

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status}`;
    try {
      const errJson = await response.json();
      if (typeof errJson.detail === 'string') {
        errorDetail = errJson.detail;
      } else if (Array.isArray(errJson.detail)) {
        errorDetail = errJson.detail.map((e: { msg?: string }) => e.msg || JSON.stringify(e)).join('; ');
      }
    } catch {
      // Fallback to status text
    }
    throw new Error(errorDetail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const api = {
  getRecipes: (params?: {
    dietary?: string;
    cuisine?: string;
    difficulty?: string;
    max_total_minutes?: number;
    sort_by?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.dietary) query.set('dietary', params.dietary);
    if (params?.cuisine) query.set('cuisine', params.cuisine);
    if (params?.difficulty) query.set('difficulty', params.difficulty);
    if (params?.max_total_minutes) query.set('max_total_minutes', String(params.max_total_minutes));
    if (params?.sort_by) query.set('sort_by', params.sort_by);
    const qs = query.toString();
    return request<RecipeSummaryOut[]>(`/recipes${qs ? `?${qs}` : ''}`);
  },

  getRecipeById: (recipeId: string, availableIngredients?: string[]) => {
    const query = new URLSearchParams();
    if (availableIngredients && availableIngredients.length > 0) {
      query.set('available_ingredients', availableIngredients.join(','));
    }
    const qs = query.toString();
    return request<RecipeDetailOut>(`/recipes/${encodeURIComponent(recipeId)}${qs ? `?${qs}` : ''}`);
  },

  searchByIngredients: (payload: {
    ingredients: string[];
    dietary_filters?: string[];
    excluded_ingredients?: string[];
    max_total_minutes?: number | null;
    difficulty?: string | null;
    cuisine?: string | null;
    sort_by?: string;
    include_ai_explanation?: boolean;
  }) =>
    request<SearchByIngredientsResponse>('/recipes/search-by-ingredients', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  scaleRecipeServings: (recipeId: string, servings: number) =>
    request<ServingScaleResponse>(`/recipes/${encodeURIComponent(recipeId)}/servings`, {
      method: 'POST',
      body: JSON.stringify({ servings }),
    }),

  getIngredients: (q?: string) => {
    const qs = q ? `?q=${encodeURIComponent(q)}` : '';
    return request<IngredientOut[]>(`/ingredients${qs}`);
  },

  getSuggestions: (prefix?: string) => {
    const qs = prefix ? `?prefix=${encodeURIComponent(prefix)}` : '';
    return request<IngredientOut[]>(`/ingredients/suggestions${qs}`);
  },

  getPantryItems: (q?: string) => {
    const qs = q ? `?q=${encodeURIComponent(q)}` : '';
    return request<PantryItemOut[]>(`/pantry/items${qs}`);
  },

  addPantryItem: (payload: {
    ingredient_name: string;
    quantity: number;
    unit: string;
    purchase_date?: string;
    best_before_date?: string;
    storage_note?: string;
  }) =>
    request<PantryItemOut>('/pantry/items', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  updatePantryItem: (
    itemId: number,
    payload: {
      quantity?: number;
      unit?: string;
      purchase_date?: string;
      best_before_date?: string;
      storage_note?: string;
    }
  ) =>
    request<PantryItemOut>(`/pantry/items/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  deletePantryItem: (itemId: number) =>
    request<void>(`/pantry/items/${itemId}`, {
      method: 'DELETE',
    }),

  getFavourites: () => request<FavouriteOut[]>('/favourites'),

  addFavourite: (recipeId: string) =>
    request<FavouriteOut>(`/favourites/${encodeURIComponent(recipeId)}`, {
      method: 'POST',
    }),

  removeFavourite: (recipeId: string) =>
    request<void>(`/favourites/${encodeURIComponent(recipeId)}`, {
      method: 'DELETE',
    }),

  getShoppingList: () => request<ShoppingListOut>('/shopping-list'),

  addShoppingItem: (payload: {
    ingredient_name: string;
    quantity?: number | null;
    unit: string;
    related_recipe_id?: string | null;
  }) =>
    request<ShoppingListItemOut>('/shopping-list/items', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  updateShoppingItem: (
    itemId: number,
    payload: { quantity?: number; unit?: string; completed?: boolean }
  ) =>
    request<ShoppingListItemOut>(`/shopping-list/items/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  deleteShoppingItem: (itemId: number) =>
    request<void>(`/shopping-list/items/${itemId}`, {
      method: 'DELETE',
    }),

  clearCompletedShoppingItems: () =>
    request<ShoppingListOut>('/shopping-list/completed', {
      method: 'DELETE',
    }),

  getProfile: () => request<UserProfileOut>('/profile'),

  updateProfile: (payload: {
    display_name?: string;
    dietary_preferences?: string[];
    disliked_ingredients?: string[];
    preferred_cuisine?: string | null;
    typical_serving_size?: number;
    max_cooking_minutes?: number | null;
  }) =>
    request<UserProfileOut>('/profile', {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
};
