from dataclasses import dataclass

from app.utils.text_cleaning import normalize_for_comparison, tokenize

# Curated list of brands commonly found in Peruvian supermarkets.
# Stored normalized (lowercase, no accents) for matching.
_KNOWN_BRANDS: set[str] = {
    # Rice
    "costeno", "paisano", "faraon", "angel", "anali", "premier",
    # Dairy
    "gloria", "nestle", "laive", "pura vida", "milkito", "soy vida",
    # Oil
    "primor", "cil", "ideal", "vivo", "alacena",
    # Detergents
    "ariel", "bolivar", "ace", "surf", "drive", "omo",
    # Toilet paper / tissue
    "elite", "suave", "scott", "paracas", "jumbo",
    # Water / soft drinks
    "san luis", "san mateo", "cielo", "bonaqua",
    "inca kola", "coca cola", "pepsi", "kola real", "sprite", "fanta",
    # Beer
    "cristal", "pilsen", "cusquena", "brahma",
    # Bread / bakery
    "bimbo", "wonder",
    # Poultry
    "san fernando",
    # Canned / pantry
    "florida", "campbells",
    # Sugar / sweetener
    "cartavio", "casa grande",
    # Flour / pasta
    "nicolini", "blanca flor", "don vittorio", "lavaggi",
    # Margarine / spreads
    "manty", "sello de oro", "dorina", "karina",
    # Condiments
    "tari", "maggi",
    # Snacks
    "lays", "cheetos", "doritos", "pringles",
}


@dataclass
class ParsedBrand:
    brand: str | None
    confidence: float  # 0.0–1.0
    raw: str = ""


def extract_brand(title: str) -> ParsedBrand:
    """
    Attempt to extract a brand name from a product title.

    High confidence (0.9) when a known brand is found.
    Low confidence (0.3) when the heuristic picks the first capitalized token.
    Returns confidence 0.0 when nothing can be extracted.
    """
    if not title or not title.strip():
        return ParsedBrand(brand=None, confidence=0.0, raw=title)

    norm_title = normalize_for_comparison(title)

    # Check multi-word known brands first (longer matches win)
    sorted_brands = sorted(_KNOWN_BRANDS, key=len, reverse=True)
    for brand in sorted_brands:
        if brand in norm_title:
            # Return the brand with original casing from title if possible
            display = _find_original_case(title, brand)
            return ParsedBrand(brand=display, confidence=0.9, raw=title)

    # Heuristic: first all-uppercase token or first Title-case word
    tokens = title.split()
    for token in tokens:
        clean = token.strip(".,;:()")
        if len(clean) >= 2 and (clean.isupper() or clean[0].isupper()):
            return ParsedBrand(brand=clean, confidence=0.3, raw=title)

    return ParsedBrand(brand=None, confidence=0.0, raw=title)


def _find_original_case(title: str, normalized_brand: str) -> str:
    """Return the substring from title that matches normalized_brand."""
    norm_title = normalize_for_comparison(title)
    idx = norm_title.find(normalized_brand)
    if idx == -1:
        return normalized_brand.title()
    return title[idx: idx + len(normalized_brand)]
