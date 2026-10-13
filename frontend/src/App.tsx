import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  BookOpen,
  Check,
  ChefHat,
  Clock,
  Heart,
  Info,
  Package,
  Plus,
  Search,
  ShieldCheck,
  ShoppingCart,
  Sparkles,
  Trash2,
  User,
  Utensils,
  X,
} from 'lucide-react';
import type {
  FavouriteOut,
  IngredientOut,
  MatchedRecipeOut,
  PantryItemOut,
  RecipeDetailOut,
  RecipeIngredientOut,
  RecipeSummaryOut,
  SearchByIngredientsResponse,
  ShoppingListOut,
  UserProfileOut,
} from './types/api';
import { api, getActiveUserId, setActiveUserId } from './services/api';
import { RecipeIllustration } from './components/RecipeIllustration';
import { RecipeDetailModal } from './components/RecipeDetailModal';

type ActiveTab = 'discover' | 'catalogue' | 'pantry' | 'shopping' | 'favourites' | 'profile' | 'about';

const QUICK_SUGGESTIONS = [
  'potato',
  'onion',
  'tomato',
  'rice',
  'cheese',
  'cooking oil',
  'salt',
  'turmeric powder',
  'egg',
  'garlic',
  'pasta',
  'butter',
  'coconut milk',
  'chickpeas',
  'spinach',
];

