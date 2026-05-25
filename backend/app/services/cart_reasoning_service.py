"""
Cart reasoning service (FR-011 / Phase 8).

Receives an already-built CartRecommendation and enriches it with LLM-generated
per-item explanations. The LLM also acts as a final validator: if the selected
product has an obvious mismatch with the user's request (wrong variant, wrong
category, completely unrelated product), it can request a swap to one of the
pre-ranked alternatives.

The LLM can only choose from candidates that already passed filtering and
ranking — it never invents products or prices.
"""

import json

from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from app.models.cart_models import CartItem, CartRecommendation
from app.models.intent_models import ShoppingIntent, ShoppingIntentItem
from app.models.product_models import ProductCandidate
from app.utils.logging_utils import get_logger
from app.utils.unit_parser import calculate_required_units

logger = get_logger(__name__)


class CartReasoningError(Exception):
    """Raised when the LLM response cannot be parsed into a valid CartReasonOutput."""


class CartReasonOutput(BaseModel):
    reasons: dict[str, str]
    swaps: dict[str, int] = {}  # product_query → 0-based index into alternatives list
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
            "alternatives": [
                {"index": i, "title": a.title, "store": a.store.value}
                for i, a in enumerate(cart_item.alternatives[:3])
            ],
        })

    summary = {
        "user_message": user_message,
        "cart": items,
        "total_estimated_cost": recommendation.total_estimated_cost,
        "warnings": recommendation.warnings,
    }
    return json.dumps(summary, ensure_ascii=False, indent=2)


def _rebuild_cart_item(
    original: CartItem,
    new_selected: ProductCandidate,
    remaining_alts: list[ProductCandidate],
    intent_item: ShoppingIntentItem | None,
) -> CartItem:
    """Promote a ranked alternative to selected product after an LLM-requested swap."""
    required_units = 1
    effective_qty = new_selected.quantity_value
    excess_qty = 0.0

    if intent_item and intent_item.quantity is not None and intent_item.unit is not None:
        result = calculate_required_units(
            intent_item.quantity,
            intent_item.unit,
            new_selected.quantity_value,
            new_selected.quantity_unit,
        )
        if result is not None:
            required_units, effective_qty, excess_qty = result

    return original.model_copy(update={
        "selected_product": new_selected.title,
        "store": new_selected.store,
        "unit_price": new_selected.unit_price,
        "product_quantity_value": new_selected.quantity_value,
        "product_quantity_unit": new_selected.quantity_unit,
        "required_units": required_units,
        "effective_quantity": effective_qty,
        "excess_quantity": excess_qty,
        "estimated_total": round(required_units * new_selected.price, 2),
        "product_url": new_selected.product_url,
        "alternatives": remaining_alts,
    })


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
        Validate selections, optionally swap to a ranked alternative, then add
        LLM-generated reasons. Returns a new CartRecommendation (original unchanged).
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
        query_to_intent = {item.product_query: item for item in intent.shopping_intent}

        enriched_cart: list[CartItem] = []
        total_delta = 0.0

        for cart_item in recommendation.cart:
            query = raw_to_query.get(cart_item.requested_item, cart_item.requested_item)

            # Apply swap if requested and the index is valid
            swap_idx = output.swaps.get(query)
            if swap_idx is not None and 0 <= swap_idx < len(cart_item.alternatives):
                old_product = cart_item.selected_product
                old_total = cart_item.estimated_total
                new_selected = cart_item.alternatives[swap_idx]
                remaining = [
                    a for i, a in enumerate(cart_item.alternatives) if i != swap_idx
                ]
                cart_item = _rebuild_cart_item(
                    cart_item, new_selected, remaining, query_to_intent.get(query)
                )
                total_delta += cart_item.estimated_total - old_total
                logger.info(
                    "LLM swapped '%s': %s → %s", query, old_product, cart_item.selected_product
                )

            reason = output.reasons.get(query, "")
            enriched_cart.append(cart_item.model_copy(update={"reason": reason}))

        new_total = round(recommendation.total_estimated_cost + total_delta, 2)

        return recommendation.model_copy(update={
            "cart": enriched_cart,
            "total_estimated_cost": new_total,
            "warnings": recommendation.warnings + output.warnings,
            "questions": recommendation.questions + output.questions,
        })
