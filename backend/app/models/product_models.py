from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.common import Availability, QuantityUnit, StoreId


class ProductConfidence(BaseModel):
    brand_extraction: float = 1.0
    quantity_extraction: float = 1.0
    price_extraction: float = 1.0


class ProductCandidate(BaseModel):
    store: StoreId
    product_id: str | None = None
    title: str
    brand: str | None = None
    category: str | None = None
    raw_price: str | None = None
    price: float
    currency: str = "PEN"
    presentation_text: str
    quantity_value: float
    quantity_unit: QuantityUnit
    unit_price: float
    unit_price_unit: QuantityUnit | None = None
    availability: Availability = Availability.AVAILABLE
    image_url: str | None = None
    product_url: str
    search_query: str
    scraped_at: datetime
    confidence: ProductConfidence = Field(default_factory=ProductConfidence)

    @field_validator("price", "unit_price", "quantity_value")
    @classmethod
    def must_be_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError("must be >= 0")
        return v
