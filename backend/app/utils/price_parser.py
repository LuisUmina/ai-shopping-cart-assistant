import re
from dataclasses import dataclass, field

# Matches: S/ 24.90  S/. 24.90  S/.24.90  24.90  S/ 1,299.00  24,90
_PRICE_RE = re.compile(
    r"(?:S/\.?\s*|PEN\s*)?"          # optional currency prefix
    r"(\d{1,3}(?:[.,]\d{3})*"        # integer part (with optional thousand sep)
    r"(?:[.,]\d{1,2})?)",            # optional decimal (1-2 digits)
    re.IGNORECASE,
)


@dataclass
class ParsedPrice:
    value: float | None
    currency: str = "PEN"
    raw: str = ""
    ambiguous: bool = False


def _normalize_numeric(s: str) -> float | None:
    """Convert a raw numeric string with mixed separators to float."""
    s = s.strip()
    if not s:
        return None

    # "1,299.00" — comma=thousands, dot=decimal  → strip commas
    if re.search(r"\d,\d{3}", s):
        s = s.replace(",", "")
    # "24,90" — comma=decimal (no dot present) → swap
    elif "," in s and "." not in s:
        s = s.replace(",", ".")

    try:
        return float(s)
    except ValueError:
        return None


def parse_price(raw: str) -> ParsedPrice:
    """
    Extract a float price from a raw price string.

    Returns ParsedPrice with value=None when no price can be extracted.
    Sets ambiguous=True when multiple candidates are found.
    """
    if not raw or not raw.strip():
        return ParsedPrice(value=None, raw=raw)

    matches = _PRICE_RE.findall(raw)
    # Filter empty strings from regex optional groups
    candidates = [m for m in matches if m]

    if not candidates:
        return ParsedPrice(value=None, raw=raw)

    value = _normalize_numeric(candidates[0])
    ambiguous = len(candidates) > 1

    return ParsedPrice(value=value, currency="PEN", raw=raw, ambiguous=ambiguous)
