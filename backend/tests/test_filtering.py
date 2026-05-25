"""
Tests for the pre-filtering engine (FilteringService).

All tests are deterministic — no LLM, no browser, no I/O.
"""
from datetime import datetime, timezone

import pytest

from app.models.common import Availability, QuantityUnit, StoreId
from app.models.intent_models import ShoppingIntentItem
from app.models.preference_models import UserPreferences
from app.models.product_models import ProductCandidate
from app.services.filtering_service import MIN_RELEVANCE_SCORE, FilteringService


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_candidate(
    title: str = "Arroz Extra Costeño Bolsa 5 Kg",
    brand: str | None = "COSTEÑO",
    category: str | None = "Abarrotes / Arroz",
    quantity_unit: QuantityUnit = QuantityUnit.KG,
    availability: Availability = Availability.AVAILABLE,
    price: float = 18.90,
) -> ProductCandidate:
    return ProductCandidate(
        store=StoreId.PLAZA_VEA,
        title=title,
        brand=brand,
        category=category,
        price=price,
        presentation_text="Bolsa 5 Kg",
        quantity_value=5.0,
        quantity_unit=quantity_unit,
        unit_price=price / 5,
        availability=availability,
        product_url="https://www.plazavea.com.pe/test",
        search_query="arroz",
        scraped_at=datetime.now(timezone.utc),
    )


def _intent(
    query: str = "arroz",
    brand: str | None = None,
    unit: QuantityUnit | None = None,
    allow_substitution: bool = True,
) -> ShoppingIntentItem:
    return ShoppingIntentItem(
        raw_text=query,
        product_query=query,
        brand_preference=brand,
        unit=unit,
        allow_substitution=allow_substitution,
    )


def _prefs(**kwargs) -> UserPreferences:
    return UserPreferences(**kwargs)


svc = FilteringService()


# ── Title scoring ─────────────────────────────────────────────────────────────

class TestTitleScore:
    def test_exact_single_token_match(self):
        score = svc._title_score("Arroz Extra Costeño 5 Kg", "arroz")
        assert score == pytest.approx(1.0)

    def test_partial_match_two_of_three_tokens(self):
        score = svc._title_score("Arroz Extra Bolsa 5 Kg", "arroz costeño extra")
        assert 0.0 < score < 1.0

    def test_no_match(self):
        score = svc._title_score("Leche Gloria Entera 1L", "arroz")
        assert score == pytest.approx(0.0)

    def test_empty_title(self):
        assert svc._title_score("", "arroz") == pytest.approx(0.0)

    def test_empty_query(self):
        assert svc._title_score("Arroz Extra", "") == pytest.approx(0.0)

    def test_multi_token_all_present(self):
        score = svc._title_score("Arroz Costeño Extra Bolsa 5 Kg", "arroz costeño")
        assert score == pytest.approx(1.0)

    def test_case_insensitive(self):
        score = svc._title_score("ARROZ EXTRA FARAON 5 KG", "arroz")
        assert score == pytest.approx(1.0)

    def test_accents_ignored(self):
        score = svc._title_score("Arroz Costeño Extra", "costeno")
        assert score == pytest.approx(1.0)


# ── Category scoring ──────────────────────────────────────────────────────────

class TestCategoryScore:
    def test_category_contains_query_token(self):
        score = svc._category_score("Abarrotes / Arroz / Arroz Extra", "arroz")
        assert score == pytest.approx(1.0)

    def test_category_does_not_match(self):
        score = svc._category_score("Bebidas / Jugos", "arroz")
        assert score == pytest.approx(0.0)

    def test_no_category_is_neutral(self):
        score = svc._category_score(None, "arroz")
        assert score == pytest.approx(0.5)

    def test_empty_category_is_neutral(self):
        score = svc._category_score("", "arroz")
        assert score == pytest.approx(0.5)


# ── Brand scoring ─────────────────────────────────────────────────────────────

