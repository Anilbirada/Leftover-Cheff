"""
Optional AI / Smart Culinary Explanation Assistant.

Follows Section 9 rules strictly:
- The core application works 100% without external AI APIs.
- Never used for deterministic ingredient matching.
- Never invents catalogue items, nutrition facts, or allergen-safety claims.
- Every suggestion is explicitly marked as `is_ai_generated=True` and `verification_status="unverified_suggestion"`.
- Handles unavailable external providers gracefully with deterministic fallback explanations.
"""
from dataclasses import dataclass
from typing import List, Optional

from app.core.config import settings
from app.services.matcher import MatchedRecipeResult


@dataclass(frozen=True)
class CulinarySuggestionOutput:
    label: str
    explanation: str
    cooking_tip: str
    is_ai_generated: bool
    verification_status: str
    safety_disclaimer: str
    provider_status: str


SAFETY_DISCLAIMER = (
    "Suggestion only — not a verified recipe or allergen safety guarantee. "
    "Always verify ingredient labels for allergens and inspect food condition before cooking."
)


def generate_recipe_match_explanation(
    match: MatchedRecipeResult,
    simulate_provider_failure: bool = False,
) -> CulinarySuggestionOutput:
    """
    Generate a transparent explanation of why a recipe matches the user's ingredients
    and how to approach cooking it. Gracefully falls back when external AI is disabled or unavailable.
    """
    matched_names = [i.canonical_name for i in match.matched_required_ingredients]
    missing_names = [i.canonical_name for i in match.missing_required_ingredients]

    if simulate_provider_failure or (settings.enable_optional_ai and not settings.ai_provider_api_key):
        provider_status = "fallback_deterministic_provider_unavailable"
    elif settings.enable_optional_ai and settings.ai_provider_api_key:
        provider_status = "configured_safe_assistant"
    else:
        provider_status = "local_deterministic_assistant"

    if not missing_names:
        explanation = (
            f"You have all {match.total_required_count} required ingredients for {match.recipe.name} "
            f"({', '.join(matched_names)})."
        )
        tip = (
            f"Prep time is {match.recipe.preparation_minutes} mins and cooking takes "
            f"{match.recipe.cooking_minutes} mins. Read all steps through before heating the pan."
        )
    else:
        explanation = (
            f"Your pantry covers {match.core_coverage_score}% of the required ingredients for {match.recipe.name} "
            f"(matched: {', '.join(matched_names) if matched_names else 'none'}). "
            f"You will need {len(missing_names)} additional required item(s): {', '.join(missing_names)}."
        )
        tip = (
            "Add the missing required ingredients to your shopping list before starting, "
            "as substituting core ingredients may alter cooking times, texture, or allergen safety."
        )

    return CulinarySuggestionOutput(
        label="AI / Smart Culinary Suggestion (Unverified)",
        explanation=explanation,
        cooking_tip=tip,
        is_ai_generated=True,
        verification_status="unverified_suggestion",
        safety_disclaimer=SAFETY_DISCLAIMER,
        provider_status=provider_status,
    )
