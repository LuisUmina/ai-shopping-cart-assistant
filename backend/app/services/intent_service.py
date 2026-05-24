import json

from openai import AsyncOpenAI
from pydantic import ValidationError

from app.models.intent_models import ShoppingIntent
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)


class IntentExtractionError(Exception):
    """Raised when the LLM response cannot be parsed into a valid ShoppingIntent."""


def _parse_intent(raw: str) -> ShoppingIntent:
    """Parse and validate a raw JSON string from the LLM into ShoppingIntent."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise IntentExtractionError(f"LLM returned non-JSON: {exc}") from exc

    try:
        return ShoppingIntent.model_validate(data)
    except ValidationError as exc:
        raise IntentExtractionError(f"LLM JSON does not match schema: {exc}") from exc


class IntentService:
    def __init__(self, client: AsyncOpenAI, model: str, system_prompt: str) -> None:
        self.client = client
        self.model = model
        self.system_prompt = system_prompt

    async def extract(self, message: str) -> ShoppingIntent:
        """
        Send the user message to the LLM and return a validated ShoppingIntent.

        Raises IntentExtractionError if the response cannot be parsed or validated.
        """
        logger.debug("Extracting intent for message: %.80s", message)

        response = await self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": message},
            ],
            temperature=0,
        )

        raw = response.choices[0].message.content or ""
        logger.debug("LLM raw response: %.200s", raw)

        intent = _parse_intent(raw)
        logger.info("Extracted %d intent items", len(intent.shopping_intent))
        return intent