class TestBrandScore:
    def test_no_preference_is_neutral(self):
        score = svc._brand_score(_make_candidate(brand="COSTEÑO"), _intent(), _prefs())
        assert score == pytest.approx(0.5)

    def test_intent_brand_match(self):
        score = svc._brand_score(
            _make_candidate(brand="GLORIA"),
            _intent(brand="Gloria"),
            _prefs(),
        )
        assert score == pytest.approx(1.0)

    def test_intent_brand_mismatch_allow_substitution(self):
        score = svc._brand_score(
            _make_candidate(brand="LAIVE"),
            _intent(brand="Gloria", allow_substitution=True),
            _prefs(),
        )
        assert 0.0 < score < 1.0

    def test_intent_brand_mismatch_no_substitution(self):
        score = svc._brand_score(
            _make_candidate(brand="LAIVE"),
            _intent(brand="Gloria", allow_substitution=False),
            _prefs(),
        )
        assert score == pytest.approx(0.0)

    def test_global_preferred_brand_match(self):
        score = svc._brand_score(
            _make_candidate(brand="COSTEÑO"),
            _intent(),
            _prefs(preferred_brands=["Costeño"]),
        )
        assert score == pytest.approx(1.0)

    def test_known_brands_only_penalizes_unknown(self):
        score = svc._brand_score(
            _make_candidate(brand=None),
            _intent(),
            _prefs(known_brands_only=True),
        )
        assert score == pytest.approx(0.0)

    def test_known_brands_only_passes_known(self):
        score = svc._brand_score(
            _make_candidate(brand="NESTLE"),
            _intent(),
            _prefs(known_brands_only=True),
        )
        assert score == pytest.approx(0.5)  # neutral — no explicit preference


# ── Unit scoring ──────────────────────────────────────────────────────────────

class TestUnitScore:
    def test_no_unit_preference_is_neutral(self):
        score = svc._unit_score(QuantityUnit.KG, None)
        assert score == pytest.approx(0.5)

    def test_compatible_units(self):
        score = svc._unit_score(QuantityUnit.KG, QuantityUnit.G)
        assert score == pytest.approx(1.0)

    def test_same_unit(self):
        score = svc._unit_score(QuantityUnit.L, QuantityUnit.L)
        assert score == pytest.approx(1.0)

    def test_incompatible_units(self):
        score = svc._unit_score(QuantityUnit.KG, QuantityUnit.L)
        assert score == pytest.approx(0.0)

    def test_count_vs_mass_incompatible(self):
        score = svc._unit_score(QuantityUnit.UNIT, QuantityUnit.KG)
        assert score == pytest.approx(0.0)


# ── Negative keyword penalty ──────────────────────────────────────────────────

class TestNegativeKeyword:
    def test_product_with_negative_keyword_penalized(self):
        c = _make_candidate(title="Taper de Vidrio para Arroz 1L")
        s = svc.score(c, _intent("arroz"), _prefs())
        assert s < MIN_RELEVANCE_SCORE

    def test_regular_product_not_penalized(self):
        c = _make_candidate(title="Arroz Extra Costeño Bolsa 5 Kg")
        s = svc.score(c, _intent("arroz"), _prefs())
        assert s >= MIN_RELEVANCE_SCORE

    def test_olla_triggers_penalty(self):
        c = _make_candidate(title="Olla Arrocera Digital 2L")
        s = svc.score(c, _intent("arroz"), _prefs())
        assert s < MIN_RELEVANCE_SCORE


# ── Combined score ────────────────────────────────────────────────────────────

