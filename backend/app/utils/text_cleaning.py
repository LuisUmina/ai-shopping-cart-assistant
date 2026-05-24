import re
import unicodedata


def normalize_whitespace(text: str) -> str:
    """Collapse multiple spaces/tabs/newlines into a single space."""
    return re.sub(r"\s+", " ", text).strip()


def remove_accents(text: str) -> str:
    """Strip diacritics: 'Costeño' → 'Costeno'."""
    nfd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def normalize_for_comparison(text: str) -> str:
    """Lowercase + remove accents + collapse whitespace. For fuzzy matching."""
    return normalize_whitespace(remove_accents(text.lower()))


def clean_title(text: str) -> str:
    """
    Light clean for product titles: normalize whitespace and strip
    leading/trailing punctuation. Preserves case and accents.
    """
    text = normalize_whitespace(text)
    text = text.strip(".,;:-")
    return text


def tokenize(text: str) -> list[str]:
    """Split text into lowercase, accent-free word tokens."""
    cleaned = normalize_for_comparison(text)
    return [t for t in re.split(r"[\s\-/|]+", cleaned) if t]
