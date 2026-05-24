import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_intent_service
from app.main import app
from app.models.common import Priority, QuantityUnit
from app.models.intent_models import ShoppingIntent
from app.services.intent_service import (
    IntentExtractionError,
    IntentService,
    _parse_intent,
)

# ── Shared fixtures ───────────────────────────────────────────────────────────

VALID_INTENT_JSON = json.dumps({
    "shopping_intent": [
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
})

MULTI_ITEM_JSON = json.dumps({
    "shopping_intent": [
        {
            "raw_text": "2 litros de leche Gloria",
            "product_query": "leche",
            "quantity": 2,
            "unit": "l",
            "brand_preference": "Gloria",
            "price_sensitivity": "medium",
            "allow_substitution": True,
        },
        {
            "raw_text": "1 detergente barato",
            "product_query": "detergente",
            "quantity": 1,
            "unit": "unit",
            "brand_preference": None,
            "price_sensitivity": "high",
            "allow_substitution": True,
        },
    ]
})


def _make_service(llm_json_response: str) -> IntentService:
    """Build an IntentService with a mocked LLM that returns the given JSON."""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = llm_json_response
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    return IntentService(client=mock_client, model="gpt-test", system_prompt="test")


# ── _parse_intent (unit tests — no LLM involved) ─────────────────────────────

class TestParseIntent:
    def test_valid_single_item(self):
        result = _parse_intent(VALID_INTENT_JSON)
        assert len(result.shopping_intent) == 1
        item = result.shopping_intent[0]
        assert item.product_query == "arroz"
        assert item.quantity == 5
        assert item.unit == QuantityUnit.KG
        assert item.brand_preference is None
        assert item.price_sensitivity == Priority.MEDIUM

    def test_valid_multi_item(self):
        result = _parse_intent(MULTI_ITEM_JSON)
        assert len(result.shopping_intent) == 2
        assert result.shopping_intent[0].brand_preference == "Gloria"
        assert result.shopping_intent[1].price_sensitivity == Priority.HIGH

    def test_null_optional_fields_accepted(self):
        data = json.dumps({
            "shopping_intent": [{
                "raw_text": "detergente",
                "product_query": "detergente",
                "quantity": None,
                "unit": None,
                "brand_preference": None,
                "price_sensitivity": "medium",
                "allow_substitution": True,
            }]
        })
        item = _parse_intent(data).shopping_intent[0]
        assert item.quantity is None
        assert item.unit is None
        assert item.brand_preference is None

    def test_empty_intent_list(self):
        result = _parse_intent('{"shopping_intent": []}')
        assert result.shopping_intent == []

    def test_invalid_json_raises(self):
        with pytest.raises(IntentExtractionError, match="non-JSON"):
            _parse_intent("this is not json at all")

    def test_wrong_schema_raises(self):
        with pytest.raises(IntentExtractionError, match="schema"):
            _parse_intent('{"wrong_key": []}')

    def test_invalid_unit_raises(self):
        data = json.dumps({
            "shopping_intent": [{
                "raw_text": "arroz",
                "product_query": "arroz",
                "quantity": 5,
                "unit": "tonelada",  # not a valid QuantityUnit
                "brand_preference": None,
                "price_sensitivity": "medium",
                "allow_substitution": True,
            }]
        })
        with pytest.raises(IntentExtractionError):
            _parse_intent(data)

    def test_allow_substitution_false(self):
        data = json.dumps({
            "shopping_intent": [{
                "raw_text": "exactamente arroz",
                "product_query": "arroz",
                "quantity": 5,
                "unit": "kg",
                "brand_preference": None,
                "price_sensitivity": "medium",
                "allow_substitution": False,
            }]
        })
        item = _parse_intent(data).shopping_intent[0]
        assert item.allow_substitution is False


# ── IntentService (mocked LLM) ────────────────────────────────────────────────

class TestIntentService:
    async def test_extract_returns_valid_intent(self):
        service = _make_service(VALID_INTENT_JSON)
        result = await service.extract("Necesito 5 kg de arroz")
        assert isinstance(result, ShoppingIntent)
        assert result.shopping_intent[0].product_query == "arroz"

    async def test_extract_multi_item(self):
        service = _make_service(MULTI_ITEM_JSON)
        result = await service.extract("2 litros de leche Gloria y 1 detergente barato")
        assert len(result.shopping_intent) == 2

    async def test_extract_raises_on_non_json(self):
        service = _make_service("Aquí está tu lista de compras...")
        with pytest.raises(IntentExtractionError):
            await service.extract("necesito arroz")

    async def test_extract_raises_on_wrong_schema(self):
        service = _make_service('{"items": []}')
        with pytest.raises(IntentExtractionError):
            await service.extract("necesito arroz")

    async def test_llm_called_with_user_message(self):
        service = _make_service(VALID_INTENT_JSON)
        await service.extract("Necesito arroz")
        call_kwargs = service.client.chat.completions.create.call_args.kwargs
        messages = call_kwargs["messages"]
        user_turn = next(m for m in messages if m["role"] == "user")
        assert "Necesito arroz" in user_turn["content"]

    async def test_temperature_is_zero(self):
        service = _make_service(VALID_INTENT_JSON)
        await service.extract("arroz")
        call_kwargs = service.client.chat.completions.create.call_args.kwargs
        assert call_kwargs["temperature"] == 0


# ── POST /api/chat (endpoint integration) ────────────────────────────────────

class TestChatEndpoint:
    def _client_with_mock_service(self, json_response: str) -> TestClient:
        """Override get_intent_service dep so no real LLM is called."""
        mock_service = _make_service(json_response)
        app.dependency_overrides[get_intent_service] = lambda: mock_service
        return TestClient(app)

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_returns_200_with_intent(self):
        client = self._client_with_mock_service(VALID_INTENT_JSON)
        resp = client.post("/api/chat", json={"message": "Necesito arroz"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["intent"]["shopping_intent"][0]["product_query"] == "arroz"

    def test_cart_and_candidates_empty_without_scrapers(self):
        client = self._client_with_mock_service(VALID_INTENT_JSON)
        resp = client.post("/api/chat", json={"message": "Necesito arroz"})
        body = resp.json()
        assert body["cart"] is None
        assert body["candidate_products"] == {}

    def test_invalid_intent_returns_422(self):
        mock_service = _make_service("not json")
        app.dependency_overrides[get_intent_service] = lambda: mock_service
        client = TestClient(app)
        resp = client.post("/api/chat", json={"message": "arroz"})
        assert resp.status_code == 422

    def test_missing_message_returns_422(self):
        client = self._client_with_mock_service(VALID_INTENT_JSON)
        resp = client.post("/api/chat", json={})
        assert resp.status_code == 422

    def test_session_id_optional(self):
        client = self._client_with_mock_service(VALID_INTENT_JSON)
        resp = client.post("/api/chat", json={"message": "arroz", "session_id": "abc"})
        assert resp.status_code == 200
