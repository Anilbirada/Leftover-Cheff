"""
Serving Size and Quantity Calculation Service.

Responsibilities:
- Scale numeric ingredient quantities reliably:
  adjusted_quantity = original_quantity * requested_servings / original_servings
- Preserve qualitative quantities (e.g., 'to taste', None) without inventing numbers.
- Format numbers cleanly (e.g., 2.0 -> 2, 0.3333 -> 0.33).
- Support compatible unit aggregation (g <-> kg, ml <-> litre) for shopping lists while
  refusing unsafe mass-to-volume conversions without density data.
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple


SUPPORTED_UNITS = {
    "g": ("mass", 1.0),
    "kg": ("mass", 1000.0),
    "ml": ("volume", 1.0),
    "litre": ("volume", 1000.0),
    "l": ("volume", 1000.0),
    "teaspoon": ("spoon_volume", 1.0),
    "tablespoon": ("spoon_volume", 3.0),
    "cup": ("cup_volume", 1.0),
    "piece": ("count", 1.0),
    "to taste": ("qualitative", 0.0),
}


@dataclass(frozen=True)
class ScaledIngredientItem:
    ingredient_id: str
    canonical_name: str
    original_quantity: Optional[float]
    adjusted_quantity: Optional[float]
    display_quantity: str
    unit: str
    requirement_type: str
    preparation_note: Optional[str]


def validate_serving_count(servings: int) -> int:
    """Validate that a requested serving count is a positive integer within reasonable bounds."""
    if not isinstance(servings, int) or isinstance(servings, bool):
        raise ValueError("Serving count must be an integer.")
    if servings < 1 or servings > 50:
        raise ValueError("Serving count must be between 1 and 50.")
    return servings


def round_quantity(value: float) -> float:
    """Round scaled quantity to at most 2 decimal places, preserving clean integers and eighths."""
    rounded_3 = round(value, 3)
    if rounded_3 in (0.125, 0.375, 0.625, 0.875):
        return rounded_3
    rounded_2 = round(value, 2)
    if rounded_2.is_integer():
        return float(int(rounded_2))
    return rounded_2


def format_quantity_display(quantity: Optional[float], unit: str) -> str:
    """Format a quantity and unit for human-readable culinary display."""
    if quantity is None or unit.strip().lower() == "to taste":
        return unit.strip() or "to taste"
    q = round_quantity(quantity)
    if q.is_integer():
        q_str = str(int(q))
    else:
        q_str = f"{q:g}"
    return f"{q_str} {unit}".strip()


def scale_single_quantity(
    original_quantity: Optional[float],
    unit: str,
    original_servings: int,
    requested_servings: int,
) -> Tuple[Optional[float], str]:
    """
    Calculate the adjusted quantity for a single recipe ingredient without mutating original data.
    Qualitative quantities (None or 'to taste') remain None.
    """
    validate_serving_count(original_servings)
    validate_serving_count(requested_servings)

    if original_quantity is None or unit.strip().lower() == "to taste":
        return None, format_quantity_display(None, unit)

    raw_adjusted = (float(original_quantity) * float(requested_servings)) / float(original_servings)
    adjusted = round_quantity(raw_adjusted)
    return adjusted, format_quantity_display(adjusted, unit)


def can_combine_units(unit_a: str, unit_b: str) -> bool:
    """
    Check if two units can be safely combined without ingredient-specific density data.
    Mass-to-volume conversions (e.g. g to ml or cup) are explicitly forbidden.
    """
    ua = unit_a.strip().lower()
    ub = unit_b.strip().lower()
    if ua == ub:
        return True
    info_a = SUPPORTED_UNITS.get(ua)
    info_b = SUPPORTED_UNITS.get(ub)
    if not info_a or not info_b:
        return False
    if info_a[0] == "qualitative" or info_b[0] == "qualitative":
        return False
    return info_a[0] == info_b[0]


def combine_compatible_quantities(
    qty_a: Optional[float],
    unit_a: str,
    qty_b: Optional[float],
    unit_b: str,
) -> Tuple[Optional[float], str]:
    """
    Combine two quantities if and only if their units are compatible.
    Raises ValueError if attempting to convert incompatible dimensions (e.g. mass to volume).
    """
    ua = unit_a.strip().lower()
    ub = unit_b.strip().lower()

    if not can_combine_units(ua, ub):
        raise ValueError(
            f"Cannot safely convert or combine '{unit_a}' and '{unit_b}' without ingredient density data."
        )

    if qty_a is None or qty_b is None or ua == "to taste":
        return None, unit_a

    if ua == ub:
        return round_quantity(qty_a + qty_b), unit_a

    dim_a, factor_a = SUPPORTED_UNITS[ua]
    _, factor_b = SUPPORTED_UNITS[ub]
    base_total = (qty_a * factor_a) + (qty_b * factor_b)

    # Return in base unit (g, ml, teaspoon) unless neatly divisible in larger unit
    if dim_a == "mass":
        if base_total >= 1000:
            return round_quantity(base_total / 1000.0), "kg"
        return round_quantity(base_total), "g"
    if dim_a == "volume":
        if base_total >= 1000:
            return round_quantity(base_total / 1000.0), "litre"
        return round_quantity(base_total), "ml"
    if dim_a == "spoon_volume":
        return round_quantity(base_total), "teaspoon"

    return round_quantity(base_total), unit_a
