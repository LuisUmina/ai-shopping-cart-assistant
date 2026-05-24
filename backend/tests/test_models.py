from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.cart_models import CartItem, CartRecommendation
from app.models.common import Availability, Priority, QuantityUnit, StoreId
from app.models.intent_models import ShoppingIntent, ShoppingIntentItem
from app.models.preference_models import UserPreferences
from app.models.product_models import ProductCandidate

NOW = datetime.now(timezone.utc)

VALID_PRODUCT = {
    "store": "plaza_vea",
    "title": "Arroz Costeño Extra Bolsa 5 kg",
    "brand": "Costeño",
    "price": 24.90,
    "presentation_text": "Bolsa 5 kg",
    "quantity_value": 5.0,
    "quantity_unit": "kg",
    "unit_price": 4.98,
    "availability": "available",
    "product_url": "https://example.com/arroz",
    "search_query": "arroz",
    "scraped_at": NOW.isoformat(),
}


# ── ProductCandidate ──────────────────────────────────────────────────────────

class TestProductCandidate:
    def test_valid(self):
        p = ProductCandidate(**VALID_PRODUCT)
        assert p.store == StoreId.PLAZA_VEA
        assert p.price == 24.90
        assert p.currency == "PEN"
        assert p.availability == Availability.AVAILABLE
        assert p.confidence.price_extraction == 1.0

    def test_optional_fields_default_to_none(self):
        p = ProductCandidate(**VALID_PRODUCT)
        assert p.product_id is None
        assert p.brand is not None  # supplied
        assert p.image_url is None

    def test_missing_required_title_raises(self):
        data = {**VALID_PRODUCT}
        del data["title"]
        with pytest.raises(ValidationError):
            ProductCandidate(**data)

    def test_negative_price_raises(self):
        with pytest.raises(ValidationError):
            ProductCandidate(**{**VALID_PRODUCT, "price": -1.0})

    def test_negative_quantity_raises(self):
        with pytest.raises(ValidationError):
            ProductCandidate(**{**VALID_PRODUCT, "quantity_value": -5.0})

    def test_invalid_store_raises(self):
        with pytest.raises(ValidationError):
            ProductCandidate(**{**VALID_PRODUCT, "store": "carrefour"})

    def test_invalid_unit_raises(self):
        with pytest.raises(ValidationError):
            ProductCandidate(**{**VALID_PRODUCT, "quantity_unit": "ton"})


# ── ShoppingIntent ────────────────────────────────────────────────────────────

class TestShoppingIntent:
    def test_valid(self):
        intent = ShoppingIntent(
            shopping_intent=[
                {
                    "raw_text": "5 kilos de arroz",
                    "product_query": "arroz",
                    "quantity": 5,
                    "unit": "kg",
                    "brand_preference": None,
                    "price_sensitivity": "medium",
                    "allow_substitution": True,
                }
            ]
        )
        assert len(intent.shopping_intent) == 1
        item = intent.shopping_intent[0]
        assert item.product_query == "arroz"
        assert item.unit == QuantityUnit.KG
        assert item.price_sensitivity == Priority.MEDIUM

    def test_null_optional_fields(self):
        item = ShoppingIntentItem(raw_text="detergente barato", product_query="detergente")
        assert item.quantity is None
        assert item.unit is None
        assert item.brand_preference is None
        assert item.allow_substitution is True

    def test_missing_product_query_raises(self):
        with pytest.raises(ValidationError):
            ShoppingIntentItem(raw_text="arroz")

    def test_empty_intent_list_is_valid(self):
        intent = ShoppingIntent(shopping_intent=[])
        assert intent.shopping_intent == []


# ── UserPreferences ───────────────────────────────────────────────────────────

class TestUserPreferences:
    def test_defaults(self):
        prefs = UserPreferences()
        assert prefs.price_priority == Priority.HIGH
        assert prefs.brand_priority == Priority.MEDIUM
        assert prefs.allow_substitutions is True
        assert len(prefs.preferred_stores) == 4
        assert StoreId.PLAZA_VEA in prefs.preferred_stores
        assert prefs.max_candidates_per_product == 5

    def test_custom_values(self):
        prefs = UserPreferences(
            price_priority="low",
            known_brands_only=True,
            preferred_stores=["metro", "tottus"],
            excluded_brands=["marca_x"],
            max_candidates_per_product=10,
        )
        assert prefs.price_priority == Priority.LOW
        assert prefs.known_brands_only is True
        assert len(prefs.preferred_stores) == 2
        assert prefs.excluded_brands == ["marca_x"]

    def test_max_candidates_bounds(self):
        with pytest.raises(ValidationError):
            UserPreferences(max_candidates_per_product=0)
        with pytest.raises(ValidationError):
            UserPreferences(max_candidates_per_product=21)

    def test_invalid_store_raises(self):
        with pytest.raises(ValidationError):
            UserPreferences(preferred_stores=["walmart"])


# ── CartItem / CartRecommendation ─────────────────────────────────────────────

class TestCart:
    def _make_item(self, **overrides) -> dict:
        base = {
            "requested_item": "arroz 5 kg",
            "selected_product": "Arroz Costeño 5 kg",
            "store": "plaza_vea",
            "unit_price": 4.98,
            "product_quantity_value": 5.0,
            "product_quantity_unit": "kg",
            "required_units": 1,
            "effective_quantity": 5.0,
            "excess_quantity": 0.0,
            "estimated_total": 24.90,
            "product_url": "https://example.com/arroz",
            "reason": "Exact quantity, best unit price.",
        }
        return {**base, **overrides}

    def test_valid_cart_item(self):
        item = CartItem(**self._make_item())
        assert item.required_units == 1
        assert item.excess_quantity == 0.0
        assert item.alternatives == []

    def test_invalid_required_units_zero(self):
        with pytest.raises(ValidationError):
            CartItem(**self._make_item(required_units=0))

    def test_cart_recommendation(self):
        item = CartItem(**self._make_item())
        rec = CartRecommendation(cart=[item], total_estimated_cost=24.90)
        assert rec.total_estimated_cost == 24.90
        assert rec.warnings == []
        assert rec.questions == []

    def test_cart_item_with_alternatives(self):
        alt = ProductCandidate(**VALID_PRODUCT)
        item = CartItem(**self._make_item(alternatives=[alt]))
        assert len(item.alternatives) == 1
