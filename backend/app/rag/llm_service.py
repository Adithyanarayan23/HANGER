from typing import List, Optional

from google import genai
from google.genai import types

from app.core.config import settings
from app.rag.prompt_templates import (
    SYSTEM_INSTRUCTION,
    build_grounded_recommendation_prompt,
)
from app.rag.vector_store import RetrievedProductMatch


class LLMServiceError(RuntimeError):
    """Raised when the Gemini generation service is unconfigured or fails."""
    pass


class GeminiLLMService:
    """
    Generates grounded natural-language product explanations using the official
    google-genai SDK. Never fabricates product cards, prices, or URLs.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        client: Optional[object] = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model_name: str = model_name or settings.GEMINI_GENERATION_MODEL
        self._client = client

    def _get_client(self) -> genai.Client:
        if self._client is not None:
            return self._client
        key = (self._api_key or "").strip()
        if not key:
            raise LLMServiceError(
                "GEMINI_API_KEY is not configured. Cannot generate AI explanation."
            )
        self._client = genai.Client(api_key=key)
        return self._client

    def generate_explanation(
        self,
        user_query: str,
        retrieved_matches: List[RetrievedProductMatch],
    ) -> str:
        """
        Build a grounded prompt from the retrieved database records and generate
        a concise explanation from Gemini.
        """
        if not retrieved_matches:
            return "No matching products were found in the catalogue for your search criteria."

        prompt = build_grounded_recommendation_prompt(
            user_query=user_query,
            retrieved_matches=retrieved_matches,
        )
        client = self._get_client()

        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.2,
                    max_output_tokens=300,
                ),
            )
        except Exception as exc:
            raise LLMServiceError(
                f"Gemini text generation failed ({type(exc).__name__})."
            ) from exc

        text = getattr(response, "text", None)
        if not text or not text.strip():
            raise LLMServiceError("Gemini returned an empty generation response.")

        return text.strip()
