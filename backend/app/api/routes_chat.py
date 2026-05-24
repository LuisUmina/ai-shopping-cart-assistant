from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import (
    get_cart_builder,
    get_cart_reasoning_service,
    get_filtering_service,
    get_intent_service,
    get_ranking_service,
    get_scraping_service,
)
from app.models.cart_models import CartRecommendation
from app.models.intent_models import ShoppingIntent
from app.models.product_models import ProductCandidate
from app.services.cart_builder import CartBuilder
from app.services.cart_reasoning_service import CartReasoningError, CartReasoningService
from app.services.filtering_service import FilteringService
from app.services.intent_service import IntentExtractionError, IntentService
from app.services.preferences_store import load_preferences
from app.services.ranking_service import RankingService
from app.services.scraping_service import ScrapingService
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    intent: ShoppingIntent | None = None
    cart: CartRecommendation | None = None
    candidate_products: dict[str, list[ProductCandidate]] = {}
    warnings: list[str] = []


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    intent_service: IntentService = Depends(get_intent_service),
    scraping_service: ScrapingService = Depends(get_scraping_service),
    filtering_service: FilteringService = Depends(get_filtering_service),
    ranking_service: RankingService = Depends(get_ranking_service),
    cart_builder: CartBuilder = Depends(get_cart_builder),
    reasoning_service: CartReasoningService = Depends(get_cart_reasoning_service),
) -> ChatResponse:
    # 1. Extract structured intent
    try:
        intent = await intent_service.extract(request.message)
    except IntentExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if not intent.shopping_intent:
        return ChatResponse(intent=intent)

    # 2. Load user preferences
    preferences = load_preferences()

    # 3. Scrape preferred stores in parallel
    queries = [item.product_query for item in intent.shopping_intent]
    raw_results = await scraping_service.search(queries, preferences.preferred_stores)

    # 4. Filter + rank per requested item
    ranked_per_query: dict[str, list[ProductCandidate]] = {}
    for item in intent.shopping_intent:
        candidates = raw_results.get(item.product_query, [])
        filtered = filtering_service.filter(candidates, item, preferences)
        ranked_per_query[item.product_query] = ranking_service.rank(
            filtered, item, preferences
        )

    # 5. Build the cart
    recommendation = cart_builder.build(intent, ranked_per_query, preferences)

    # 6. LLM reasoning — best-effort; cart is still returned if it fails
    try:
        recommendation = await reasoning_service.enrich(
            recommendation, intent, request.message
        )
    except CartReasoningError as exc:
        logger.warning("Cart reasoning failed: %s", exc)
        recommendation = recommendation.model_copy(update={
            "warnings": recommendation.warnings
            + ["No se pudo generar la explicación del carrito."]
        })

    return ChatResponse(
        intent=intent,
        cart=recommendation,
        candidate_products=ranked_per_query,
        warnings=recommendation.warnings,
    )
