"""Tests for RankingService — deterministic, no I/O."""
from datetime import datetime, timezone

import pytest

from app.models.common import Availability, Priority, QuantityUnit, StoreId
from app.models.intent_models import ShoppingIntentItem
from app.models.preference_models import UserPreferences
from app.models.product_models import ProductCandidate
from app.services.ranking_service import (
    RankingService,
    _availability_score,
    _brand_score,
    _price_score,
    _relevance_score,
    _store_score,
    _unit_match_score,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _candidate(
    title: str = "Arroz Extra Costeño Bolsa 5 Kg",
    brand: str | None = "COSTEÑO",
    category: str | None = "Abarrotes / Arroz",
    unit_price: float = 3.78,
    quantity_value: float = 5.0,
    quantity_unit: QuantityUnit = QuantityUnit.KG,
    availability: Availability = Availability.AVAILABLE,
    store: StoreId = StoreId.PLAZA_VEA,
    price: float = 18.90,
) -> ProductCandidate:
    return ProductCandidate(
        store=store,
        title=title,
        brand=brand,
        category=category,
        price=price,
        presentation_text="Bolsa 5 Kg",
        quantity_value=quantity_value,
        quantity_unit=quantity_unit,
        unit_price=unit_price,
        availability=availability,
        product_url="https://example.com/product",
        search_query="arroz",
        scraped_at=datetime.now(timezone.utc),
    )


def _intent(
    query: str = "arroz",
    quantity: float | None = None,
    unit: QuantityUnit | None = None,
    brand: str | None = None,
    price_sensitivity: Priority = Priority.MEDIUM,
    allow_substitution: bool = True,
) -> ShoppingIntentItem:
    return ShoppingIntentItem(
        raw_text=query,
        product_query=query,
        quantity=quantity,
        unit=unit,
        brand_preference=brand,
        price_sensitivity=price_sensitivity,
        allow_substitution=allow_substitution,
    )


def _prefs(**kwargs) -> UserPreferences:
    return UserPreferences(**kwargs)


svc = RankingService()


# ── Relevance score ───────────────────────────────────────────────────────────

class TestRelevanceScore:
    def test_exact_title_match(self):
        c = _candidate(title="Arroz Extra Costeño Bolsa 5 Kg", category="Abarrotes / Arroz")
        s = _relevance_score(c, _intent("arroz"))
        assert s > 0.5

    def test_unrelated_product_scores_low(self):
        c = _candidate(title="Leche Gloria Entera 1L", category="Lácteos")
        s = _relevance_score(c, _intent("arroz"))
        assert s < 0.5

    def test_no_category_is_neutral(self):
        with_cat = _candidate(title="Arroz Extra 5 Kg", category="Arroz")
        without_cat = _candidate(title="Arroz Extra 5 Kg", category=None)
        s_with = _relevance_score(with_cat, _intent("arroz"))
        s_without = _relevance_score(without_cat, _intent("arroz"))
        # Without category is neutral — should still score OK if title matches
        assert s_without > 0.0
        assert s_with >= s_without


# ── Price score ───────────────────────────────────────────────────────────────

class TestPriceScore:
    def test_cheapest_scores_one(self):
        cheap = _candidate(unit_price=2.00)
        mid = _candidate(unit_price=4.00)
        expensive = _candidate(unit_price=8.00)
        peers = [cheap, mid, expensive]
        assert _price_score(cheap, peers) == pytest.approx(1.0)

    def test_most_expensive_scores_zero(self):
        cheap = _candidate(unit_price=2.00)
        expensive = _candidate(unit_price=8.00)
        assert _price_score(expensive, [cheap, expensive]) == pytest.approx(0.0)

    def test_all_same_price_scores_one(self):
        c = _candidate(unit_price=5.00)
        assert _price_score(c, [c, c, c]) == pytest.approx(1.0)

    def test_single_candidate_scores_one(self):
        c = _candidate(unit_price=5.00)
        assert _price_score(c, [c]) == pytest.approx(1.0)

    def test_midrange_scores_between_zero_and_one(self):
        cheap = _candidate(unit_price=2.00)
        mid = _candidate(unit_price=5.00)
        expensive = _candidate(unit_price=8.00)
        s = _price_score(mid, [cheap, mid, expensive])
        assert 0.0 < s < 1.0


# ── Unit match score ──────────────────────────────────────────────────────────

class TestUnitMatchScore:
    def test_no_quantity_is_neutral(self):
        c = _candidate(quantity_value=5.0, quantity_unit=QuantityUnit.KG)
        s = _unit_match_score(c, _intent(quantity=None, unit=None))
        assert s == pytest.approx(0.5)

    def test_exact_fit_scores_one(self):
        c = _candidate(quantity_value=5.0, quantity_unit=QuantityUnit.KG)
        s = _unit_match_score(c, _intent(quantity=5.0, unit=QuantityUnit.KG))
        assert s == pytest.approx(1.0)

    def test_multiple_units_no_excess(self):
        # User wants 5 kg, product is 1 kg → need 5 units, no excess
        c = _candidate(quantity_value=1.0, quantity_unit=QuantityUnit.KG)
        s = _unit_match_score(c, _intent(quantity=5.0, unit=QuantityUnit.KG))
        assert s == pytest.approx(1.0)

    def test_significant_overbuying_penalized(self):
        # User wants 1 kg, product is 5 kg → 4 kg excess (400%)
        c = _candidate(quantity_value=5.0, quantity_unit=QuantityUnit.KG)
        s = _unit_match_score(c, _intent(quantity=1.0, unit=QuantityUnit.KG))
        assert s < 0.5

    def test_incompatible_units_neutral(self):
        # User wants kg, product is liters → incompatible, neutral
        c = _candidate(quantity_value=1.0, quantity_unit=QuantityUnit.L)
        s = _unit_match_score(c, _intent(quantity=1.0, unit=QuantityUnit.KG))
        assert s == pytest.approx(0.5)

    def test_score_never_negative(self):
        # Extreme overbuying — still >= 0
        c = _candidate(quantity_value=10.0, quantity_unit=QuantityUnit.KG)
        s = _unit_match_score(c, _intent(quantity=0.5, unit=QuantityUnit.KG))
        assert s >= 0.0


# ── Brand score ───────────────────────────────────────────────────────────────

class TestBrandScore:
    def test_no_preference_neutral(self):
        s = _brand_score(_candidate(brand="COSTEÑO"), _intent(), _prefs())
        assert s == pytest.approx(0.5)

    def test_brand_match(self):
        s = _brand_score(
            _candidate(brand="GLORIA"),
            _intent(brand="Gloria"),
            _prefs(),
        )
        assert s == pytest.approx(1.0)

    def test_brand_mismatch_with_substitution(self):
        s = _brand_score(
            _candidate(brand="LAIVE"),
            _intent(brand="Gloria", allow_substitution=True),
            _prefs(),
        )
        assert 0.0 < s < 1.0

    def test_brand_mismatch_no_substitution(self):
        s = _brand_score(
            _candidate(brand="LAIVE"),
            _intent(brand="Gloria", allow_substitution=False),
            _prefs(),
        )
        assert s == pytest.approx(0.0)


# ── Availability score ────────────────────────────────────────────────────────

class TestAvailabilityScore:
    def test_available(self):
        assert _availability_score(_candidate(availability=Availability.AVAILABLE)) == 1.0

    def test_unavailable(self):
        assert _availability_score(_candidate(availability=Availability.UNAVAILABLE)) == 0.0

    def test_unknown(self):
        assert _availability_score(_candidate(availability=Availability.UNKNOWN)) == 0.5


# ── Store score ───────────────────────────────────────────────────────────────

class TestStoreScore:
    def test_preferred_store_scores_one(self):
        c = _candidate(store=StoreId.PLAZA_VEA)
        assert _store_score(c, _prefs(preferred_stores=[StoreId.PLAZA_VEA])) == 1.0

    def test_non_preferred_store_scores_zero(self):
        c = _candidate(store=StoreId.METRO)
        assert _store_score(c, _prefs(preferred_stores=[StoreId.PLAZA_VEA])) == 0.0


# ── Rank method ───────────────────────────────────────────────────────────────

class TestRank:
    def test_empty_returns_empty(self):
        assert svc.rank([], _intent(), _prefs()) == []

    def test_single_candidate_returned(self):
        c = _candidate()
        assert svc.rank([c], _intent(), _prefs()) == [c]

    def test_cheaper_ranked_higher_when_price_priority_high(self):
        cheap = _candidate(title="Arroz Genérico 5 Kg", unit_price=2.00, price=10.00)
        expensive = _candidate(title="Arroz Premium 5 Kg", unit_price=6.00, price=30.00)
        ranked = svc.rank(
            [expensive, cheap],
            _intent(price_sensitivity=Priority.HIGH),
            _prefs(price_priority=Priority.HIGH),
        )
        assert ranked[0].unit_price < ranked[-1].unit_price

    def test_brand_match_ranked_higher(self):
        matching = _candidate(title="Arroz Costeño Extra 5 Kg", brand="COSTEÑO")
        other = _candidate(title="Arroz Faraón Extra 5 Kg", brand="FARAON")
        ranked = svc.rank(
            [other, matching],
            _intent(brand="Costeño"),
            _prefs(),
        )
        assert ranked[0].brand == "COSTEÑO"

    def test_available_ranked_above_unavailable(self):
        avail = _candidate(title="Arroz 5 Kg", availability=Availability.AVAILABLE)
        unavail = _candidate(title="Arroz 5 Kg", availability=Availability.UNAVAILABLE)
        ranked = svc.rank([unavail, avail], _intent(), _prefs())
        assert ranked[0].availability == Availability.AVAILABLE

    def test_score_in_zero_one_range(self):
        candidates = [
            _candidate(title="Arroz Extra 5 Kg", unit_price=3.00),
            _candidate(title="Arroz Genérico 1 Kg", unit_price=5.00),
        ]
        for c in candidates:
            s = svc.score(c, _intent("arroz"), _prefs(), candidates)
            assert 0.0 <= s <= 1.0
