from pydantic import BaseModel

from app.models.common import Priority, QuantityUnit


class ShoppingIntentItem(BaseModel):
    raw_text: str
    product_query: str
    quantity: float | None = None
    unit: QuantityUnit | None = None
    brand_preference: str | None = None
    price_sensitivity: Priority = Priority.MEDIUM
    allow_substitution: bool = True


class ShoppingIntent(BaseModel):
    shopping_intent: list[ShoppingIntentItem]
