"""
Cart reasoning service (FR-011 / Phase 8).

Receives an already-built CartRecommendation and enriches it with LLM-generated
per-item explanations (reason field), plus optional extra warnings and questions.
The LLM only explains; all product selection is already done deterministically.
"""

import json

from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from app.models.cart_models import CartRecommendation
from app.models.intent_models import ShoppingIntent
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)


class CartReasoningError(Exception):
    """Raised when the LLM response cannot be parsed into a valid CartReasonOutput."""


class CartReasonOutput(BaseModel):
    reasons: dict[str, str]
    warnings: list[str] = []
    questions: list[str] = []


def _parse_reason_output(raw: str) -> CartReasonOutput:
    """Parse and validate a raw JSON string from the LLM into CartReasonOutput."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CartReasoningError(f"LLM returned non-JSON: {exc}") from exc

    try:
        return CartReasonOutput.model_validate(data)
    except ValidationError as exc:
        raise CartReasoningError(f"LLM JSON does not match schema: {exc}") from exc


def _build_cart_summary(
    recommendation: CartRecommendation,
    intent: ShoppingIntent,
    user_message: str,
) -> str:
    """Build a compact JSON description of the cart to send to the LLM."""
    raw_to_query = {item.raw_text: item.product_query for item in intent.shopping_intent}

    items = []
    for cart_item in recommendation.cart:
        product_query = raw_to_query.get(cart_item.requested_item, cart_item.requested_item)
        items.append({
            "product_query": product_query,
            "requested": cart_item.requested_item,
            "selected": cart_item.selected_product,
            "store": cart_item.store.value,
            "unit_price": cart_item.unit_price,
            "required_units": cart_item.required_units,
            "estimated_total": cart_item.estimated_total,
            "alternatives": [a.title for a in cart_item.alternatives[:3]],
        })

    summary = {
        "user_message": user_message,
        "cart": items,
        "total_estimated_cost": recommendation.total_estimated_cost,
        "warnings": recommendation.warnings,
    }
    return json.dumps(summary, ensure_ascii=False, indent=2)


class CartReasoningService:
    def __init__(self, client: AsyncOpenAI, model: str, system_prompt: str) -> None:
        self.client = client
        self.model = model
        self.system_prompt = system_prompt

    async def enrich(
        self,
        recommendation: CartRecommendation,
        intent: ShoppingIntent,
        user_message: str,
    ) -> CartRecommendation:
        """
        Add LLM-generated reasons to each CartItem and merge extra warnings/questions.
        Returns a new CartRecommendation (original is not mutated).
        """
        if not recommendation.cart:
            return recommendation

        logger.debug("Enriching cart with %d items", len(recommendation.cart))

        cart_summary = _build_cart_summary(recommendation, intent, user_message)
        response = await self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": cart_summary},
            ],
            temperature=0,
        )

        raw = response.choices[0].message.content or ""
        logger.debug("LLM raw response: %.200s", raw)

        output = _parse_reason_output(raw)

        raw_to_query = {item.raw_text: item.product_query for item in intent.shopping_intent}
        enriched_cart = []
        for cart_item in recommendation.cart:
            query = raw_to_query.get(cart_item.requested_item, cart_item.requested_item)
            reason = output.reasons.get(query, "")
            enriched_cart.append(cart_item.model_copy(update={"reason": reason}))

        return recommendation.model_copy(update={
            "cart": enriched_cart,
            "warnings": recommendation.warnings + output.warnings,
            "questions": recommendation.questions + output.questions,
        })
