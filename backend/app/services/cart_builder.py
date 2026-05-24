"""
Cart builder (FR-009).

Consumes ranked product candidates (one list per requested item) and
produces a CartRecommendation: selected product, required units,
estimated total, alternatives, and any overbuying warnings.
"""

from app.models.cart_models import CartItem, CartRecommendation
from app.models.intent_models import ShoppingIntent, ShoppingIntentItem
from app.models.preference_models import UserPreferences
from app.models.product_models import ProductCandidate
from app.utils.unit_parser import calculate_required_units, to_base_value

# Warn when the effective quantity exceeds the requested quantity by more than this fraction.
_OVERBUYING_THRESHOLD = 0.5  # 50 % excess


class CartBuilder:
    """Builds a CartRecommendation from ranked candidates."""

    def build(
        self,
        intent: ShoppingIntent,
        ranked_per_query: dict[str, list[ProductCandidate]],
        preferences: UserPreferences,
    ) -> CartRecommendation:
        """
        ranked_per_query maps product_query → already-ranked candidates.
        The first element of each list is the selected product.
        """
        cart: list[CartItem] = []
        warnings: list[str] = []

        for intent_item in intent.shopping_intent:
            candidates = ranked_per_query.get(intent_item.product_query, [])
            if not candidates:
                warnings.append(
                    f"No se encontraron productos para '{intent_item.product_query}'."
                )
                continue
            selected = candidates[0]
            alternatives = candidates[1:]
            cart_item = self._build_item(intent_item, selected, alternatives, warnings)
            cart.append(cart_item)

        total = round(sum(ci.estimated_total for ci in cart), 2)
        return CartRecommendation(
            cart=cart,
            total_estimated_cost=total,
            warnings=warnings,
        )

    # ── Private ───────────────────────────────────────────────────────────────

    def _build_item(
        self,
        intent_item: ShoppingIntentItem,
        selected: ProductCandidate,
        alternatives: list[ProductCandidate],
        warnings: list[str],
    ) -> CartItem:
        required_units, effective_qty, excess_qty = self._required_units(
            intent_item, selected, warnings
        )
        estimated_total = round(required_units * selected.price, 2)

        return CartItem(
            requested_item=intent_item.raw_text,
            selected_product=selected.title,
            store=selected.store,
            unit_price=selected.unit_price,
            product_quantity_value=selected.quantity_value,
            product_quantity_unit=selected.quantity_unit,
            required_units=required_units,
            effective_quantity=effective_qty,
            excess_quantity=excess_qty,
            estimated_total=estimated_total,
            product_url=selected.product_url,
            reason="",  # filled by LLM in Phase 8
            alternatives=alternatives,
        )

    def _required_units(
        self,
        intent_item: ShoppingIntentItem,
        selected: ProductCandidate,
        warnings: list[str],
    ) -> tuple[int, float, float]:
        """
        Return (required_units, effective_quantity, excess_quantity).
        Falls back to 1 unit when quantity/unit is unspecified or incompatible.
        """
        if intent_item.quantity is None or intent_item.unit is None:
            return 1, selected.quantity_value, 0.0

        result = calculate_required_units(
            intent_item.quantity,
            intent_item.unit,
            selected.quantity_value,
            selected.quantity_unit,
        )
        if result is None:
            # Units are incompatible (e.g. requested kg but product is in liters)
            warnings.append(
                f"No se pudo calcular unidades requeridas para '{selected.title}' "
                f"({intent_item.unit} vs {selected.quantity_unit}). Se asume 1 unidad."
            )
            return 1, selected.quantity_value, 0.0

        required_units, effective_base, excess_base = result

        # Overbuying warning
        req_base = to_base_value(intent_item.quantity, intent_item.unit)
        if req_base > 0 and excess_base / req_base > _OVERBUYING_THRESHOLD:
            warnings.append(
                f"'{selected.title}': se comprarán {effective_base:.0f} "
                f"(unidad base) pero solo se necesitan {req_base:.0f}. "
                f"Considera buscar una presentación más pequeña."
            )

        return required_units, effective_base, excess_base
