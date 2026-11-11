from __future__ import annotations

import os

from providers.openai_provider import OpenAIProvider


class GroqProvider(OpenAIProvider):
    """Groq via its OpenAI-compatible Chat Completions endpoint."""

    def __init__(self) -> None:
        super().__init__(
            api_key_env="GROQ_API_KEY",
            base_url=os.getenv("GROQ_BASE_URL") or "https://api.groq.com/openai/v1",
            default_model=os.getenv("GROQ_MODEL") or "openai/gpt-oss-120b",
        )
