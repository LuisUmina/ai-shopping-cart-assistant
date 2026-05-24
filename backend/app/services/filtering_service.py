"""
Pre-filtering engine (FR-008).

Scores product candidates for relevance against a shopping intent item and
user preferences, then returns only the top-N candidates above the threshold.

Relevance formula (weights sum to 1.0):
    score = title_score  * 0.40
          + category_score * 0.25
          + brand_score    * 0.15
          + unit_score     * 0.10
          + avail_score    * 0.10
          - negative_keyword_penalty (0.50 if triggered)
    clamped to [0.0, 1.0]

Products scoring below MIN_RELEVANCE_SCORE (0.55) are rejected.
"""

from app.models.common import Availability, QuantityUnit
from app.models.intent_models import ShoppingIntentItem
from app.models.preference_models import UserPreferences
from app.models.product_models import ProductCandidate
from app.utils.text_cleaning import normalize_for_comparison, tokenize
from app.utils.unit_parser import are_compatible

MIN_RELEVANCE_SCORE: float = 0.55

# Terms that almost always indicate the product is an accessory/container,
# not the food or consumable item itself.
_NEGATIVE_KEYWORDS: frozenset[str] = frozenset([
    "taper", "tapers", "olla", "ollas", "receta", "recetario",
    "libro", "libros", "copa", "copas", "funda", "fundas",
    "accesorio", "accesorios", "utensilio", "utensilios",
    "molde", "moldes", "bandeja", "bandejas", "dispensador",
    "sticker", "horno", "soporte", "gancho", "colgador",
])


class FilteringService:
    """Deterministic pre-filter: score, reject below threshold, cap at top-N."""

    def filter(
        self,
        candidates: list[ProductCandidate],
        intent_item: ShoppingIntentItem,
        preferences: UserPreferences,
    ) -> list[ProductCandidate]:
        """Return top-N relevant candidates, ordered by relevance score."""
        excluded = {normalize_for_comparison(b) for b in preferences.excluded_brands}

        scored: list[tuple[ProductCandidate, float]] = []
        for candidate in candidates:
            # Hard-reject excluded brands before scoring
            if candidate.brand and normalize_for_comparison(candidate.brand) in excluded:
                continue
            s = self.score(candidate, intent_item, preferences)
            if s >= MIN_RELEVANCE_SCORE:
                scored.append((candidate, s))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored[: preferences.max_candidates_per_product]]

    def score(
        self,
        candidate: ProductCandidate,
        intent_item: ShoppingIntentItem,
        preferences: UserPreferences,
    ) -> float:
        """Compute relevance score in [0.0, 1.0] for a single candidate."""
        raw = (
            self._title_score(candidate.title, intent_item.product_query) * 0.40
            + self._category_score(candidate.category, intent_item.product_query) * 0.25
            + self._brand_score(candidate, intent_item, preferences) * 0.15
            + self._unit_score(candidate.quantity_unit, intent_item.unit) * 0.10
            + self._availability_score(candidate.availability) * 0.10
        )
        if _has_negative_keyword(candidate.title):
            raw -= 0.50
        return max(0.0, min(1.0, raw))

    # ── Component scorers ─────────────────────────────────────────────────────

    def _title_score(self, title: str, query: str) -> float:
        """Fraction of query tokens found in the normalized product title."""
        if not title or not query:
            return 0.0
        title_norm = normalize_for_comparison(title)
        query_tokens = tokenize(query)
        if not query_tokens:
            return 0.0
        hits = sum(1 for t in query_tokens if t in title_norm)
        return hits / len(query_tokens)

    def _category_score(self, category: str | None, query: str) -> float:
        """1.0 if a query token is in the category, 0.5 if unknown, 0.0 if miss."""
        if not category:
            return 0.5  # many stores don't return a category — neutral, not a penalty
        cat_norm = normalize_for_comparison(category)
        return 1.0 if any(t in cat_norm for t in tokenize(query)) else 0.0

    def _brand_score(
        self,
        candidate: ProductCandidate,
        intent_item: ShoppingIntentItem,
        preferences: UserPreferences,
    ) -> float:
        """Score brand relevance given intent preference and global preferences."""
        candidate_brand = normalize_for_comparison(candidate.brand or "")

        # Intent-level brand preference (highest priority)
        if intent_item.brand_preference:
            pref = normalize_for_comparison(intent_item.brand_preference)
            if candidate_brand and pref in candidate_brand:
                return 1.0
            # Brand doesn't match — penalize, but allow substitution if permitted
            return 0.3 if intent_item.allow_substitution else 0.0

        # Global preferred brands list
        preferred = {normalize_for_comparison(b) for b in preferences.preferred_brands}
        if preferred and candidate_brand in preferred:
            return 1.0

        # Penalize unknown brands when user wants known brands only
        if preferences.known_brands_only and not candidate_brand:
            return 0.0

        return 0.5  # neutral — no brand preference expressed


    def _unit_score(
        self, product_unit: QuantityUnit, requested_unit: QuantityUnit | None
    ) -> float:
        """1.0 if units are dimension-compatible, 0.5 if no preference, 0.0 if mismatch."""
        if requested_unit is None:
            return 0.5
        return 1.0 if are_compatible(product_unit, requested_unit) else 0.0

    def _availability_score(self, availability: Availability) -> float:
        if availability == Availability.AVAILABLE:
            return 1.0
        if availability == Availability.UNKNOWN:
            return 0.5
        return 0.0


# ── Module-level helper ───────────────────────────────────────────────────────

def _has_negative_keyword(title: str) -> bool:
    """Return True if the title contains any word from the negative keyword list."""
    return bool(set(tokenize(title)) & _NEGATIVE_KEYWORDS)
