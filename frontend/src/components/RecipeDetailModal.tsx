import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Heart,
  Minus,
  Plus,
  ShieldAlert,
  ShoppingCart,
  Users,
  X,
} from 'lucide-react';
import type { RecipeDetailOut, RecipeIngredientOut, ScaledIngredientOut } from '../types/api';
import { api } from '../services/api';
import { RecipeIllustration } from './RecipeIllustration';

interface Props {
  recipe: RecipeDetailOut;
  isFavourite: boolean;
  onToggleFavourite: (recipeId: string) => void;
  onAddMissingToShoppingList: (recipeId: string, items: RecipeIngredientOut[]) => Promise<void>;
  onClose: () => void;
}

export const RecipeDetailModal: React.FC<Props> = ({
  recipe,
  isFavourite,
  onToggleFavourite,
  onAddMissingToShoppingList,
  onClose,
}) => {
  const [servings, setServings] = useState<number>(recipe.default_servings);
  const [scaledMap, setScaledMap] = useState<Record<string, ScaledIngredientOut>>({});
  const [scalingError, setScalingError] = useState<string | null>(null);
  const [addingToCart, setAddingToCart] = useState(false);
  const [addedFeedback, setAddedFeedback] = useState<string | null>(null);

  useEffect(() => {
    setServings(recipe.default_servings);
    setScaledMap({});
    setScalingError(null);
    setAddedFeedback(null);
  }, [recipe]);

  const handleAdjustServings = async (nextServings: number) => {
    if (nextServings < 1 || nextServings > 50) return;
    setServings(nextServings);
    setScalingError(null);

    if (nextServings === recipe.default_servings) {
      setScaledMap({});
      return;
    }

    try {
      const response = await api.scaleRecipeServings(recipe.id, nextServings);
      const map: Record<string, ScaledIngredientOut> = {};
      for (const item of response.ingredients) {
        map[item.ingredient_id] = item;
      }
      setScaledMap(map);
    } catch (err) {
      setScalingError(err instanceof Error ? err.message : 'Unable to scale servings.');
    }
  };

  const requiredIngredients = recipe.ingredients.filter((i) => i.requirement_type === 'required');
  const optionalIngredients = recipe.ingredients.filter((i) => i.requirement_type !== 'required');
  const missingRequired = requiredIngredients.filter((i) => i.is_available === false);

  const handleAddMissing = async () => {
    const itemsToAdd = missingRequired.length > 0 ? missingRequired : requiredIngredients;
    const scaledItems = itemsToAdd.map((item) => {
      const scaled = scaledMap[item.ingredient_id];
      return {
        ...item,
        quantity: scaled ? scaled.adjusted_quantity : item.quantity,
        display_quantity: scaled ? scaled.display_quantity : item.display_quantity,
      };
    });
    setAddingToCart(true);
    try {
      await onAddMissingToShoppingList(recipe.id, scaledItems);
      setAddedFeedback(`Added ${scaledItems.length} ingredient(s) to Shopping List.`);
    } finally {
      setAddingToCart(false);
    }
  };

  const getDisplayQty = (item: RecipeIngredientOut) => {
    const scaled = scaledMap[item.ingredient_id];
    return scaled ? scaled.display_quantity : item.display_quantity;
  };

  return (
    <div
      className="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="recipe-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="modal-card">
        <div className="modal-header">
          <div>
            <span className="badge-tag" style={{ marginBottom: '0.35rem' }}>
              {recipe.cuisine || 'Home Kitchen'} &bull; {recipe.difficulty}
            </span>
            <h2 id="recipe-modal-title" style={{ fontSize: '1.4rem', fontWeight: 800 }}>
              {recipe.name}
            </h2>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              type="button"
              className="btn btn-outline btn-sm"
              onClick={() => onToggleFavourite(recipe.id)}
              aria-label={isFavourite ? 'Remove from favourites' : 'Save to favourites'}
            >
              <Heart
                size={16}
                fill={isFavourite ? '#a62626' : 'none'}
                color={isFavourite ? '#a62626' : 'currentColor'}
              />
              {isFavourite ? 'Saved' : 'Save'}
            </button>
            <button
              type="button"
              className="btn btn-outline btn-sm"
              onClick={onClose}
              aria-label="Close recipe details"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        <div className="modal-body">
          <div style={{ height: '190px', borderRadius: '12px', overflow: 'hidden', marginBottom: '1.1rem' }}>
            <RecipeIllustration recipeId={recipe.id} cuisine={recipe.cuisine} title={recipe.name} />
          </div>

          <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>{recipe.description}</p>

          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '1rem',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0.85rem 1rem',
              backgroundColor: 'var(--bg-cream)',
              borderRadius: '8px',
              marginBottom: '1.25rem',
            }}
          >
            <div style={{ display: 'flex', gap: '1.25rem', flexWrap: 'wrap', fontSize: '0.88rem' }}>
              <span className="meta-item">
                <Clock size={16} /> Prep: <strong>{recipe.preparation_minutes} min</strong>
              </span>
              <span className="meta-item">
                <Clock size={16} /> Cook: <strong>{recipe.cooking_minutes} min</strong>
              </span>
              <span className="meta-item">
                Total: <strong>{recipe.total_minutes} min</strong>
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Users size={16} />
              <span style={{ fontSize: '0.86rem', fontWeight: 600 }}>Servings:</span>
              <button
                type="button"
                className="btn btn-outline btn-sm"
                onClick={() => handleAdjustServings(servings - 1)}
                disabled={servings <= 1}
                aria-label="Decrease servings"
              >
                <Minus size={14} />
              </button>
              <span
                data-testid="serving-count-value"
                style={{ fontWeight: 800, minWidth: '1.75rem', textAlign: 'center' }}
              >
                {servings}
              </span>
              <button
                type="button"
                className="btn btn-outline btn-sm"
                onClick={() => handleAdjustServings(servings + 1)}
                disabled={servings >= 50}
                aria-label="Increase servings"
              >
                <Plus size={14} />
              </button>
            </div>
          </div>

          {scalingError && <div className="notice-banner notice-danger">{scalingError}</div>}
          {addedFeedback && <div className="notice-banner">{addedFeedback}</div>}

          {/* Allergen & Food Safety Precautions */}
          <div className="notice-banner notice-warn" role="note" aria-label="Allergen and food safety information">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', fontWeight: 700, marginBottom: '0.25rem' }}>
              <ShieldAlert size={16} /> Allergen &amp; Food Safety Precautions
            </div>
            <div>{recipe.allergen_verification_notice}</div>
            <div style={{ marginTop: '0.25rem', fontSize: '0.8rem' }}>{recipe.food_safety_notice}</div>
          </div>

          {/* Ingredients Columns */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '1.25rem',
              marginBottom: '1.5rem',
            }}
          >
            <div className="panel-card" style={{ marginBottom: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '1.02rem', fontWeight: 700 }}>
                  Required Ingredients ({requiredIngredients.length})
                </h3>
                <button
                  type="button"
                  className="btn btn-amber btn-sm"
                  onClick={handleAddMissing}
                  disabled={addingToCart}
                >
                  <ShoppingCart size={14} />
                  {missingRequired.length > 0
                    ? `Add ${missingRequired.length} Missing to List`
                    : 'Add Required to List'}
                </button>
              </div>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {requiredIngredients.map((item) => (
                  <li
                    key={item.ingredient_id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '0.45rem 0.6rem',
                      borderRadius: '6px',
                      backgroundColor:
                        item.is_available === true
                          ? 'var(--status-success-bg)'
                          : item.is_available === false
                          ? 'var(--status-warn-bg)'
                          : 'var(--bg-cream)',
                      fontSize: '0.88rem',
                    }}
                  >
                    <span>
                      <strong>{item.canonical_name}</strong>
                      {item.preparation_note ? ` (${item.preparation_note})` : ''}
                      {item.is_available === true && (
                        <span style={{ marginLeft: '0.4rem', color: 'var(--status-success)', fontWeight: 700 }}>
                          [Available]
                        </span>
                      )}
                      {item.is_available === false && (
                        <span style={{ marginLeft: '0.4rem', color: 'var(--status-warn)', fontWeight: 700 }}>
                          [Missing]
                        </span>
                      )}
                    </span>
                    <span style={{ fontWeight: 700 }}>{getDisplayQty(item)}</span>
                  </li>
                ))}
              </ul>
            </div>

            {optionalIngredients.length > 0 && (
              <div className="panel-card" style={{ marginBottom: 0 }}>
                <h3 style={{ fontSize: '1.02rem', fontWeight: 700, marginBottom: '0.75rem' }}>
                  Optional Ingredients ({optionalIngredients.length})
                </h3>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.6rem' }}>
                  Excluded from the required ingredient coverage denominator.
                </p>
                <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {optionalIngredients.map((item) => (
                    <li
                      key={item.ingredient_id}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        padding: '0.45rem 0.6rem',
                        borderRadius: '6px',
                        backgroundColor: 'var(--bg-cream)',
                        fontSize: '0.88rem',
                      }}
                    >
                      <span>
                        {item.canonical_name}
                        {item.preparation_note ? ` (${item.preparation_note})` : ''}
                      </span>
                      <span style={{ fontWeight: 600 }}>{getDisplayQty(item)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Step-by-Step Instructions */}
          <div className="panel-card">
            <h3 style={{ fontSize: '1.08rem', fontWeight: 700, marginBottom: '0.85rem' }}>
              Step-by-Step Cooking Instructions
            </h3>
            <ol style={{ paddingLeft: '1.35rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {recipe.instructions.map((step, idx) => (
                <li key={idx} style={{ fontSize: '0.94rem', color: 'var(--text-primary)' }}>
                  {step}
                </li>
              ))}
            </ol>
          </div>

          {/* Provenance & Licensing */}
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
            <span>Source: {recipe.source_reference}</span>
            <span>Licence: {recipe.licence_reference}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
