from pydantic import BaseModel, Field

from app.models.common import Priority, StoreId

ALL_STORES = [StoreId.PLAZA_VEA, StoreId.METRO, StoreId.VIVANDA, StoreId.TOTTUS]


class UserPreferences(BaseModel):
    price_priority: Priority = Priority.HIGH
    brand_priority: Priority = Priority.MEDIUM
    known_brands_only: bool = False
    allow_substitutions: bool = True
    allow_equivalent_sizes: bool = True
    preferred_stores: list[StoreId] = Field(default_factory=lambda: list(ALL_STORES))
    excluded_brands: list[str] = Field(default_factory=list)
    preferred_brands: list[str] = Field(default_factory=list)
    max_candidates_per_product: int = Field(default=5, ge=1, le=20)