class TestCombinedScore:
    def test_perfect_match_scores_high(self):
        c = _make_candidate(
            title="Arroz Extra Costeño Bolsa 5 Kg",
            brand="COSTEÑO",
            category="Abarrotes / Arroz",
            quantity_unit=QuantityUnit.KG,
            availability=Availability.AVAILABLE,
        )
        s = svc.score(c, _intent("arroz", brand="Costeño", unit=QuantityUnit.KG), _prefs())
        assert s >= 0.85

    def test_irrelevant_product_scores_low(self):
        c = _make_candidate(
            title="Leche Gloria Entera 1L",
            brand="GLORIA",
            category="Bebidas / Lácteos",
            quantity_unit=QuantityUnit.L,
        )
        s = svc.score(c, _intent("arroz"), _prefs())
        assert s < MIN_RELEVANCE_SCORE

    def test_score_clamped_to_zero_minimum(self):
        c = _make_candidate(
            title="Taper Vidrio Bandeja Accesorio Olla",  # many negative keywords
            category="Utensilios",
        )
        s = svc.score(c, _intent("arroz"), _prefs())
        assert s >= 0.0  # never negative

    def test_score_clamped_to_one_maximum(self):
        c = _make_candidate(
            title="Arroz Extra Costeño Bolsa 5 Kg",
            brand="COSTEÑO",
            category="Abarrotes / Arroz",
        )
        s = svc.score(c, _intent("arroz", brand="Costeño", unit=QuantityUnit.KG), _prefs())
        assert s <= 1.0


# ── Filter method ─────────────────────────────────────────────────────────────

class TestFilter:
    def test_below_threshold_rejected(self):
        irrelevant = _make_candidate(title="Leche Gloria Entera 1L", category="Lácteos")
        result = svc.filter([irrelevant], _intent("arroz"), _prefs())
        assert result == []

    def test_above_threshold_kept(self):
        relevant = _make_candidate(title="Arroz Extra Faraón Bolsa 5 Kg", category="Arroz")
        result = svc.filter([relevant], _intent("arroz"), _prefs())
        assert len(result) == 1

    def test_results_capped_at_max_candidates(self):
        candidates = [
            _make_candidate(title=f"Arroz Extra Marca{i} Bolsa 5 Kg", brand=f"MARCA{i}")
            for i in range(10)
        ]
        result = svc.filter(candidates, _intent("arroz"), _prefs(max_candidates_per_product=3))
        assert len(result) == 3

    def test_excluded_brand_rejected(self):
        c = _make_candidate(brand="COSTEÑO")
        result = svc.filter([c], _intent("arroz"), _prefs(excluded_brands=["Costeño"]))
        assert result == []

    def test_results_sorted_by_relevance(self):
        low = _make_candidate(title="Arroz Genérico", category=None, brand=None)
        high = _make_candidate(
            title="Arroz Extra Costeño Bolsa 5 Kg",
            category="Abarrotes / Arroz",
            brand="COSTEÑO",
        )
        result = svc.filter(
            [low, high],
            _intent("arroz", brand="Costeño"),
            _prefs(),
        )
        assert result[0].brand == "COSTEÑO"

    def test_empty_candidates_returns_empty(self):
        assert svc.filter([], _intent("arroz"), _prefs()) == []

    def test_all_below_threshold_returns_empty(self):
        candidates = [
            _make_candidate(title="Leche Gloria 1L", category="Lácteos"),
            _make_candidate(title="Detergente Ariel 1Kg", category="Limpieza"),
        ]
        assert svc.filter(candidates, _intent("arroz"), _prefs()) == []

    def test_non_excluded_brand_passes(self):
        c = _make_candidate(brand="FARAON", title="Arroz Extra Faraón Bolsa 5 Kg")
        result = svc.filter([c], _intent("arroz"), _prefs(excluded_brands=["Costeño"]))
        assert len(result) == 1

    def test_unavailable_product_is_hard_rejected(self):
        c = _make_candidate(
            title="Arroz Extra Faraón Bolsa 5 Kg",
            category="Abarrotes / Arroz",
            availability=Availability.UNAVAILABLE,
        )
        result = svc.filter([c], _intent("arroz"), _prefs())
        assert len(result) == 0
