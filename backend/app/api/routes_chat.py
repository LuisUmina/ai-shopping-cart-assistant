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
from app.models.debug_models import CandidateDebug, PipelineDebug, QueryDebug
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
    pipeline_debug: PipelineDebug | None = None


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

    # Build pipeline debug data (additive — does not affect the pipeline above)
    query_debugs: list[QueryDebug] = []
    for item in intent.shopping_intent:
        raw = raw_results.get(item.product_query, [])
        ranked = ranked_per_query[item.product_query]

        scraped_per_store: dict[str, int] = {}
        for c in raw:
            scraped_per_store[c.store.value] = scraped_per_store.get(c.store.value, 0) + 1

        candidates_debug: list[CandidateDebug] = []
        for c in ranked:
            fs = filtering_service.score_breakdown(c, item, preferences)
            rs = ranking_service.score_breakdown(c, item, preferences, ranked)
            candidates_debug.append(CandidateDebug(
                title=c.title,
                store=c.store,
                brand=c.brand,
                price=round(c.price, 2),
                unit_price=round(c.unit_price, 4),
                filter_title=round(fs["title"], 3),
                filter_brand=round(fs["brand"], 3),
                filter_category=round(fs["category"], 3),
                filter_unit=round(fs["unit"], 3),
                filter_score=round(fs["final"], 3),
                rank_relevance=round(rs["relevance"], 3),
                rank_price=round(rs["price"], 3),
                rank_unit=round(rs["unit"], 3),
                rank_brand=round(rs["brand"], 3),
                rank_store=round(rs["store"], 3),
                rank_final=round(rs["final"], 3),
            ))

        query_debugs.append(QueryDebug(
            query=item.product_query,
            scraped_total=len(raw),
            scraped_per_store=scraped_per_store,
            passed_filter=len(ranked),
            candidates=candidates_debug,
        ))

    # Warnings live inside cart.warnings — don't duplicate them at the top level.
    # ChatResponse.warnings is reserved for pipeline-level issues (e.g. a store
    # that was completely unreachable), not product-level cart warnings.
    return ChatResponse(
        intent=intent,
        cart=recommendation,
        candidate_products=ranked_per_query,
        pipeline_debug=PipelineDebug(queries=query_debugs),
    )
