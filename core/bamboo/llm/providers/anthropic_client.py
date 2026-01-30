"""Anthropic LLM client implementation."""

from __future__ import annotations

from collections.abc import Sequence

from bamboo.llm.base import LLMClient
from bamboo.llm.exceptions import LLMProviderError
from bamboo.llm.types import GenerateParams, LLMResponse, Message


class AnthropicLLMClient(LLMClient):
    """Anthropic provider client (skeleton)."""

    async def generate(self, _messages: Sequence[Message], _params: GenerateParams) -> LLMResponse:
        try:
            return LLMResponse(text="[Anthropic not wired yet]")
        except Exception as exc:  # noqa: BLE001
            raise LLMProviderError(str(exc)) from exc
