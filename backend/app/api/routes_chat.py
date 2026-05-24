from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import get_intent_service
from app.models.cart_models import CartRecommendation
from app.models.intent_models import ShoppingIntent
from app.models.product_models import ProductCandidate
from app.services.intent_service import IntentExtractionError, IntentService

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
    service: IntentService = Depends(get_intent_service),
) -> ChatResponse:
    try:
        intent = await service.extract(request.message)
        return ChatResponse(intent=intent)
    except IntentExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
