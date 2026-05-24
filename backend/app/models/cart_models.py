from pydantic import BaseModel, Field

from app.models.common import QuantityUnit, StoreId
from app.models.product_models import ProductCandidate


class CartItem(BaseModel):
    requested_item: str
    selected_product: str
    store: StoreId
    unit_price: float
    product_quantity_value: float
    product_quantity_unit: QuantityUnit
    required_units: int = Field(ge=1)
    effective_quantity: float
    excess_quantity: float = 0.0
    estimated_total: float
    product_url: str
    reason: str
    alternatives: list[ProductCandidate] = Field(default_factory=list)


class CartRecommendation(BaseModel):
    cart: list[CartItem]
    total_estimated_cost: float
    warnings: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
