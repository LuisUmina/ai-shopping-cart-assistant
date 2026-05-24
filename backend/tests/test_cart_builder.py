"""Tests for CartBuilder — deterministic, no I/O."""
from datetime import datetime, timezone

import pytest

from app.models.cart_models import CartItem, CartRecommendation
from app.models.common import Availability, QuantityUnit, StoreId
from app.models.intent_models import ShoppingIntent, ShoppingIntentItem
from app.models.preference_models import UserPreferences
from app.models.product_models import ProductCandidate
from app.services.cart_builder import CartBuilder


# ── Helpers ───────────────────────────────────────────────────────────────────

def _candidate(
    title: str = "Arroz Extra Costeño Bolsa 5 Kg",
    price: float = 18.90,
    quantity_value: float = 5.0,
    quantity_unit: QuantityUnit = QuantityUnit.KG,
    store: StoreId = StoreId.PLAZA_VEA,
    brand: str | None = "COSTEÑO",
) -> ProductCandidate:
    return ProductCandidate(
        store=store,
        title=title,
        brand=brand,
        price=price,
        presentation_text="Bolsa 5 Kg",
        quantity_value=quantity_value,
        quantity_unit=quantity_unit,
        unit_price=price / quantity_value,
        availability=Availability.AVAILABLE,
        product_url="https://example.com/product",
        search_query="arroz",
        scraped_at=datetime.now(timezone.utc),
    )


def _intent_item(
    raw: str = "5 kg de arroz",
    query: str = "arroz",
    quantity: float | None = 5.0,
    unit: QuantityUnit | None = QuantityUnit.KG,
) -> ShoppingIntentItem:
    return ShoppingIntentItem(
        raw_text=raw,
        product_query=query,
        quantity=quantity,
        unit=unit,
    )


def _intent(*items: ShoppingIntentItem) -> ShoppingIntent:
    return ShoppingIntent(shopping_intent=list(items))


builder = CartBuilder()
DEFAULT_PREFS = UserPreferences()


# ── Basic cart building ───────────────────────────────────────────────────────

class TestBuildBasic:
    def test_returns_cart_recommendation(self):
        item = _intent_item()
        result = builder.build(
            _intent(item),
            {"arroz": [_candidate()]},
            DEFAULT_PREFS,
        )
        assert isinstance(result, CartRecommendation)

    def test_cart_has_one_item(self):
        item = _intent_item()
        result = builder.build(_intent(item), {"arroz": [_candidate()]}, DEFAULT_PREFS)
        assert len(result.cart) == 1

    def test_cart_item_is_cart_item(self):
        result = builder.build(
            _intent(_intent_item()),
            {"arroz": [_candidate()]},
            DEFAULT_PREFS,
        )
        assert isinstance(result.cart[0], CartItem)

    def test_selected_product_title(self):
        c = _candidate(title="Arroz Extra Costeño Bolsa 5 Kg")
        result = builder.build(_intent(_intent_item()), {"arroz": [c]}, DEFAULT_PREFS)
        assert result.cart[0].selected_product == "Arroz Extra Costeño Bolsa 5 Kg"

    def test_total_estimated_cost(self):
        c = _candidate(price=18.90)
        result = builder.build(_intent(_intent_item()), {"arroz": [c]}, DEFAULT_PREFS)
        assert result.total_estimated_cost == pytest.approx(18.90)

    def test_empty_intent_returns_empty_cart(self):
        result = builder.build(ShoppingIntent(shopping_intent=[]), {}, DEFAULT_PREFS)
        assert result.cart == []
        assert result.total_estimated_cost == 0.0


# ── Required units ────────────────────────────────────────────────────────────

class TestRequiredUnits:
    def test_exact_match_one_unit(self):
        # User wants 5 kg, product is 5 kg → 1 unit
        c = _candidate(quantity_value=5.0, quantity_unit=QuantityUnit.KG, price=18.90)
        result = builder.build(_intent(_intent_item(quantity=5.0)), {"arroz": [c]}, DEFAULT_PREFS)
        assert result.cart[0].required_units == 1

    def test_multiple_units_needed(self):
        # User wants 5 kg, product is 1 kg → 5 units
        c = _candidate(quantity_value=1.0, quantity_unit=QuantityUnit.KG, price=5.20)
        result = builder.build(_intent(_intent_item(quantity=5.0)), {"arroz": [c]}, DEFAULT_PREFS)
        assert result.cart[0].required_units == 5

    def test_estimated_total_with_multiple_units(self):
        # 5 units × S/ 5.20 = S/ 26.00
        c = _candidate(quantity_value=1.0, quantity_unit=QuantityUnit.KG, price=5.20)
        result = builder.build(_intent(_intent_item(quantity=5.0)), {"arroz": [c]}, DEFAULT_PREFS)
        assert result.cart[0].estimated_total == pytest.approx(26.00)

    def test_no_quantity_defaults_to_one_unit(self):
        c = _candidate(price=18.90)
        result = builder.build(
            _intent(_intent_item(quantity=None, unit=None)),
            {"arroz": [c]},
            DEFAULT_PREFS,
        )
        assert result.cart[0].required_units == 1

    def test_excess_quantity_zero_when_exact_fit(self):
        c = _candidate(quantity_value=5.0, quantity_unit=QuantityUnit.KG)
        result = builder.build(_intent(_intent_item(quantity=5.0)), {"arroz": [c]}, DEFAULT_PREFS)
        assert result.cart[0].excess_quantity == pytest.approx(0.0)

    def test_excess_quantity_when_overbuying(self):
        # User wants 1 kg, product is 5 kg → excess = 4000 g in base units
        c = _candidate(quantity_value=5.0, quantity_unit=QuantityUnit.KG)
        result = builder.build(
            _intent(_intent_item(quantity=1.0, unit=QuantityUnit.KG)),
            {"arroz": [c]},
            DEFAULT_PREFS,
        )
        assert result.cart[0].excess_quantity > 0

    def test_incompatible_units_fallback_to_one(self):
        # User wants kg, product is liters → incompatible, fallback to 1 unit + warning
        c = _candidate(quantity_value=1.0, quantity_unit=QuantityUnit.L)
        result = builder.build(
            _intent(_intent_item(quantity=5.0, unit=QuantityUnit.KG)),
            {"arroz": [c]},
            DEFAULT_PREFS,
        )
        assert result.cart[0].required_units == 1
        assert any("unidad" in w.lower() for w in result.warnings)


