"""Tests for CartReasoningService — deterministic, no real LLM calls."""
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.cart_models import CartItem, CartRecommendation
from app.models.common import Availability, QuantityUnit, StoreId
from app.models.intent_models import ShoppingIntent, ShoppingIntentItem
from app.models.product_models import ProductCandidate
from app.services.cart_reasoning_service import (
    CartReasoningError,
    CartReasoningService,
    CartReasonOutput,
    _build_cart_summary,
    _parse_reason_output,
    _rebuild_cart_item,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _candidate(title: str = "Arroz Extra Costeño 5 Kg") -> ProductCandidate:
    return ProductCandidate(
        store=StoreId.PLAZA_VEA,
        title=title,
        brand="COSTEÑO",
        price=18.90,
        presentation_text="Bolsa 5 Kg",
        quantity_value=5.0,
        quantity_unit=QuantityUnit.KG,
        unit_price=3.78,
        availability=Availability.AVAILABLE,
        product_url="https://example.com/product",
        search_query="arroz",
        scraped_at=datetime.now(timezone.utc),
    )


def _cart_item(
    requested: str = "5 kg de arroz",
    product: str = "Arroz Extra Costeño 5 Kg",
    query_key: str = "arroz",
) -> CartItem:
    return CartItem(
        requested_item=requested,
        selected_product=product,
        store=StoreId.PLAZA_VEA,
        unit_price=3.78,
        product_quantity_value=5.0,
        product_quantity_unit=QuantityUnit.KG,
        required_units=1,
        effective_quantity=5.0,
        excess_quantity=0.0,
        estimated_total=18.90,
        product_url="https://example.com/product",
        reason="",
        alternatives=[],
    )


def _intent_item(
    raw: str = "5 kg de arroz",
    query: str = "arroz",
) -> ShoppingIntentItem:
    return ShoppingIntentItem(
        raw_text=raw,
        product_query=query,
        quantity=5.0,
        unit=QuantityUnit.KG,
    )


def _intent(*items: ShoppingIntentItem) -> ShoppingIntent:
    return ShoppingIntent(shopping_intent=list(items))


def _recommendation(
    cart: list[CartItem] | None = None,
    warnings: list[str] | None = None,
    questions: list[str] | None = None,
) -> CartRecommendation:
    return CartRecommendation(
        cart=cart or [_cart_item()],
        total_estimated_cost=sum(c.estimated_total for c in (cart or [_cart_item()])),
        warnings=warnings or [],
        questions=questions or [],
    )


def _make_service(llm_json_response: str) -> CartReasoningService:
    """Build a CartReasoningService with a mocked LLM."""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = llm_json_response
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    return CartReasoningService(client=mock_client, model="gpt-test", system_prompt="test")


VALID_REASON_JSON = json.dumps({
    "reasons": {"arroz": "Se seleccionó Costeño por su excelente relación calidad-precio."},
    "warnings": [],
    "questions": [],
})


# ── _parse_reason_output ──────────────────────────────────────────────────────

class TestParseReasonOutput:
    def test_valid_response_parsed(self):
        result = _parse_reason_output(VALID_REASON_JSON)
        assert isinstance(result, CartReasonOutput)
        assert "arroz" in result.reasons

    def test_reasons_dict_content(self):
        result = _parse_reason_output(VALID_REASON_JSON)
        assert "Costeño" in result.reasons["arroz"]

    def test_empty_warnings_and_questions(self):
        result = _parse_reason_output(VALID_REASON_JSON)
        assert result.warnings == []
        assert result.questions == []

    def test_with_warnings_and_questions(self):
        data = json.dumps({
            "reasons": {"leche": "Buena opción."},
            "warnings": ["Producto con poco stock."],
            "questions": ["¿Prefieres leche descremada?"],
        })
        result = _parse_reason_output(data)
        assert len(result.warnings) == 1
        assert len(result.questions) == 1

    def test_non_json_raises(self):
        with pytest.raises(CartReasoningError, match="non-JSON"):
            _parse_reason_output("esto no es JSON")

    def test_wrong_schema_raises(self):
        with pytest.raises(CartReasoningError, match="schema"):
            _parse_reason_output('{"wrong_key": {}}')

    def test_empty_reasons_accepted(self):
        data = json.dumps({"reasons": {}, "warnings": [], "questions": []})
        result = _parse_reason_output(data)
        assert result.reasons == {}

    def test_swaps_field_parsed(self):
        data = json.dumps({
            "reasons": {"leche": "Se cambió a leche entera."},
            "swaps": {"leche": 0},
            "warnings": [],
            "questions": [],
        })
        result = _parse_reason_output(data)
        assert result.swaps == {"leche": 0}

    def test_swaps_defaults_to_empty(self):
        result = _parse_reason_output(VALID_REASON_JSON)
        assert result.swaps == {}


# ── _build_cart_summary ───────────────────────────────────────────────────────

class TestBuildCartSummary:
    def test_returns_valid_json(self):
        rec = _recommendation()
        intent = _intent(_intent_item())
        summary = _build_cart_summary(rec, intent, "5 kg de arroz")
        parsed = json.loads(summary)
        assert "cart" in parsed
        assert "user_message" in parsed

    def test_user_message_included(self):
        rec = _recommendation()
        intent = _intent(_intent_item())
        summary = _build_cart_summary(rec, intent, "Necesito arroz y leche")
        parsed = json.loads(summary)
        assert parsed["user_message"] == "Necesito arroz y leche"

    def test_product_query_in_cart_items(self):
        rec = _recommendation()
        intent = _intent(_intent_item(raw="5 kg de arroz", query="arroz"))
        summary = _build_cart_summary(rec, intent, "5 kg de arroz")
        parsed = json.loads(summary)
        assert parsed["cart"][0]["product_query"] == "arroz"

    def test_total_cost_included(self):
        rec = _recommendation()
        intent = _intent(_intent_item())
        summary = _build_cart_summary(rec, intent, "arroz")
        parsed = json.loads(summary)
        assert parsed["total_estimated_cost"] == rec.total_estimated_cost

    def test_alternatives_capped_at_three(self):
        item = _cart_item()
        item = item.model_copy(update={
            "alternatives": [_candidate(f"Arroz {i}") for i in range(5)]
        })
        rec = CartRecommendation(cart=[item], total_estimated_cost=18.90)
        intent = _intent(_intent_item())
        summary = _build_cart_summary(rec, intent, "arroz")
        parsed = json.loads(summary)
        assert len(parsed["cart"][0]["alternatives"]) == 3

    def test_existing_warnings_included(self):
        rec = _recommendation(warnings=["Advertencia previa"])
        intent = _intent(_intent_item())
        summary = _build_cart_summary(rec, intent, "arroz")
        parsed = json.loads(summary)
        assert "Advertencia previa" in parsed["warnings"]

    def test_alternatives_include_index(self):
        item = _cart_item()
        item = item.model_copy(update={
            "alternatives": [_candidate(f"Arroz {i}") for i in range(2)]
        })
        rec = CartRecommendation(cart=[item], total_estimated_cost=18.90)
        intent = _intent(_intent_item())
        summary = _build_cart_summary(rec, intent, "arroz")
        parsed = json.loads(summary)
        alts = parsed["cart"][0]["alternatives"]
        assert alts[0]["index"] == 0
        assert alts[1]["index"] == 1
        assert "title" in alts[0]
        assert "store" in alts[0]


# ── CartReasoningService.enrich ───────────────────────────────────────────────

class TestCartReasoningServiceEnrich:
    async def test_empty_cart_returned_unchanged(self):
        svc = _make_service(VALID_REASON_JSON)
        empty_rec = CartRecommendation(cart=[], total_estimated_cost=0.0)
        result = await svc.enrich(empty_rec, _intent(), "nada")
        assert result.cart == []
        svc.client.chat.completions.create.assert_not_called()

    async def test_reason_applied_to_cart_item(self):
        svc = _make_service(VALID_REASON_JSON)
        result = await svc.enrich(_recommendation(), _intent(_intent_item()), "arroz")
        assert result.cart[0].reason != ""
        assert "Costeño" in result.cart[0].reason

    async def test_llm_called_once(self):
        svc = _make_service(VALID_REASON_JSON)
        await svc.enrich(_recommendation(), _intent(_intent_item()), "arroz")
        svc.client.chat.completions.create.assert_called_once()

    async def test_llm_receives_system_prompt(self):
        svc = _make_service(VALID_REASON_JSON)
        await svc.enrich(_recommendation(), _intent(_intent_item()), "arroz")
        call_kwargs = svc.client.chat.completions.create.call_args.kwargs
        messages = call_kwargs["messages"]
        system = next(m for m in messages if m["role"] == "system")
        assert system["content"] == "test"

    async def test_temperature_is_zero(self):
        svc = _make_service(VALID_REASON_JSON)
        await svc.enrich(_recommendation(), _intent(_intent_item()), "arroz")
        call_kwargs = svc.client.chat.completions.create.call_args.kwargs
        assert call_kwargs["temperature"] == 0

    async def test_original_recommendation_not_mutated(self):
        svc = _make_service(VALID_REASON_JSON)
        original = _recommendation()
        original_reason = original.cart[0].reason
        await svc.enrich(original, _intent(_intent_item()), "arroz")
        assert original.cart[0].reason == original_reason

    async def test_llm_warnings_merged(self):
        response = json.dumps({
            "reasons": {"arroz": "Buena opción."},
            "warnings": ["Advertencia del LLM"],
            "questions": [],
        })
        svc = _make_service(response)
        rec = _recommendation(warnings=["Advertencia previa"])
        result = await svc.enrich(rec, _intent(_intent_item()), "arroz")
        assert "Advertencia previa" in result.warnings
        assert "Advertencia del LLM" in result.warnings

    async def test_llm_questions_merged(self):
        response = json.dumps({
            "reasons": {"arroz": "Buena opción."},
            "warnings": [],
            "questions": ["¿Prefieres otra marca?"],
        })
        svc = _make_service(response)
        result = await svc.enrich(_recommendation(), _intent(_intent_item()), "arroz")
        assert "¿Prefieres otra marca?" in result.questions

    async def test_missing_reason_key_gives_empty_string(self):
        response = json.dumps({"reasons": {}, "warnings": [], "questions": []})
        svc = _make_service(response)
        result = await svc.enrich(_recommendation(), _intent(_intent_item()), "arroz")
        assert result.cart[0].reason == ""

    async def test_non_json_response_raises(self):
        svc = _make_service("no es JSON")
        with pytest.raises(CartReasoningError):
            await svc.enrich(_recommendation(), _intent(_intent_item()), "arroz")

    async def test_multi_item_cart_all_enriched(self):
        response = json.dumps({
            "reasons": {
                "arroz": "Mejor precio.",
                "leche": "Marca confiable.",
            },
            "warnings": [],
            "questions": [],
        })
        svc = _make_service(response)
        cart = [
            _cart_item(requested="5 kg arroz", product="Arroz 5 Kg"),
            _cart_item(requested="2 l leche", product="Leche Gloria 1L"),
        ]
        rec = CartRecommendation(cart=cart, total_estimated_cost=29.90)
        intent = _intent(
            _intent_item(raw="5 kg arroz", query="arroz"),
            _intent_item(raw="2 l leche", query="leche"),
        )
        result = await svc.enrich(rec, intent, "arroz y leche")
        assert result.cart[0].reason == "Mejor precio."
        assert result.cart[1].reason == "Marca confiable."

    async def test_enrich_applies_valid_swap(self):
        alt = _candidate("Arroz Costeño 5 Kg")
        item = _cart_item()
        item = item.model_copy(update={"alternatives": [alt]})
        rec = CartRecommendation(cart=[item], total_estimated_cost=18.90)
        response = json.dumps({
            "reasons": {"arroz": "Se cambió a una mejor opción."},
            "swaps": {"arroz": 0},
            "warnings": [],
            "questions": [],
        })
        svc = _make_service(response)
        result = await svc.enrich(rec, _intent(_intent_item()), "arroz")
        assert result.cart[0].selected_product == "Arroz Costeño 5 Kg"
        assert result.cart[0].reason == "Se cambió a una mejor opción."

    async def test_enrich_ignores_out_of_range_swap(self):
        item = _cart_item()  # no alternatives
        rec = CartRecommendation(cart=[item], total_estimated_cost=18.90)
        response = json.dumps({
            "reasons": {"arroz": "Selección válida."},
            "swaps": {"arroz": 5},  # índice fuera de rango
            "warnings": [],
            "questions": [],
        })
        svc = _make_service(response)
        result = await svc.enrich(rec, _intent(_intent_item()), "arroz")
        assert result.cart[0].selected_product == "Arroz Extra Costeño 5 Kg"  # sin cambio

    async def test_enrich_swap_updates_total(self):
        alt = _candidate("Arroz Económico 5 Kg")
        alt = alt.model_copy(update={"price": 15.00, "unit_price": 3.00})
        item = _cart_item()  # estimated_total = 18.90
        item = item.model_copy(update={"alternatives": [alt]})
        rec = CartRecommendation(cart=[item], total_estimated_cost=18.90)
        response = json.dumps({
            "reasons": {"arroz": "Opción más económica."},
            "swaps": {"arroz": 0},
            "warnings": [],
            "questions": [],
        })
        svc = _make_service(response)
        result = await svc.enrich(rec, _intent(_intent_item()), "arroz")
        assert result.total_estimated_cost == 15.00


# ── _rebuild_cart_item ────────────────────────────────────────────────────────

class TestRebuildCartItem:
    def test_updates_product_fields(self):
        original = _cart_item()
        new_candidate = _candidate("Arroz Faraón 5 Kg")
        new_candidate = new_candidate.model_copy(update={
            "price": 20.0, "unit_price": 4.0, "store": StoreId.METRO,
        })
        rebuilt = _rebuild_cart_item(original, new_candidate, [], _intent_item())
        assert rebuilt.selected_product == "Arroz Faraón 5 Kg"
        assert rebuilt.store == StoreId.METRO
        assert rebuilt.estimated_total == 20.0

    def test_remaining_alts_set_correctly(self):
        original = _cart_item()
        alt1 = _candidate("Arroz A")
        alt2 = _candidate("Arroz B")
        rebuilt = _rebuild_cart_item(original, _candidate(), [alt1, alt2], None)
        assert len(rebuilt.alternatives) == 2

    def test_without_intent_defaults_one_unit(self):
        original = _cart_item()
        new_candidate = _candidate("Arroz 1 Kg")
        rebuilt = _rebuild_cart_item(original, new_candidate, [], None)
        assert rebuilt.required_units == 1

    def test_original_not_mutated(self):
        original = _cart_item()
        original_title = original.selected_product
        _rebuild_cart_item(original, _candidate("Otro Arroz"), [], None)
        assert original.selected_product == original_title
