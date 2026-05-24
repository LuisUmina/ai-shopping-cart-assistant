import math
import re
from dataclasses import dataclass

from app.models.common import QuantityUnit

# Spanish → canonical unit
_UNIT_ALIASES: dict[str, QuantityUnit] = {
    # mass
    "kg": QuantityUnit.KG, "kilo": QuantityUnit.KG, "kilos": QuantityUnit.KG,
    "kilogramo": QuantityUnit.KG, "kilogramos": QuantityUnit.KG,
    "g": QuantityUnit.G, "gr": QuantityUnit.G, "grs": QuantityUnit.G,
    "gramo": QuantityUnit.G, "gramos": QuantityUnit.G,
    # volume
    "l": QuantityUnit.L, "lt": QuantityUnit.L, "lts": QuantityUnit.L,
    "litro": QuantityUnit.L, "litros": QuantityUnit.L,
    "ml": QuantityUnit.ML, "mililitro": QuantityUnit.ML, "mililitros": QuantityUnit.ML,
    "cc": QuantityUnit.ML,
    # count
    "unit": QuantityUnit.UNIT, "und": QuantityUnit.UNIT, "un": QuantityUnit.UNIT,
    "unidad": QuantityUnit.UNIT, "unidades": QuantityUnit.UNIT,
    # presentation types that imply count
    "pack": QuantityUnit.PACK, "paquete": QuantityUnit.PACK, "paquetes": QuantityUnit.PACK,
    "rollo": QuantityUnit.ROLL, "rollos": QuantityUnit.ROLL,
    "bolsa": QuantityUnit.BAG, "bolsas": QuantityUnit.BAG,
    "caja": QuantityUnit.BOX, "cajas": QuantityUnit.BOX,
}

# Promotion patterns — should not be parsed as quantity+unit
_PROMOTION_RE = re.compile(r"\b\d+\s*[xX]\s*\d+\b")

# Main quantity pattern: optional connector, number, optional unit
_QUANTITY_RE = re.compile(
    r"""
    (?:x\s*)?                                          # optional "x " prefix
    (\d+(?:[.,]\d+)?)                                  # numeric value
    \s*                                                # optional space
    (kg|kilo[s]?|kilogramo[s]?|g|gr[s]?|gramo[s]?     # mass units
    |ml|cc|mililitro[s]?                               # volume ml
    |l(?:t[s]?)?|litro[s]?                             # volume l
    |unidades?|und?|pack|paquetes?|rollo[s]?           # count
    |bolsas?|cajas?)\b                                 # bag/box
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Pattern for "x N" without explicit unit (e.g. "Pack x 6")
_COUNT_X_RE = re.compile(r"\bx\s*(\d+)\b", re.IGNORECASE)


@dataclass
class ParsedQuantity:
    value: float | None
    unit: QuantityUnit | None
    raw: str = ""
    ambiguous: bool = False
    is_promotion: bool = False


# ── Normalization ─────────────────────────────────────────────────────────────

def normalize_quantity(value: float, unit: QuantityUnit) -> tuple[float, QuantityUnit]:
    """Convert g→kg and ml→l. Other units pass through unchanged."""
    if unit == QuantityUnit.G:
        return round(value / 1000, 6), QuantityUnit.KG
    if unit == QuantityUnit.ML:
        return round(value / 1000, 6), QuantityUnit.L
    return value, unit


def to_base_value(value: float, unit: QuantityUnit) -> float:
    """Convert to base unit for arithmetic comparison (g for mass, ml for volume)."""
    if unit == QuantityUnit.KG:
        return value * 1000
    if unit == QuantityUnit.L:
        return value * 1000
    return value  # g, ml, unit, pack, roll, bag, box already base


def are_compatible(unit_a: QuantityUnit, unit_b: QuantityUnit) -> bool:
    """Return True when both units measure the same dimension."""
    mass = {QuantityUnit.G, QuantityUnit.KG}
    volume = {QuantityUnit.ML, QuantityUnit.L}
    count = {QuantityUnit.UNIT, QuantityUnit.PACK, QuantityUnit.ROLL,
             QuantityUnit.BAG, QuantityUnit.BOX}
    for group in (mass, volume, count):
        if unit_a in group and unit_b in group:
            return True
    return False


# ── Required-units calculation (FR-009) ──────────────────────────────────────

def calculate_required_units(
    requested_value: float,
    requested_unit: QuantityUnit,
    product_value: float,
    product_unit: QuantityUnit,
) -> tuple[int, float, float] | None:
    """
    Return (required_units, effective_quantity_in_product_unit, excess_in_product_unit).
    Returns None when units are incompatible dimensions.
    """
    if not are_compatible(requested_unit, product_unit):
        return None
    req_base = to_base_value(requested_value, requested_unit)
    prod_base = to_base_value(product_value, product_unit)
    if prod_base == 0:
        return None
    required = math.ceil(req_base / prod_base)
    effective_base = required * prod_base
    excess_base = effective_base - req_base
    # Return effective/excess in the same base unit
    return required, effective_base, excess_base


# ── Parsing ───────────────────────────────────────────────────────────────────

def parse_quantity(raw: str) -> ParsedQuantity:
    """
    Extract quantity and unit from a product title or presentation string.

    Ambiguous cases are flagged; promotion patterns (2x1) set is_promotion=True.
    """
    if not raw or not raw.strip():
        return ParsedQuantity(value=None, unit=None, raw=raw)

    # Flag promotions like "2x1", "3x2" — do not attempt to parse further
    if _PROMOTION_RE.search(raw):
        return ParsedQuantity(value=None, unit=None, raw=raw, is_promotion=True)

    matches = _QUANTITY_RE.findall(raw)

    if matches:
        raw_value, raw_unit = matches[0]
        value = float(raw_value.replace(",", "."))
        unit = _UNIT_ALIASES.get(raw_unit.lower())
        if unit is None:
            return ParsedQuantity(value=None, unit=None, raw=raw, ambiguous=True)
        norm_value, norm_unit = normalize_quantity(value, unit)
        return ParsedQuantity(
            value=norm_value,
            unit=norm_unit,
            raw=raw,
            ambiguous=len(matches) > 1,
        )

    # Fallback: "x 6" pattern implying count
    count_match = _COUNT_X_RE.search(raw)
    if count_match:
        return ParsedQuantity(
            value=float(count_match.group(1)),
            unit=QuantityUnit.UNIT,
            raw=raw,
        )

    return ParsedQuantity(value=None, unit=None, raw=raw)