# ── Alternatives ──────────────────────────────────────────────────────────────

class TestAlternatives:
    def test_first_candidate_is_selected(self):
        first = _candidate(title="Arroz A")
        second = _candidate(title="Arroz B")
        result = builder.build(_intent(_intent_item()), {"arroz": [first, second]}, DEFAULT_PREFS)
        assert result.cart[0].selected_product == "Arroz A"

    def test_alternatives_contain_remaining_candidates(self):
        first = _candidate(title="Arroz A")
        second = _candidate(title="Arroz B")
        third = _candidate(title="Arroz C")
        result = builder.build(
            _intent(_intent_item()),
            {"arroz": [first, second, third]},
            DEFAULT_PREFS,
        )
        alt_titles = [p.title for p in result.cart[0].alternatives]
        assert "Arroz B" in alt_titles
        assert "Arroz C" in alt_titles

    def test_no_alternatives_when_single_candidate(self):
        result = builder.build(
            _intent(_intent_item()),
            {"arroz": [_candidate()]},
            DEFAULT_PREFS,
        )
        assert result.cart[0].alternatives == []


# ── Warnings ──────────────────────────────────────────────────────────────────

class TestWarnings:
    def test_warning_when_no_candidates(self):
        result = builder.build(_intent(_intent_item()), {}, DEFAULT_PREFS)
        assert len(result.warnings) >= 1
        assert "arroz" in result.warnings[0].lower()

    def test_no_warning_for_normal_match(self):
        c = _candidate(quantity_value=5.0, quantity_unit=QuantityUnit.KG)
        result = builder.build(_intent(_intent_item(quantity=5.0)), {"arroz": [c]}, DEFAULT_PREFS)
        overbuying_warnings = [w for w in result.warnings if "pequeña" in w]
        assert overbuying_warnings == []

    def test_overbuying_warning(self):
        # Buying 5 kg when only 1 kg requested → significant overbuying
        c = _candidate(quantity_value=5.0, quantity_unit=QuantityUnit.KG)
        result = builder.build(
            _intent(_intent_item(quantity=1.0, unit=QuantityUnit.KG)),
            {"arroz": [c]},
            DEFAULT_PREFS,
        )
        assert any("pequeña" in w for w in result.warnings)


# ── Multi-item cart ───────────────────────────────────────────────────────────

class TestMultiItemCart:
    def test_two_items_in_cart(self):
        arroz = _intent_item("5 kg arroz", "arroz", 5.0, QuantityUnit.KG)
        leche = _intent_item("2 l leche", "leche", 2.0, QuantityUnit.L)
        c_arroz = _candidate("Arroz Extra 5 Kg", price=18.90, quantity_unit=QuantityUnit.KG)
        c_leche = _candidate(
            "Leche Gloria Entera 1L", price=5.50,
            quantity_value=1.0, quantity_unit=QuantityUnit.L
        )
        result = builder.build(
            _intent(arroz, leche),
            {"arroz": [c_arroz], "leche": [c_leche]},
            DEFAULT_PREFS,
        )
        assert len(result.cart) == 2

    def test_total_cost_is_sum_of_items(self):
        arroz = _intent_item("5 kg arroz", "arroz", 5.0, QuantityUnit.KG)
        leche = _intent_item("2 l leche", "leche", 2.0, QuantityUnit.L)
        c_arroz = _candidate("Arroz Extra 5 Kg", price=18.90, quantity_unit=QuantityUnit.KG)
        c_leche = _candidate(
            "Leche Gloria Entera 1L", price=5.50,
            quantity_value=1.0, quantity_unit=QuantityUnit.L
        )
        result = builder.build(
            _intent(arroz, leche),
            {"arroz": [c_arroz], "leche": [c_leche]},
            DEFAULT_PREFS,
        )
        # arroz: 1 unit × 18.90; leche: 2 units × 5.50 = 11.00; total = 29.90
        assert result.total_estimated_cost == pytest.approx(29.90)
