from pydantic import BaseModel

from app.models.common import StoreId


class CandidateDebug(BaseModel):
    title: str
    store: StoreId
    brand: str | None = None
    price: float
    unit_price: float
    # Filtering component scores
    filter_title: float
    filter_brand: float
    filter_category: float
    filter_unit: float
    filter_score: float
    # Ranking component scores
    rank_relevance: float
    rank_price: float
    rank_unit: float
    rank_brand: float
    rank_store: float
    rank_final: float


class QueryDebug(BaseModel):
    query: str
    scraped_total: int
    scraped_per_store: dict[str, int]
    passed_filter: int
    candidates: list[CandidateDebug]


class PipelineDebug(BaseModel):
    queries: list[QueryDebug]
