from functools import lru_cache
from pathlib import Path

from fastapi import Depends
from openai import AsyncOpenAI

from app.config import Settings, get_settings
from app.services.intent_service import IntentService

_PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


@lru_cache(maxsize=8)
def _load_prompt(filename: str) -> str:
    return (_PROMPTS_DIR / filename).read_text(encoding="utf-8")


def get_intent_service(settings: Settings = Depends(get_settings)) -> IntentService:
    llm = settings.active_llm()
    client = AsyncOpenAI(api_key=llm.api_key, base_url=llm.base_url)
    return IntentService(
        client=client,
        model=llm.model,
        system_prompt=_load_prompt("intent_extraction_prompt.md"),
    )