export function parseIngredientInputTokens(rawText: string): string[] {
  return rawText
    .split(/[,;\n]+/)
    .map((part) => part.trim().toLowerCase().replace(/\s+/g, ' '))
    .filter((part) => part.length > 0);
}

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('discover');
  const [currentUserId, setCurrentUserId] = useState<string>(getActiveUserId());

  // Ingredient Search State
  const [inputValue, setInputValue] = useState<string>('');
  const [selectedIngredients, setSelectedIngredients] = useState<string[]>([
    'potato',
    'onion',
    'tomato',
    'rice',
  ]);
  const [recentIngredients, setRecentIngredients] = useState<string[]>([
    'cheese',
    'cooking oil',
    'salt',
  ]);
  const [dietaryFilter, setDietaryFilter] = useState<string>('');
  const [excludedInput, setExcludedInput] = useState<string>('');
  const [maxMinutes, setMaxMinutes] = useState<string>('');
  const [difficultyFilter, setDifficultyFilter] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('best_match');
  const [includeAiExplanation, setIncludeAiExplanation] = useState<boolean>(false);

  const [searchResult, setSearchResult] = useState<SearchByIngredientsResponse | null>(null);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Full Catalogue State
  const [catalogueRecipes, setCatalogueRecipes] = useState<RecipeSummaryOut[]>([]);
  const [catalogueIngredients, setCatalogueIngredients] = useState<IngredientOut[]>([]);

  // Modal State
  const [selectedRecipeDetail, setSelectedRecipeDetail] = useState<RecipeDetailOut | null>(null);

  // Pantry State
  const [pantryItems, setPantryItems] = useState<PantryItemOut[]>([]);
  const [pantrySearch, setPantrySearch] = useState<string>('');
  const [newPantryName, setNewPantryName] = useState<string>('');
  const [newPantryQty, setNewPantryQty] = useState<string>('2');
  const [newPantryUnit, setNewPantryUnit] = useState<string>('piece');
  const [newPantryBestBefore, setNewPantryBestBefore] = useState<string>('');
  const [newPantryNote, setNewPantryNote] = useState<string>('');
  const [pantryError, setPantryError] = useState<string | null>(null);

  // Shopping List State
  const [shoppingList, setShoppingList] = useState<ShoppingListOut | null>(null);
  const [newShopName, setNewShopName] = useState<string>('');
  const [newShopQty, setNewShopQty] = useState<string>('1');
  const [newShopUnit, setNewShopUnit] = useState<string>('piece');
  const [shoppingError, setShoppingError] = useState<string | null>(null);

  // Favourites & Profile State
  const [favourites, setFavourites] = useState<FavouriteOut[]>([]);
  const [profile, setProfile] = useState<UserProfileOut | null>(null);
  const [profileSavedMsg, setProfileSavedMsg] = useState<string | null>(null);

  const loadUserWorkspaceData = async () => {
    try {
      const [pantryRes, shopRes, favRes, profRes] = await Promise.all([
        api.getPantryItems(),
        api.getShoppingList(),
        api.getFavourites(),
        api.getProfile(),
      ]);
      setPantryItems(pantryRes);
      setShoppingList(shopRes);
      setFavourites(favRes);
      setProfile(profRes);
    } catch {
      // Non-blocking during initial mount or offline unit tests
    }
  };

  const loadCatalogueData = async () => {
    try {
      const [recRes, ingRes] = await Promise.all([api.getRecipes(), api.getIngredients()]);
      setCatalogueRecipes(recRes);
      setCatalogueIngredients(ingRes);
    } catch {
      // Non-blocking
    }
  };

  const executeIngredientSearch = async (ingredientsToSearch: string[]) => {
    setIsSearching(true);
    setSearchError(null);
    try {
      const excludedList = parseIngredientInputTokens(excludedInput);
      const res = await api.searchByIngredients({
        ingredients: ingredientsToSearch,
        dietary_filters: dietaryFilter ? [dietaryFilter] : undefined,
        excluded_ingredients: excludedList.length > 0 ? excludedList : undefined,
        max_total_minutes: maxMinutes ? Number(maxMinutes) : undefined,
        difficulty: difficultyFilter || undefined,
        sort_by: sortBy,
        include_ai_explanation: includeAiExplanation,
      });
      setSearchResult(res);
    } catch (err) {
      setSearchError(err instanceof Error ? err.message : 'Unable to search recipes.');
    } finally {
      setIsSearching(false);
    }
  };

  useEffect(() => {
    loadCatalogueData();
    loadUserWorkspaceData();
    executeIngredientSearch(selectedIngredients);
  }, []);

  const handleAddIngredientsFromInput = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputValue.trim()) {
      setSearchError('Please enter at least one ingredient name (e.g., "potato, onion, tomato").');
      return;
    }
    const tokens = parseIngredientInputTokens(inputValue);
    if (tokens.length === 0) return;

    setSearchError(null);
    const merged = Array.from(new Set([...selectedIngredients, ...tokens]));
    setSelectedIngredients(merged);
    setRecentIngredients((prev) => Array.from(new Set([...tokens, ...prev])).slice(0, 8));
    setInputValue('');
    executeIngredientSearch(merged);
  };

  const handleAddSingleChip = (name: string) => {
    const clean = name.trim().toLowerCase();
    if (!clean) return;
    if (selectedIngredients.includes(clean)) return;
    const next = [...selectedIngredients, clean];
    setSelectedIngredients(next);
    executeIngredientSearch(next);
  };

  const handleRemoveChip = (name: string) => {
    const next = selectedIngredients.filter((item) => item !== name);
    setSelectedIngredients(next);
    executeIngredientSearch(next);
  };

  const handleClearAllChips = () => {
    setSelectedIngredients([]);
    executeIngredientSearch([]);
  };

  const handleUsePantryIngredients = () => {
    if (pantryItems.length === 0) {
      setActiveTab('pantry');
      return;
    }
    const pantryNames = pantryItems.map((p) => p.canonical_name);
    const merged = Array.from(new Set([...selectedIngredients, ...pantryNames]));
    setSelectedIngredients(merged);
    setActiveTab('discover');
    executeIngredientSearch(merged);
  };

  const handleOpenRecipeDetail = async (recipeId: string, preloaded?: RecipeDetailOut) => {
    if (preloaded) {
      setSelectedRecipeDetail(preloaded);
      return;
    }
    try {
      const detail = await api.getRecipeById(recipeId, selectedIngredients);
      setSelectedRecipeDetail(detail);
    } catch (err) {
      setSearchError(err instanceof Error ? err.message : 'Could not load recipe details.');
    }
  };

  const handleToggleFavourite = async (recipeId: string) => {
    const exists = favourites.some((f) => f.recipe_id === recipeId);
    try {
      if (exists) {
        await api.removeFavourite(recipeId);
      } else {
        await api.addFavourite(recipeId);
      }
      const updated = await api.getFavourites();
      setFavourites(updated);
    } catch (err) {
      setSearchError(err instanceof Error ? err.message : 'Failed to update favourites.');
    }
  };

  const handleAddMissingToShoppingList = async (
    recipeId: string,
    items: RecipeIngredientOut[]
  ) => {
    for (const item of items) {
      await api.addShoppingItem({
        ingredient_name: item.canonical_name,
        quantity: item.quantity ?? 1,
        unit: item.unit,
        related_recipe_id: recipeId,
      });
    }
    const updatedList = await api.getShoppingList();
    setShoppingList(updatedList);
  };

  const handleAddPantrySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPantryError(null);
    if (!newPantryName.trim()) {
      setPantryError('Enter a valid canonical ingredient name.');
      return;
    }
    try {
      await api.addPantryItem({
        ingredient_name: newPantryName.trim(),
        quantity: Number(newPantryQty) || 1,
        unit: newPantryUnit.trim() || 'piece',
        best_before_date: newPantryBestBefore || undefined,
        storage_note: newPantryNote || undefined,
      });
      setNewPantryName('');
      setNewPantryNote('');
      setNewPantryBestBefore('');
      const refreshed = await api.getPantryItems(pantrySearch);
      setPantryItems(refreshed);
    } catch (err) {
      setPantryError(err instanceof Error ? err.message : 'Unable to add pantry item.');
    }
  };

  const handleUpdatePantryQty = async (item: PantryItemOut, delta: number) => {
    const nextQty = Math.max(0.5, Number((item.quantity + delta).toFixed(2)));
    try {
      await api.updatePantryItem(item.id, { quantity: nextQty });
      const refreshed = await api.getPantryItems(pantrySearch);
      setPantryItems(refreshed);
    } catch (err) {
      setPantryError(err instanceof Error ? err.message : 'Could not update quantity.');
    }
  };

  const handleDeletePantryItem = async (id: number) => {
    try {
      await api.deletePantryItem(id);
      setPantryItems((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      setPantryError(err instanceof Error ? err.message : 'Could not delete item.');
    }
  };

  const handleAddShoppingSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setShoppingError(null);
    if (!newShopName.trim()) {
      setShoppingError('Please enter an item name.');
      return;
    }
    try {
      await api.addShoppingItem({
        ingredient_name: newShopName.trim(),
        quantity: Number(newShopQty) || 1,
        unit: newShopUnit.trim() || 'piece',
      });
      setNewShopName('');
      const refreshed = await api.getShoppingList();
      setShoppingList(refreshed);
    } catch (err) {
      setShoppingError(err instanceof Error ? err.message : 'Could not add shopping item.');
    }
  };

  const handleToggleShoppingItem = async (itemId: number, completed: boolean) => {
    try {
      await api.updateShoppingItem(itemId, { completed });
      const refreshed = await api.getShoppingList();
      setShoppingList(refreshed);
    } catch (err) {
      setShoppingError(err instanceof Error ? err.message : 'Could not update shopping item.');
    }
  };

  const handleDeleteShoppingItem = async (itemId: number) => {
    try {
      await api.deleteShoppingItem(itemId);
      const refreshed = await api.getShoppingList();
      setShoppingList(refreshed);
    } catch (err) {
      setShoppingError(err instanceof Error ? err.message : 'Could not remove item.');
    }
  };

  const handleClearCompletedShopping = async () => {
    try {
      const updated = await api.clearCompletedShoppingItems();
      setShoppingList(updated);
    } catch (err) {
      setShoppingError(err instanceof Error ? err.message : 'Could not clear completed items.');
    }
  };

  const handleSwitchUser = async (nextUserId: string) => {
    setActiveUserId(nextUserId);
    setCurrentUserId(nextUserId);
    await loadUserWorkspaceData();
  };

  const favouriteIds = new Set(favourites.map((f) => f.recipe_id));
  const pendingShoppingCount = shoppingList
    ? shoppingList.items.filter((i) => !i.completed).length
    : 0;

  return (
    <div className="app-shell">
      {/* Top Navigation Header */}
      <header className="site-header">
        <div className="header-inner">
          <button
            type="button"
            className="brand-group"
            onClick={() => setActiveTab('discover')}
            aria-label="Leftover Chef Home"
          >
            <div className="brand-logo">
              <ChefHat size={24} />
            </div>
            <div>
              <span className="brand-title">LEFTOVER CHEF</span>
              <span className="brand-subtitle">Smart Recipe Discovery &amp; Ingredient Matching</span>
            </div>
          </button>

          <nav className="main-nav" aria-label="Main navigation">
            <button
              type="button"
              className={`nav-btn ${activeTab === 'discover' ? 'active' : ''}`}
              onClick={() => setActiveTab('discover')}
            >
              <Search size={16} /> Match Ingredients
            </button>
            <button
              type="button"
              className={`nav-btn ${activeTab === 'catalogue' ? 'active' : ''}`}
              onClick={() => setActiveTab('catalogue')}
            >
              <Utensils size={16} /> Recipe Catalogue
            </button>
            <button
              type="button"
              className={`nav-btn ${activeTab === 'pantry' ? 'active' : ''}`}
              onClick={() => setActiveTab('pantry')}
            >
              <Package size={16} /> My Pantry
              {pantryItems.length > 0 && <span className="nav-badge">{pantryItems.length}</span>}
            </button>
            <button
              type="button"
              className={`nav-btn ${activeTab === 'shopping' ? 'active' : ''}`}
              onClick={() => setActiveTab('shopping')}
            >
              <ShoppingCart size={16} /> Shopping List
              {pendingShoppingCount > 0 && <span className="nav-badge">{pendingShoppingCount}</span>}
            </button>
            <button
              type="button"
              className={`nav-btn ${activeTab === 'favourites' ? 'active' : ''}`}
              onClick={() => setActiveTab('favourites')}
            >
              <Heart size={16} /> Favourites
              {favourites.length > 0 && <span className="nav-badge">{favourites.length}</span>}
            </button>
            <button
              type="button"
              className={`nav-btn ${activeTab === 'profile' ? 'active' : ''}`}
              onClick={() => setActiveTab('profile')}
            >
              <User size={16} /> Preferences
            </button>
            <button
              type="button"
              className={`nav-btn ${activeTab === 'about' ? 'active' : ''}`}
              onClick={() => setActiveTab('about')}
            >
              <Info size={16} /> Food Safety &amp; Credits
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {activeTab === 'discover' && (
          <>
            {/* Hero & Natural Ingredient Input */}
            <section className="hero-banner" aria-labelledby="hero-heading">
              <div className="hero-eyebrow">
                <Sparkles size={14} /> Zero-Waste Culinary Matching Engine
              </div>
              <h1 id="hero-heading" className="hero-title">
                Cook delicious meals with the ingredients you already have.
              </h1>
              <p className="hero-lead">
                Enter your leftover vegetables, grains, dairy, or spices below. Leftover Chef normalises
                aliases, preserves important culinary and allergen distinctions, and ranks verified recipes
                by exact required ingredient coverage.
              </p>

              <div className="ingredient-entry-box">
                <form onSubmit={handleAddIngredientsFromInput} className="input-row">
                  <input
                    type="text"
                    className="ingredient-input"
                    placeholder="Enter ingredients (e.g., potato, onion, tomato, rice, cheese)..."
                    aria-label="Enter ingredients you have"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                  />
                  <button type="submit" className="btn btn-primary">
                    <Plus size={16} /> Add Ingredients
                  </button>
                  <button
                    type="button"
                    className="btn btn-amber"
                    onClick={() => executeIngredientSearch(selectedIngredients)}
                    disabled={isSearching}
                  >
                    <Search size={16} /> {isSearching ? 'Matching...' : 'Find Matching Recipes'}
                  </button>
                  <button
                    type="button"
                    className="btn btn-outline"
                    onClick={handleUsePantryIngredients}
                  >
                    <Package size={16} /> Use Pantry ({pantryItems.length})
                  </button>
                </form>

                {/* Active Ingredient Chips */}
                <div className="chips-section">
                  <div className="chips-label">
                    <span>Your Active Ingredients ({selectedIngredients.length}):</span>
                    {selectedIngredients.length > 0 && (
                      <button
                        type="button"
                        className="btn btn-outline btn-sm"
                        onClick={handleClearAllChips}
                      >
                        Clear All
                      </button>
                    )}
                  </div>
                  {selectedIngredients.length === 0 ? (
                    <p style={{ fontSize: '0.86rem', color: 'var(--text-muted)' }}>
                      No ingredients selected yet. Add ingredients above or click a suggestion below.
                    </p>
                  ) : (
                    <div className="chip-list" role="list" aria-label="Selected ingredients">
                      {selectedIngredients.map((ing) => (
                        <span key={ing} className="ingredient-chip" role="listitem">
                          {ing}
                          <button
                            type="button"
                            className="chip-remove-btn"
                            onClick={() => handleRemoveChip(ing)}
                            aria-label={`Remove ${ing}`}
                          >
                            &times;
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Quick-Add Suggestions & Recent */}
                <div className="chips-section">
                  <div className="chips-label">
                    <span>Suggested Staples (click to add):</span>
                  </div>
                  <div className="chip-list">
                    {QUICK_SUGGESTIONS.filter((s) => !selectedIngredients.includes(s)).map((sug) => (
                      <button
                        key={sug}
                        type="button"
                        className="suggestion-chip"
                        onClick={() => handleAddSingleChip(sug)}
                      >
                        + {sug}
                      </button>
                    ))}
                  </div>
                </div>

                {recentIngredients.length > 0 && (
                  <div className="chips-section">
                    <div className="chips-label">
                      <span>Recently Used:</span>
                    </div>
                    <div className="chip-list">
                      {recentIngredients
                        .filter((r) => !selectedIngredients.includes(r))
                        .map((rec) => (
                          <button
                            key={rec}
                            type="button"
                            className="suggestion-chip"
                            onClick={() => handleAddSingleChip(rec)}
                          >
                            + {rec}
                          </button>
                        ))}
                    </div>
                  </div>
                )}

                {/* Search Filters & Sorting */}
                <div className="filters-bar">
                  <div className="field-group">
                    <label htmlFor="sort-select">Sort Recipes By</label>
                    <select
                      id="sort-select"
                      className="select-input"
                      value={sortBy}
                      onChange={(e) => {
                        setSortBy(e.target.value);
                      }}
                    >
                      <option value="best_match">Best Ingredient Match</option>
                      <option value="fewest_missing">Fewest Missing Ingredients</option>
                      <option value="shortest_time">Shortest Total Cooking Time</option>
                      <option value="alphabetical">Alphabetical (A–Z)</option>
                    </select>
                  </div>

                  <div className="field-group">
                    <label htmlFor="dietary-select">Dietary Preference</label>
                    <select
                      id="dietary-select"
                      className="select-input"
                      value={dietaryFilter}
                      onChange={(e) => setDietaryFilter(e.target.value)}
                    >
                      <option value="">All Dietary Types</option>
                      <option value="vegetarian">Vegetarian</option>
                      <option value="vegan">Vegan</option>
                      <option value="gluten-free">Gluten-Free</option>
                      <option value="dairy-free">Dairy-Free</option>
                      <option value="nut-free">Nut-Free</option>
                    </select>
                  </div>

                  <div className="field-group">
                    <label htmlFor="difficulty-select">Difficulty</label>
                    <select
                      id="difficulty-select"
                      className="select-input"
                      value={difficultyFilter}
                      onChange={(e) => setDifficultyFilter(e.target.value)}
                    >
                      <option value="">Any Difficulty</option>
                      <option value="Easy">Easy</option>
                      <option value="Medium">Medium</option>
                    </select>
                  </div>

                  <div className="field-group">
                    <label htmlFor="max-time-select">Max Total Time</label>
                    <select
                      id="max-time-select"
                      className="select-input"
                      value={maxMinutes}
                      onChange={(e) => setMaxMinutes(e.target.value)}
                    >
                      <option value="">Any Duration</option>
                      <option value="15">Up to 15 mins</option>
                      <option value="25">Up to 25 mins</option>
                      <option value="35">Up to 35 mins</option>
                    </select>
                  </div>

                  <div className="field-group">
                    <label htmlFor="exclude-input">Exclude Ingredients</label>
                    <input
                      id="exclude-input"
                      type="text"
                      className="text-input"
                      placeholder="e.g. peanuts, milk"
                      value={excludedInput}
                      onChange={(e) => setExcludedInput(e.target.value)}
                    />
                  </div>

                  <div className="field-group">
                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={includeAiExplanation}
                        onChange={(e) => setIncludeAiExplanation(e.target.checked)}
                      />
                      Show Match Assistant Notes
                    </label>
                    <button
                      type="button"
                      className="btn btn-primary btn-sm"
                      onClick={() => executeIngredientSearch(selectedIngredients)}
                    >
                      Apply Filters
                    </button>
                  </div>
                </div>
              </div>
            </section>

            {/* Error & Unrecognised Warnings */}
            {searchError && (
              <div className="notice-banner notice-danger" role="alert">
                <AlertCircle size={16} style={{ verticalAlign: 'middle', marginRight: '0.4rem' }} />
                {searchError}
              </div>
            )}

            {searchResult && searchResult.unrecognised_inputs.length > 0 && (
              <div className="notice-banner notice-warn" role="status">
                <strong>Unrecognised ingredient input(s):</strong>{' '}
                {searchResult.unrecognised_inputs.join(', ')}. These items were not found in the local
                canonical catalogue and were excluded from matching.
              </div>
            )}

            {searchResult && searchResult.no_match_guidance && (
              <div className="notice-banner" role="status">
                {searchResult.no_match_guidance}
              </div>
            )}

            {/* Results Header & Transparent Formula Box */}
            <section aria-labelledby="results-heading">
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'baseline',
                  flexWrap: 'wrap',
                  gap: '0.5rem',
                }}
              >
                <h2 id="results-heading" style={{ fontSize: '1.35rem', fontWeight: 800 }}>
                  Matching Recipes ({searchResult ? searchResult.matched_recipes.length : 0})
                </h2>
                {searchResult && (
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {searchResult.score_formula_description}
                  </span>
                )}
              </div>

              {isSearching && (
                <div className="panel-card" style={{ textAlign: 'center', marginTop: '1rem' }}>
                  Searching catalogue and calculating ingredient coverage...
                </div>
              )}

              {!isSearching && searchResult && searchResult.matched_recipes.length === 0 && (
                <div className="panel-card" style={{ textAlign: 'center', marginTop: '1rem' }}>
                  <h3 style={{ marginBottom: '0.5rem' }}>No matching recipes found</h3>
                  <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                    Try adding staple ingredients like <strong>potato, onion, tomato, rice</strong> or
                    relaxing active dietary/time filters.
                  </p>
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => {
                      const defaults = ['potato', 'onion', 'tomato', 'rice'];
                      setSelectedIngredients(defaults);
                      setDietaryFilter('');
                      setExcludedInput('');
                      setMaxMinutes('');
                      setDifficultyFilter('');
                      executeIngredientSearch(defaults);
                    }}
                  >
                    Reset to Sample Leftover Basket
                  </button>
                </div>
              )}

              {!isSearching && searchResult && searchResult.matched_recipes.length > 0 && (
                <div className="recipe-grid">
                  {searchResult.matched_recipes.map((match: MatchedRecipeOut) => {
                    const { recipe } = match;
                    const isFav = favouriteIds.has(recipe.id);
                    return (
                      <article key={recipe.id} className="recipe-card">
                        <div className="recipe-card-media">
                          <RecipeIllustration
                            recipeId={recipe.id}
                            cuisine={recipe.cuisine}
                            title={recipe.name}
                          />
                          <span className="match-score-pill">
                            {match.core_coverage_score}% Required Match
                          </span>
                          <button
                            type="button"
                            className={`fav-icon-btn ${isFav ? 'active' : ''}`}
                            onClick={() => handleToggleFavourite(recipe.id)}
                            aria-label={
                              isFav
                                ? `Remove ${recipe.name} from favourites`
                                : `Save ${recipe.name} to favourites`
                            }
                          >
                            <Heart size={17} fill={isFav ? '#a62626' : 'none'} />
                          </button>
                        </div>

                        <div className="recipe-card-body">
                          <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                            {recipe.dietary_attributes.map((attr) => (
                              <span key={attr} className="badge-tag">
                                {attr}
                              </span>
                            ))}
                          </div>

                          <h3 className="recipe-card-title">{recipe.name}</h3>
                          <p className="recipe-card-desc">{recipe.description}</p>

                          <div className="recipe-meta-row">
                            <span className="meta-item">
                              <Clock size={14} /> Prep {recipe.preparation_minutes}m &bull; Cook{' '}
                              {recipe.cooking_minutes}m ({recipe.total_minutes}m)
                            </span>
                            <span className="meta-item">
                              Serves {recipe.default_servings} &bull; {recipe.difficulty}
                            </span>
                          </div>

                          <div className="match-breakdown-box">
                            <div className="match-line">
                              <span className="badge-tag badge-matched">
                                Matched Required: {match.matched_required_count}/
                                {match.total_required_count}
                              </span>
                              <span className="badge-tag badge-missing">
                                Missing Required: {match.missing_required_count}
                              </span>
                            </div>
                            <div style={{ marginTop: '0.35rem', color: 'var(--text-primary)' }}>
                              <strong>Have:</strong>{' '}
                              {match.matched_required_ingredients
                                .map((i) => i.canonical_name)
                                .join(', ') || 'None'}
                            </div>
                            {match.missing_required_ingredients.length > 0 && (
                              <div style={{ marginTop: '0.2rem', color: 'var(--status-warn)' }}>
                                <strong>Need:</strong>{' '}
                                {match.missing_required_ingredients
                                  .map((i) => `${i.canonical_name} (${i.display_quantity})`)
                                  .join(', ')}
                              </div>
                            )}
                          </div>

                          {match.ai_suggestion && (
                            <div
                              style={{
                                backgroundColor: 'var(--olive-light)',
                                padding: '0.6rem 0.75rem',
                                borderRadius: '6px',
                                fontSize: '0.78rem',
                              }}
                            >
                              <strong>{match.ai_suggestion.label}:</strong>{' '}
                              {match.ai_suggestion.explanation}
                              <div style={{ fontStyle: 'italic', marginTop: '0.2rem' }}>
                                {match.ai_suggestion.safety_disclaimer}
                              </div>
                            </div>
                          )}

                          <div
                            style={{
                              marginTop: 'auto',
                              paddingTop: '0.5rem',
                              display: 'flex',
                              gap: '0.5rem',
                            }}
                          >
                            <button
                              type="button"
                              className="btn btn-primary"
                              style={{ flex: 1 }}
                              onClick={() => handleOpenRecipeDetail(recipe.id, recipe)}
                            >
                              <BookOpen size={16} /> View Recipe
                            </button>
                            {match.missing_required_ingredients.length > 0 && (
                              <button
                                type="button"
                                className="btn btn-outline"
                                onClick={() =>
                                  handleAddMissingToShoppingList(
                                    recipe.id,
                                    match.missing_required_ingredients
                                  )
                                }
                                title="Add missing required ingredients to shopping list"
                              >
                                <ShoppingCart size={16} />
                              </button>
                            )}
                          </div>
                        </div>
                      </article>
                    );
                  })}
                </div>
              )}
            </section>
          </>
        )}

        {/* BROWSE FULL CATALOGUE */}
        {activeTab === 'catalogue' && (
          <section aria-labelledby="catalogue-heading">
            <div className="panel-card">
              <h1 id="catalogue-heading" style={{ fontSize: '1.5rem', fontWeight: 800 }}>
                Verified Local Recipe &amp; Ingredient Catalogue
              </h1>
              <p style={{ color: 'var(--text-secondary)', marginTop: '0.35rem' }}>
                Browse all {catalogueRecipes.length} structured recipes and{' '}
                {catalogueIngredients.length} canonical ingredients with preserved culinary
                distinctions (e.g., dairy milk vs coconut milk, wheat flour vs rice flour, bulb onion
                vs spring onion, peanuts vs tree nuts).
              </p>
            </div>

            <div className="recipe-grid">
              {catalogueRecipes.map((rec) => (
                <article key={rec.id} className="recipe-card">
                  <div className="recipe-card-media">
                    <RecipeIllustration
                      recipeId={rec.id}
                      cuisine={rec.cuisine}
                      title={rec.name}
                    />
                  </div>
                  <div className="recipe-card-body">
                    <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                      {rec.dietary_attributes.map((attr) => (
                        <span key={attr} className="badge-tag">
                          {attr}
                        </span>
                      ))}
                    </div>
                    <h3 className="recipe-card-title">{rec.name}</h3>
                    <p className="recipe-card-desc">{rec.description}</p>
                    <div className="recipe-meta-row">
                      <span>Total: {rec.total_minutes} mins</span>
                      <span>Required items: {rec.required_ingredient_count}</span>
                      <span>{rec.difficulty}</span>
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      {rec.allergen_summary_notice}
                    </div>
                    <button
                      type="button"
                      className="btn btn-primary"
                      style={{ marginTop: 'auto' }}
                      onClick={() => handleOpenRecipeDetail(rec.id)}
                    >
                      <BookOpen size={16} /> View Recipe &amp; Quantities
                    </button>
                  </div>
                </article>
              ))}
            </div>
          </section>
        )}

        {/* MY PANTRY */}
        {activeTab === 'pantry' && (
          <section aria-labelledby="pantry-heading">
            <div className="panel-card">
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '1rem',
                }}
              >
                <div>
                  <h1 id="pantry-heading" style={{ fontSize: '1.5rem', fontWeight: 800 }}>
                    My Kitchen Pantry
                  </h1>
                  <p style={{ color: 'var(--text-secondary)' }}>
                    Track staple ingredients you keep at home and use them directly in recipe search.
                  </p>
                </div>
                <button
                  type="button"
                  className="btn btn-amber"
                  onClick={handleUsePantryIngredients}
                  disabled={pantryItems.length === 0}
                >
                  <Search size={16} /> Search Recipes Using Pantry ({pantryItems.length})
                </button>
              </div>

              <div className="notice-banner notice-warn" style={{ marginTop: '1rem' }}>
                <strong>Food Safety Precaution:</strong> Adding an item to this digital pantry or
                recording a best-before date does <em>not</em> guarantee that food is safe to eat.
                Always verify storage temperature, aroma, and physical condition before cooking.
              </div>

              {pantryError && <div className="notice-banner notice-danger">{pantryError}</div>}

              <form onSubmit={handleAddPantrySubmit} className="filters-bar">
                <div className="field-group">
                  <label htmlFor="pantry-ing-input">Ingredient Name</label>
                  <input
                    id="pantry-ing-input"
                    type="text"
                    className="text-input"
                    placeholder="e.g., potato, rice, coconut milk"
                    value={newPantryName}
                    onChange={(e) => setNewPantryName(e.target.value)}
                    list="canonical-ingredient-options"
                  />
                  <datalist id="canonical-ingredient-options">
                    {catalogueIngredients.map((i) => (
                      <option key={i.id} value={i.canonical_name} />
                    ))}
                  </datalist>
                </div>

                <div className="field-group">
                  <label htmlFor="pantry-qty-input">Quantity</label>
                  <input
                    id="pantry-qty-input"
                    type="number"
                    step="0.25"
                    min="0.25"
                    className="text-input"
                    value={newPantryQty}
                    onChange={(e) => setNewPantryQty(e.target.value)}
                  />
                </div>

                <div className="field-group">
                  <label htmlFor="pantry-unit-select">Unit</label>
                  <select
                    id="pantry-unit-select"
                    className="select-input"
                    value={newPantryUnit}
                    onChange={(e) => setNewPantryUnit(e.target.value)}
                  >
                    <option value="piece">piece</option>
                    <option value="g">g</option>
                    <option value="kg">kg</option>
                    <option value="ml">ml</option>
                    <option value="litre">litre</option>
                    <option value="tablespoon">tablespoon</option>
                    <option value="teaspoon">teaspoon</option>
                    <option value="cup">cup</option>
                  </select>
                </div>

                <div className="field-group">
                  <label htmlFor="pantry-date-input">Best-Before Date (Optional)</label>
                  <input
                    id="pantry-date-input"
                    type="date"
                    className="text-input"
                    value={newPantryBestBefore}
                    onChange={(e) => setNewPantryBestBefore(e.target.value)}
                  />
                </div>

                <div className="field-group">
                  <label htmlFor="pantry-note-input">Storage Note (Optional)</label>
                  <input
                    id="pantry-note-input"
                    type="text"
                    className="text-input"
                    placeholder="e.g., Refrigerated"
                    value={newPantryNote}
                    onChange={(e) => setNewPantryNote(e.target.value)}
                  />
                </div>

                <button type="submit" className="btn btn-primary">
                  <Plus size={16} /> Add to Pantry
                </button>
              </form>
            </div>

            <div className="panel-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
                <h2 style={{ fontSize: '1.15rem', fontWeight: 700 }}>
                  Stored Pantry Items ({pantryItems.length})
                </h2>
                <input
                  type="text"
                  className="text-input"
                  placeholder="Filter pantry items..."
                  value={pantrySearch}
                  onChange={async (e) => {
                    const val = e.target.value;
                    setPantrySearch(val);
                    const filtered = await api.getPantryItems(val);
                    setPantryItems(filtered);
                  }}
                />
              </div>

              {pantryItems.length === 0 ? (
                <p style={{ color: 'var(--text-secondary)', marginTop: '1rem' }}>
                  Your pantry is currently empty. Add staple items above to track quantities.
                </p>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Ingredient</th>
                      <th>Category</th>
                      <th>Available Quantity</th>
                      <th>Best-Before (Ref Only)</th>
                      <th>Storage Note</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pantryItems.map((item) => (
                      <tr key={item.id}>
                        <td>
                          <strong>{item.canonical_name}</strong>
                        </td>
                        <td>
                          <span className="badge-tag">{item.category}</span>
                        </td>
                        <td>{item.display_quantity}</td>
                        <td>{item.best_before_date || '—'}</td>
                        <td>{item.storage_note || '—'}</td>
                        <td style={{ display: 'flex', gap: '0.4rem' }}>
                          <button
                            type="button"
                            className="btn btn-outline btn-sm"
                            onClick={() => handleUpdatePantryQty(item, 1)}
                          >
                            +1
                          </button>
                          <button
                            type="button"
                            className="btn btn-outline btn-sm"
                            onClick={() => handleUpdatePantryQty(item, -1)}
                          >
                            -1
                          </button>
                          <button
                            type="button"
                            className="btn btn-outline btn-sm"
                            onClick={() => handleDeletePantryItem(item.id)}
                            aria-label={`Delete ${item.canonical_name}`}
                          >
                            <Trash2 size={14} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </section>
        )}

        {/* SHOPPING LIST */}
        {activeTab === 'shopping' && (
          <section aria-labelledby="shopping-heading">
            <div className="panel-card">
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '1rem',
                }}
              >
                <div>
                  <h1 id="shopping-heading" style={{ fontSize: '1.5rem', fontWeight: 800 }}>
                    Shopping List for Missing Ingredients
                  </h1>
                  <p style={{ color: 'var(--text-secondary)' }}>
                    {shoppingList?.unit_handling_note ||
                      'Compatible units are merged automatically; incompatible units remain separate.'}
                  </p>
                </div>
                {shoppingList && shoppingList.items.some((i) => i.completed) && (
                  <button
                    type="button"
                    className="btn btn-outline btn-sm"
                    onClick={handleClearCompletedShopping}
                  >
                    Clear Purchased Items
                  </button>
                )}
              </div>

              {shoppingError && <div className="notice-banner notice-danger">{shoppingError}</div>}

              <form onSubmit={handleAddShoppingSubmit} className="filters-bar">
                <div className="field-group">
                  <label htmlFor="shop-name-input">Ingredient Name</label>
                  <input
                    id="shop-name-input"
                    type="text"
                    className="text-input"
                    placeholder="e.g., turmeric powder, cheese"
                    value={newShopName}
                    onChange={(e) => setNewShopName(e.target.value)}
                  />
                </div>
                <div className="field-group">
                  <label htmlFor="shop-qty-input">Quantity</label>
                  <input
                    id="shop-qty-input"
                    type="number"
                    step="0.25"
                    min="0.25"
                    className="text-input"
                    value={newShopQty}
                    onChange={(e) => setNewShopQty(e.target.value)}
                  />
                </div>
                <div className="field-group">
                  <label htmlFor="shop-unit-select">Unit</label>
                  <select
                    id="shop-unit-select"
                    className="select-input"
                    value={newShopUnit}
                    onChange={(e) => setNewShopUnit(e.target.value)}
                  >
                    <option value="piece">piece</option>
                    <option value="g">g</option>
                    <option value="kg">kg</option>
                    <option value="ml">ml</option>
                    <option value="litre">litre</option>
                    <option value="tablespoon">tablespoon</option>
                    <option value="teaspoon">teaspoon</option>
                    <option value="cup">cup</option>
                  </select>
                </div>
                <button type="submit" className="btn btn-primary">
                  <Plus size={16} /> Add Item
                </button>
              </form>
            </div>

            <div className="panel-card">
              {!shoppingList || shoppingList.items.length === 0 ? (
                <p style={{ color: 'var(--text-secondary)' }}>
                  Your shopping list is empty. Add missing ingredients directly from any recipe card
                  or add items above.
                </p>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Purchased</th>
                      <th>Ingredient</th>
                      <th>Quantity &amp; Unit</th>
                      <th>Related Recipe</th>
                      <th>Remove</th>
                    </tr>
                  </thead>
                  <tbody>
                    {shoppingList.items.map((item) => (
                      <tr
                        key={item.id}
                        style={{
                          opacity: item.completed ? 0.55 : 1,
                          textDecoration: item.completed ? 'line-through' : 'none',
                        }}
                      >
                        <td>
                          <input
                            type="checkbox"
                            checked={item.completed}
                            onChange={(e) => handleToggleShoppingItem(item.id, e.target.checked)}
                            aria-label={`Mark ${item.ingredient_name} as purchased`}
                          />
                        </td>
                        <td>
                          <strong>{item.ingredient_name}</strong>
                        </td>
                        <td>{item.display_quantity}</td>
                        <td>{item.related_recipe_name || 'Manual entry'}</td>
                        <td>
                          <button
                            type="button"
                            className="btn btn-outline btn-sm"
                            onClick={() => handleDeleteShoppingItem(item.id)}
                            aria-label={`Remove ${item.ingredient_name}`}
                          >
                            <Trash2 size={14} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </section>
        )}

        {/* FAVOURITES */}
        {activeTab === 'favourites' && (
          <section aria-labelledby="favourites-heading">
            <div className="panel-card">
              <h1 id="favourites-heading" style={{ fontSize: '1.5rem', fontWeight: 800 }}>
                Saved Favourite Recipes ({favourites.length})
              </h1>
              <p style={{ color: 'var(--text-secondary)' }}>
                Quickly revisit recipes you love cooking with your leftover ingredients.
              </p>
            </div>

            {favourites.length === 0 ? (
              <div className="panel-card">
                <p style={{ color: 'var(--text-secondary)' }}>
                  You have not saved any favourite recipes yet. Click the heart icon on any recipe card
                  to save it here.
                </p>
              </div>
            ) : (
              <div className="recipe-grid">
                {favourites.map((fav) => (
                  <article key={fav.id} className="recipe-card">
                    <div className="recipe-card-media">
                      <RecipeIllustration
                        recipeId={fav.recipe_id}
                        cuisine={fav.cuisine}
                        title={fav.recipe_name}
                      />
                    </div>
                    <div className="recipe-card-body">
                      <h3 className="recipe-card-title">{fav.recipe_name}</h3>
                      <div className="recipe-meta-row">
                        <span>Total Time: {fav.total_minutes} mins</span>
                        <span>Difficulty: {fav.difficulty}</span>
                      </div>
                      <div style={{ display: 'flex', gap: '0.5rem', marginTop: 'auto' }}>
                        <button
                          type="button"
                          className="btn btn-primary"
                          style={{ flex: 1 }}
                          onClick={() => handleOpenRecipeDetail(fav.recipe_id)}
                        >
                          <BookOpen size={16} /> View Details
                        </button>
                        <button
                          type="button"
                          className="btn btn-outline"
                          onClick={() => handleToggleFavourite(fav.recipe_id)}
                          aria-label={`Remove ${fav.recipe_name} from favourites`}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        )}

        {/* PROFILE & PREFERENCES */}
        {activeTab === 'profile' && (
          <section aria-labelledby="profile-heading">
            <div className="panel-card">
              <h1 id="profile-heading" style={{ fontSize: '1.5rem', fontWeight: 800 }}>
                Chef Profile &amp; Culinary Preferences
              </h1>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                Manage your workspace profile and default cooking preferences.
              </p>

              <div className="notice-banner notice-warn">
                <strong>Medical &amp; Allergen Disclaimer:</strong>{' '}
                {profile?.medical_disclaimer ||
                  'Dietary preferences are culinary filters only and must not be treated as a medical guarantee of allergen safety.'}
              </div>

              {profileSavedMsg && <div className="notice-banner">{profileSavedMsg}</div>}

              <div style={{ marginBottom: '1.25rem' }}>
                <label htmlFor="workspace-switcher" style={{ fontWeight: 700, fontSize: '0.86rem', display: 'block', marginBottom: '0.35rem' }}>
                  Active Chef Workspace (Demonstrates User Isolation):
                </label>
                <select
                  id="workspace-switcher"
                  className="select-input"
                  value={currentUserId}
                  onChange={(e) => handleSwitchUser(e.target.value)}
                >
                  <option value="default_chef">default_chef (Primary Household)</option>
                  <option value="student_kitchen">student_kitchen (Hostel / Student Kitchen)</option>
                  <option value="family_pantry">family_pantry (Family Weeknight Pantry)</option>
                </select>
              </div>

              {profile && (
                <form
                  onSubmit={async (e) => {
                    e.preventDefault();
                    const updated = await api.updateProfile({
                      display_name: profile.display_name,
                      preferred_cuisine: profile.preferred_cuisine,
                      typical_serving_size: profile.typical_serving_size,
                    });
                    setProfile(updated);
                    setProfileSavedMsg('Preferences saved successfully.');
                  }}
                  className="filters-bar"
                >
                  <div className="field-group">
                    <label htmlFor="prof-name">Display Name</label>
                    <input
                      id="prof-name"
                      type="text"
                      className="text-input"
                      value={profile.display_name}
                      onChange={(e) => setProfile({ ...profile, display_name: e.target.value })}
                    />
                  </div>
                  <div className="field-group">
                    <label htmlFor="prof-cuisine">Preferred Cuisine</label>
                    <input
                      id="prof-cuisine"
                      type="text"
                      className="text-input"
                      placeholder="e.g., Indian, Mediterranean"
                      value={profile.preferred_cuisine || ''}
                      onChange={(e) =>
                        setProfile({ ...profile, preferred_cuisine: e.target.value })
                      }
                    />
                  </div>
                  <div className="field-group">
                    <label htmlFor="prof-servings">Typical Serving Size</label>
                    <input
                      id="prof-servings"
                      type="number"
                      min="1"
                      max="50"
                      className="text-input"
                      value={profile.typical_serving_size}
                      onChange={(e) =>
                        setProfile({
                          ...profile,
                          typical_serving_size: Number(e.target.value) || 2,
                        })
                      }
                    />
                  </div>
                  <button type="submit" className="btn btn-primary">
                    <Check size={16} /> Save Profile
                  </button>
                </form>
              )}
            </div>
          </section>
        )}

        {/* ABOUT, HOW MATCHING WORKS, FOOD SAFETY & CREDITS */}
        {activeTab === 'about' && (
          <section aria-labelledby="about-heading">
            <div className="panel-card">
              <h1 id="about-heading" style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '0.5rem' }}>
                How Ingredient Matching Works, Food Safety &amp; Credits
              </h1>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                Leftover Chef is engineered to help households cook practical meals with available
                ingredients, reduce avoidable food waste, and maintain transparent culinary data.
              </p>

              <h2 style={{ fontSize: '1.15rem', fontWeight: 700, marginTop: '1rem', marginBottom: '0.4rem' }}>
                1. Deterministic Ingredient Normalisation &amp; Matching Formula
              </h2>
              <p style={{ fontSize: '0.92rem', color: 'var(--text-secondary)', marginBottom: '0.6rem' }}>
                Every entered ingredient is lowercased, trimmed, stripped of punctuation, and
                resolved against canonical ingredient identifiers and approved aliases. Crucial
                culinary and allergen distinctions (such as <em>dairy milk vs coconut milk</em>,{' '}
                <em>wheat flour vs rice flour</em>, <em>bulb onion vs spring onion</em>, and{' '}
                <em>peanuts vs tree nuts</em>) are strictly preserved.
              </p>
              <div className="notice-banner">
                <strong>Core Coverage Formula:</strong>{' '}
                <code>
                  (Matched Required Ingredients / Total Required Ingredients) &times; 100
                </code>
                . Required spices and cooking fats are never hidden from the denominator. Optional
                garnishes are tracked separately and excluded from the required coverage denominator.
              </div>

              <h2 style={{ fontSize: '1.15rem', fontWeight: 700, marginTop: '1.25rem', marginBottom: '0.4rem' }}>
                2. Food Safety &amp; Allergen Limitations
              </h2>
              <ul style={{ paddingLeft: '1.25rem', fontSize: '0.92rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                <li>
                  Adding an ingredient to My Pantry or entering a best-before date does <strong>not</strong>{' '}
                  prove that the food is safe to eat. Always inspect food for spoilage, mould, or
                  unsafe temperature exposure.
                </li>
                <li>
                  Cooking does <strong>not</strong> automatically make spoiled food safe.
                </li>
                <li>
                  Allergen records distinguish verified base-recipe audits from unverified components.
                  Commercial brand variations and kitchen cross-contamination can always introduce
                  allergens.
                </li>
              </ul>

              <h2 style={{ fontSize: '1.15rem', fontWeight: 700, marginTop: '1.25rem', marginBottom: '0.4rem' }}>
                3. Data Provenance &amp; Developer Attribution
              </h2>
              <p style={{ fontSize: '0.92rem', color: 'var(--text-secondary)' }}>
                Recipe Catalogue: Leftover Chef Verified Test Kitchen Catalogue v1.0 (CC0-1.0 Public
                Domain Dedication). Illustrations: Original SVG culinary vectors created for Leftover
                Chef.
              </p>
              <p style={{ marginTop: '0.75rem', fontWeight: 800, color: 'var(--olive-primary)' }}>
                Developed by Anil Biradar
              </p>
            </div>
          </section>
        )}
      </main>

      {/* Recipe Details Modal */}
      {selectedRecipeDetail && (
        <RecipeDetailModal
          recipe={selectedRecipeDetail}
          isFavourite={favouriteIds.has(selectedRecipeDetail.id)}
          onToggleFavourite={handleToggleFavourite}
          onAddMissingToShoppingList={handleAddMissingToShoppingList}
          onClose={() => setSelectedRecipeDetail(null)}
        />
      )}

      {/* Persistent Production Footer */}
      <footer className="site-footer" role="contentinfo">
        <div className="footer-inner">
          <div>
            <strong>Leftover Chef</strong> &mdash; Smart Recipe Discovery and Ingredient Matching
            Platform
          </div>
          <div style={{ fontSize: '0.8rem' }}>
            Always inspect food condition and verify allergen labels before cooking.
          </div>
          <div className="developer-credit" data-testid="footer-developer-credit">
            Developed by Anil Biradar
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
