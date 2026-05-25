"""
Ranking engine (FR-010).

Scores pre-filtered candidates with a weighted formula and returns them
sorted best-first.  Weights adjust automatically based on user priorities.

Base formula (weights sum to 1.0 after normalization):
    final_score =
        relevance_score      * w_relevance   (title match + small category bonus)
      + price_score          * w_price       (lower unit price → higher score)
      + unit_match_score     * w_unit        (overbuying penalty)
      + brand_score          * w_brand       (brand alignment)
      + store_preference     * w_store

price_priority / brand_priority (from UserPreferences or intent) shift the weights.

Anti-bias notes:
  - relevance_score is driven 90% by title match and only 10% by a category
    bonus (Plaza Vea exposes data-ga-category; others don't).
  - Availability is not scored — only 1 of 4 stores exposes reliable stock
    data, making it a store-bias source rather than a useful signal.
    UNAVAILABLE products are hard-filtered before ranking reaches this stage.
"""

from app.models.common import Priority, QuantityUnit
from app.models.intent_models import ShoppingIntentItem
from app.models.preference_models import UserPreferences
from app.models.product_models import ProductCandidate
from app.utils.text_cleaning import normalize_for_comparison, tokenize
from app.utils.unit_parser import are_compatible, calculate_required_units, to_base_value

_EPSILON = 1e-9

# Priority → weight multiplier
_PRIORITY_FACTOR = {Priority.HIGH: 1.5, Priority.MEDIUM: 1.0, Priority.LOW: 0.5}


class RankingService:
    """Deterministic ranking: score every candidate, sort best-first."""

    def rank(
        self,
        candidates: list[ProductCandidate],
        intent_item: ShoppingIntentItem,
        preferences: UserPreferences,
    ) -> list[ProductCandidate]:
        """Return candidates sorted by final_score descending."""
        if not candidates:
            return []
        scored = [
            (c, self.score(c, intent_item, preferences, candidates))
            for c in candidates
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored]

    def score(
        self,
        candidate: ProductCandidate,
        intent_item: ShoppingIntentItem,
        preferences: UserPreferences,
        peer_candidates: list[ProductCandidate],
    ) -> float:
        """Compute final ranking score in [0.0, 1.0]."""
        w = _compute_weights(intent_item, preferences)
        raw = (
            _relevance_score(candidate, intent_item) * w["relevance"]
            + _price_score(candidate, peer_candidates) * w["price"]
            + _unit_match_score(candidate, intent_item) * w["unit"]
            + _brand_score(candidate, intent_item, preferences) * w["brand"]
            + _store_score(candidate, preferences) * w["store"]
        )
        return max(0.0, min(1.0, raw))

    def score_breakdown(
        self,
        candidate: ProductCandidate,
        intent_item: ShoppingIntentItem,
        preferences: UserPreferences,
        peer_candidates: list[ProductCandidate],
    ) -> dict[str, float]:
        """Return individual ranking component scores. Used only for debug output."""
        return {
            "relevance": _relevance_score(candidate, intent_item),
            "price":     _price_score(candidate, peer_candidates),
            "unit":      _unit_match_score(candidate, intent_item),
            "brand":     _brand_score(candidate, intent_item, preferences),
            "store":     _store_score(candidate, preferences),
            "final":     self.score(candidate, intent_item, preferences, peer_candidates),
        }


# ── Weight computation ────────────────────────────────────────────────────────

def _compute_weights(
    intent_item: ShoppingIntentItem, preferences: UserPreferences
) -> dict[str, float]:
    """Return normalized weights adjusted for user priorities."""
    # Use the higher of intent-level and global price sensitivity
    effective_price_priority = (
        intent_item.price_sensitivity
        if _PRIORITY_FACTOR[intent_item.price_sensitivity]
        > _PRIORITY_FACTOR[preferences.price_priority]
        else preferences.price_priority
    )
    w = dict(
        relevance=0.35,
        price=0.25 * _PRIORITY_FACTOR[effective_price_priority],
        unit=0.15,
        brand=0.15 * _PRIORITY_FACTOR[preferences.brand_priority],
        store=0.10,
    )
    total = sum(w.values())
    return {k: v / total for k, v in w.items()}


# ── Component scorers ─────────────────────────────────────────────────────────

def _relevance_score(candidate: ProductCandidate, intent_item: ShoppingIntentItem) -> float:
    """
    Title match is the primary signal (90% weight).
    A matching category adds a small bonus (up to 0.10) — this keeps category
    useful as a disambiguation signal without creating a systematic advantage
    for stores that expose richer metadata than others.
    """
    query_tokens = tokenize(intent_item.product_query)
    if not query_tokens:
        return 0.5

    title_norm = normalize_for_comparison(candidate.title)
    title_hits = sum(1 for t in query_tokens if t in title_norm)
    title_s = title_hits / len(query_tokens)

    cat_bonus = 0.0
    if candidate.category:
        cat_norm = normalize_for_comparison(candidate.category)
        if any(t in cat_norm for t in query_tokens):
            cat_bonus = 0.10

    return min(1.0, title_s * 0.90 + cat_bonus)


def _price_score(
    candidate: ProductCandidate, peers: list[ProductCandidate]
) -> float:
    """Normalize unit_price across peers: lower price → higher score."""
    prices = [p.unit_price for p in peers if p.unit_price >= 0]
    if not prices:
        return 0.5
    lo, hi = min(prices), max(prices)
    if hi - lo < _EPSILON:
        return 1.0  # all same price
    return 1.0 - (candidate.unit_price - lo) / (hi - lo)


def _unit_match_score(
    candidate: ProductCandidate, intent_item: ShoppingIntentItem
) -> float:
    """
    Penalize excessive overbuying.

    - No quantity requested → 0.5 (neutral)
    - Exact fit or compatible units with minimal excess → 1.0
    - Excess equal to requested (buying double) → 0.5
    - Excess ≥ 2× requested → 0.0
    """
    if intent_item.quantity is None or intent_item.unit is None:
        return 0.5
    result = calculate_required_units(
        intent_item.quantity,
        intent_item.unit,
        candidate.quantity_value,
        candidate.quantity_unit,
    )
    if result is None:
        return 0.5  # incompatible units — don't penalize here (relevance handles it)
    _, _, excess_base = result
    req_base = to_base_value(intent_item.quantity, intent_item.unit)
    if req_base <= _EPSILON:
        return 1.0
    excess_ratio = excess_base / req_base  # 0 = exact fit, 1 = buying double, 2 = triple
    return max(0.0, 1.0 - excess_ratio * 0.5)


def _brand_score(
    candidate: ProductCandidate,
    intent_item: ShoppingIntentItem,
    preferences: UserPreferences,
) -> float:
    """Brand alignment — mirrors FilteringService._brand_score."""
    candidate_brand = normalize_for_comparison(candidate.brand or "")

    if intent_item.brand_preference:
        pref = normalize_for_comparison(intent_item.brand_preference)
        if candidate_brand and pref in candidate_brand:
            return 1.0
        return 0.3 if intent_item.allow_substitution else 0.0

    preferred = {normalize_for_comparison(b) for b in preferences.preferred_brands}
    if preferred and candidate_brand in preferred:
        return 1.0
    if preferences.known_brands_only and not candidate_brand:
        return 0.0
    return 0.5


def _store_score(candidate: ProductCandidate, preferences: UserPreferences) -> float:
    return 1.0 if candidate.store in preferences.preferred_stores else 0.0
