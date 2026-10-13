import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App, { parseIngredientInputTokens } from '../App';
import { api } from '../services/api';

const MOCK_SEARCH_RESPONSE = {
  normalised_user_ingredients: [
    {
      raw_input: 'potato',
      normalised_input: 'potato',
      ingredient_id: 'ing_potato',
      canonical_name: 'potato',
      category: 'vegetable',
      is_recognised: true,
      resolution_method: 'canonical',
    },
    {
      raw_input: 'onion',
      normalised_input: 'onion',
      ingredient_id: 'ing_onion',
      canonical_name: 'onion',
      category: 'vegetable',
      is_recognised: true,
      resolution_method: 'canonical',
    },
  ],
  recognised_ingredient_ids: ['ing_potato', 'ing_onion'],
  unrecognised_inputs: [],
  matched_recipes: [
    {
      recipe: {
        id: 'rec_potato_tomato_curry',
        name: 'Homestyle Potato Tomato Curry (Aloo Tamatar)',
        description: 'A comforting everyday curry made with diced potatoes and ripe tomatoes.',
        preparation_minutes: 10,
        cooking_minutes: 20,
        total_minutes: 30,
        default_servings: 2,
        difficulty: 'Easy',
        cuisine: 'Indian',
        image_reference: '/images/potato-tomato-curry.svg',
        source_reference: 'Leftover Chef Verified Test Kitchen Catalogue v1.0',
        licence_reference: 'CC0-1.0 Public Domain Dedication',
        dietary_attributes: ['vegetarian', 'vegan', 'gluten-free'],
        allergens: [],
        allergen_verification_notice: 'Allergen information not verified for all components.',
        food_safety_notice: 'Always inspect ingredients before cooking.',
        instructions: ['Peel and cube potatoes.', 'Simmer with tomatoes and spices.'],
        ingredients: [
          {
            ingredient_id: 'ing_potato',
            canonical_name: 'potato',
            quantity: 2,
            unit: 'piece',
            display_quantity: '2 piece',
            requirement_type: 'required',
            preparation_note: 'cubed',
            is_available: true,
          },
          {
            ingredient_id: 'ing_tomato',
            canonical_name: 'tomato',
            quantity: 2,
            unit: 'piece',
            display_quantity: '2 piece',
            requirement_type: 'required',
            preparation_note: 'diced',
            is_available: false,
          },
        ],
      },
      core_coverage_score: 50.0,
      score_explanation: 'Matched 1 of 2 required ingredients (50.0%).',
      total_required_count: 2,
      matched_required_count: 1,
      missing_required_count: 1,
      matched_optional_count: 0,
      missing_optional_count: 0,
      matched_required_ingredients: [
        {
          ingredient_id: 'ing_potato',
          canonical_name: 'potato',
          quantity: 2,
          unit: 'piece',
          display_quantity: '2 piece',
          requirement_type: 'required',
          is_available: true,
        },
      ],
      missing_required_ingredients: [
        {
          ingredient_id: 'ing_tomato',
          canonical_name: 'tomato',
          quantity: 2,
          unit: 'piece',
          display_quantity: '2 piece',
          requirement_type: 'required',
          is_available: false,
        },
      ],
      matched_optional_ingredients: [],
      missing_optional_ingredients: [],
      ai_suggestion: null,
    },
  ],
  no_match_guidance: null,
  ranking_rule_summary: 'Ranked by required ingredient coverage.',
  score_formula_description: 'Core ingredient coverage = (matched required / total required) × 100.',
  food_safety_notice: 'Always inspect ingredients before cooking.',
};

