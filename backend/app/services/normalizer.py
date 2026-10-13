"""
Ingredient Normalisation Pipeline.

Responsibilities:
- Parse single or comma-separated ingredient strings.
- Lowercase, strip punctuation, and collapse repeated whitespace.
- Deduplicate ingredients while preserving entry order.
- Resolve against explicit canonical names and approved aliases.
- Apply controlled plural-to-singular resolution without merging distinct culinary or allergen items
  (e.g., milk vs coconut milk, butter vs margarine, wheat flour vs rice flour,
   onion vs spring onion, fresh chilli vs chilli powder, peanuts vs tree nuts).
"""
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.entities import Ingredient, IngredientAlias


PUNCTUATION_RE = re.compile(r"[^\w\s-]", re.UNICODE)
WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class NormalisedIngredientResult:
    raw_input: str
    normalised_input: str
    ingredient_id: Optional[str]
    canonical_name: str
    category: Optional[str]
    is_recognised: bool
    resolution_method: str  # "canonical", "alias", "plural_rule", "unrecognised"


def clean_ingredient_token(raw: str) -> str:
    """Normalise case, punctuation, and whitespace for a single ingredient phrase."""
    lowered = raw.lower().strip()
    # Replace hyphens with spaces for consistent token comparison
    dehyphenated = lowered.replace("-", " ")
    no_punct = PUNCTUATION_RE.sub(" ", dehyphenated)
    collapsed = WHITESPACE_RE.sub(" ", no_punct).strip()
    return collapsed


def ControlledSingularCandidates(normalised: str) -> List[str]:
    """
    Generate safe singular form candidates for common English plurals.
    Does not strip modifiers (so 'spring onions' -> 'spring onion', never 'onion').
    """
    candidates: List[str] = []
    if len(normalised) <= 3:
        return candidates
    if normalised.endswith("oes") and len(normalised) > 4:
        # potatoes -> potato, tomatoes -> tomato
        candidates.append(normalised[:-2])
    if normalised.endswith("ies") and len(normalised) > 4:
        # chillies -> chilli, berries -> berry
        candidates.append(normalised[:-3] + "y")
        candidates.append(normalised[:-3] + "i")
    if normalised.endswith("ves") and len(normalised) > 4:
        # leaves -> leaf, halves -> half
        candidates.append(normalised[:-3] + "f")
        candidates.append(normalised[:-3] + "fe")
    if normalised.endswith("es") and len(normalised) > 3:
        candidates.append(normalised[:-2])
    if normalised.endswith("s") and not normalised.endswith("ss"):
        candidates.append(normalised[:-1])
    return candidates


def parse_raw_ingredient_inputs(raw_inputs: Iterable[str]) -> List[str]:
    """
    Expand comma/semicolon/newline-separated entries into individual raw tokens.
    Enforces input length limits.
    """
    tokens: List[str] = []
    total_chars = 0
    for item in raw_inputs:
        if item is None:
            continue
        text = str(item)
        total_chars += len(text)
        if total_chars > settings.max_ingredient_input_chars:
            raise ValueError(
                f"Ingredient input exceeds maximum allowed length of {settings.max_ingredient_input_chars} characters."
            )
        # Split on comma, semicolon, or newline
        parts = re.split(r"[,;\n]+", text)
        for part in parts:
            stripped = part.strip()
            if stripped:
                if len(stripped) > 120:
                    raise ValueError("Individual ingredient name cannot exceed 120 characters.")
                tokens.append(stripped)

    if len(tokens) > settings.max_ingredients_per_search:
        raise ValueError(
            f"Too many ingredients submitted (max {settings.max_ingredients_per_search})."
        )
    return tokens


def build_lookup_maps(
    db: Session,
) -> Tuple[Dict[str, Ingredient], Dict[str, Tuple[Ingredient, str]]]:
    """
    Build in-memory lookup dictionaries from active database ingredients and aliases.
    Returns (canonical_map, alias_map).
    """
    ingredients = db.query(Ingredient).filter(Ingredient.active.is_(True)).all()
    aliases = db.query(IngredientAlias).all()

    ing_by_id: Dict[str, Ingredient] = {ing.id: ing for ing in ingredients}
    canonical_map: Dict[str, Ingredient] = {}
    for ing in ingredients:
        canonical_map[clean_ingredient_token(ing.canonical_name)] = ing

    alias_map: Dict[str, Tuple[Ingredient, str]] = {}
    for al in aliases:
        target = ing_by_id.get(al.ingredient_id)
        if target:
            alias_map[clean_ingredient_token(al.normalised_alias)] = (target, al.alias)

    return canonical_map, alias_map


def normalise_ingredients(
    db: Session,
    raw_inputs: Iterable[str],
) -> List[NormalisedIngredientResult]:
    """
    Normalise, deduplicate, and resolve a sequence of user-entered ingredient strings.
    """
    expanded_tokens = parse_raw_ingredient_inputs(raw_inputs)
    if not expanded_tokens:
        return []

    canonical_map, alias_map = build_lookup_maps(db)

    results: List[NormalisedIngredientResult] = []
    seen_keys: set[str] = set()

    for raw_token in expanded_tokens:
        cleaned = clean_ingredient_token(raw_token)
        if not cleaned:
            continue

        matched_ing: Optional[Ingredient] = None
        method = "unrecognised"

        # 1. Exact canonical match
        if cleaned in canonical_map:
            matched_ing = canonical_map[cleaned]
            method = "canonical"
        # 2. Explicit approved alias match
        elif cleaned in alias_map:
            matched_ing = alias_map[cleaned][0]
            method = "alias"
        else:
            # 3. Controlled singularization candidates
            for candidate in ControlledSingularCandidates(cleaned):
                if candidate in canonical_map:
                    matched_ing = canonical_map[candidate]
                    method = "plural_rule"
                    break
                if candidate in alias_map:
                    matched_ing = alias_map[candidate][0]
                    method = "plural_rule"
                    break

        dedup_key = matched_ing.id if matched_ing else f"unrecognised:{cleaned}"
        if dedup_key in seen_keys:
            continue
        seen_keys.add(dedup_key)

        if matched_ing:
            results.append(
                NormalisedIngredientResult(
                    raw_input=raw_token,
                    normalised_input=cleaned,
                    ingredient_id=matched_ing.id,
                    canonical_name=matched_ing.canonical_name,
                    category=matched_ing.category,
                    is_recognised=True,
                    resolution_method=method,
                )
            )
        else:
            results.append(
                NormalisedIngredientResult(
                    raw_input=raw_token,
                    normalised_input=cleaned,
                    ingredient_id=None,
                    canonical_name=cleaned,
                    category=None,
                    is_recognised=False,
                    resolution_method="unrecognised",
                )
            )

    return results