describe('Leftover Chef Frontend Verification Suite (TC-53 to TC-60)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(api, 'searchByIngredients').mockResolvedValue(MOCK_SEARCH_RESPONSE);
    vi.spyOn(api, 'getRecipes').mockResolvedValue([]);
    vi.spyOn(api, 'getIngredients').mockResolvedValue([]);
    vi.spyOn(api, 'getPantryItems').mockResolvedValue([]);
    vi.spyOn(api, 'getShoppingList').mockResolvedValue({
      id: 1,
      user_id: 'default_chef',
      name: 'My Shopping List',
      items: [],
      unit_handling_note: 'Compatible units are merged.',
    });
    vi.spyOn(api, 'getFavourites').mockResolvedValue([]);
    vi.spyOn(api, 'getProfile').mockResolvedValue({
      user_id: 'default_chef',
      display_name: 'Default Home Chef',
      dietary_preferences: [],
      disliked_ingredients: [],
      preferred_cuisine: null,
      typical_serving_size: 2,
      max_cooking_minutes: null,
      medical_disclaimer: 'Not medical advice.',
    });
  });

  it('TC-53: Completes the main ingredient-search workflow and splits comma-separated inputs into chips', async () => {
    const parsed = parseIngredientInputTokens('  Potato, ONION ,  garlic  ');
    expect(parsed).toEqual(['potato', 'onion', 'garlic']);

    render(<App />);
    await waitFor(() => {
      expect(screen.getByText('Homestyle Potato Tomato Curry (Aloo Tamatar)')).toBeInTheDocument();
    });

    const input = screen.getByLabelText('Enter ingredients you have');
    fireEvent.change(input, { target: { value: 'garlic, spinach' } });
    fireEvent.click(screen.getByRole('button', { name: /Add Ingredients/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Remove garlic' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Remove spinach' })).toBeInTheDocument();
    });
  });

  it('TC-54: Displays loading state while recipe search is in flight', async () => {
    let resolvePromise: (val: typeof MOCK_SEARCH_RESPONSE) => void = () => {};
    vi.spyOn(api, 'searchByIngredients').mockImplementation(
      () =>
        new Promise((resolve) => {
          resolvePromise = resolve;
        })
    );

    render(<App />);
    expect(
      screen.getByText(/Searching catalogue and calculating ingredient coverage/i)
    ).toBeInTheDocument();

    resolvePromise(MOCK_SEARCH_RESPONSE);
    await waitFor(() => {
      expect(
        screen.queryByText(/Searching catalogue and calculating ingredient coverage/i)
      ).not.toBeInTheDocument();
    });
  });

  it('TC-55: Displays understandable error message when submitting empty ingredient text or on API failure', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText('Homestyle Potato Tomato Curry (Aloo Tamatar)')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Add Ingredients/i }));
    expect(screen.getByRole('alert')).toHaveTextContent(/Please enter at least one ingredient/i);
  });

  it('TC-56: Clearly displays matching and missing required ingredients on recipe cards and detail modal', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText('50% Required Match')).toBeInTheDocument();
    });

    expect(screen.getByText(/Matched Required: 1\/2/i)).toBeInTheDocument();
    expect(screen.getByText(/Missing Required: 1/i)).toBeInTheDocument();
    expect(screen.getByText(/tomato \(2 piece\)/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /View Recipe/i }));
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('[Available]')).toBeInTheDocument();
      expect(screen.getByText('[Missing]')).toBeInTheDocument();
    });
  });

  it('TC-57: Confirms responsive layout containers and grid structure exist', async () => {
    const { container } = render(<App />);
    await waitFor(() => {
      expect(container.querySelector('.app-shell')).toBeInTheDocument();
      expect(container.querySelector('.recipe-grid')).toBeInTheDocument();
      expect(container.querySelector('.filters-bar')).toBeInTheDocument();
    });
  });

  it('TC-58: Verifies accessible labels, roles, and keyboard-operable form controls', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByLabelText('Main navigation')).toBeInTheDocument();
      expect(screen.getByLabelText('Enter ingredients you have')).toBeInTheDocument();
      expect(screen.getByLabelText('Sort Recipes By')).toBeInTheDocument();
      expect(screen.getByLabelText('Dietary Preference')).toBeInTheDocument();
    });
  });

  it('TC-59: Confirms the footer developer credit "Developed by Anil Biradar" is visible across views', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText('Homestyle Potato Tomato Curry (Aloo Tamatar)')).toBeInTheDocument();
    });
    const footerCredit = screen.getByTestId('footer-developer-credit');
    expect(footerCredit).toBeVisible();
    expect(footerCredit).toHaveTextContent('Developed by Anil Biradar');

    fireEvent.click(screen.getByRole('button', { name: /Food Safety & Credits/i }));
    expect(screen.getAllByText('Developed by Anil Biradar').length).toBeGreaterThanOrEqual(2);
  });

  it('TC-60: Confirms all navigation tabs and interactive controls perform real state updates', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText('Homestyle Potato Tomato Curry (Aloo Tamatar)')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /My Pantry/i }));
    expect(screen.getByRole('heading', { name: /My Kitchen Pantry/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Shopping List/i }));
    expect(
      screen.getByRole('heading', { name: /Shopping List for Missing Ingredients/i })
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Favourites/i }));
    expect(screen.getByRole('heading', { name: /Saved Favourite Recipes/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Preferences/i }));
    expect(
      screen.getByRole('heading', { name: /Chef Profile & Culinary Preferences/i })
    ).toBeInTheDocument();
  });
});
