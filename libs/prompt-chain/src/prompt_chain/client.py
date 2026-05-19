"""LLM client for chat completions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import anthropic
from google import genai
from openai import OpenAI
from openai._types import NOT_GIVEN

from prompt_chain.models import LLMPayload, LLMResponse


class LLMClient(ABC):
    """Interface for LLM clients."""

    @abstractmethod
    def generate(
        self,
        payload: LLMPayload,
    ) -> LLMResponse:
        pass


class GeminiClient(LLMClient):
    """LLM client for Gemini."""

    """ID of the previous interaction to enable conversation history."""
    _previous_interaction_id: str | None = None

    def __init__(
        self,
        api_key: str,
        model: str,
    ) -> None:
        self._model = model
        self._client = genai.Client(api_key=api_key)

    def generate(
        self,
        payload: LLMPayload,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "store": False,
            "input": payload.user,
        }
        if payload.system is not None:
            kwargs["system_instruction"] = payload.system
        if self._previous_interaction_id is not None:
            kwargs["previous_interaction_id"] = self._previous_interaction_id

        interaction = self._client.interactions.create(**kwargs)
        self._previous_interaction_id = interaction.id

        return self._parse_interaction(interaction)

    def _parse_interaction(self, data: Any) -> LLMResponse:
        """Extract an LLMResponse from the raw API JSON."""
        usage = data.usage
        return LLMResponse(
            content=data.output_text,
            model=data.model or self._model,
            prompt_tokens=usage.total_input_tokens
            if usage and usage.total_input_tokens
            else 0,
            completion_tokens=usage.total_output_tokens
            if usage and usage.total_output_tokens
            else 0,
            total_tokens=usage.total_tokens if usage and usage.total_tokens else 0,
        )


class ClaudeClient(LLMClient):
    """LLM client for Anthropic Claude."""

    """Previous messages to enable conversation history."""
    _conversation_history: list[dict[str, str]]

    def __init__(
        self,
        api_key: str,
        model: str,
        max_tokens: int = 16384,
    ) -> None:
        self._model = model
        self._max_tokens = max_tokens
        self._client = anthropic.Anthropic(api_key=api_key)
        self._conversation_history = []

    def generate(
        self,
        payload: LLMPayload,
    ) -> LLMResponse:
        self._conversation_history.append({"role": "user", "content": payload.user})

        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "messages": self._conversation_history,
        }
        if payload.system is not None:
            kwargs["system"] = payload.system

        message = self._client.messages.create(**kwargs)

        assistant_text = message.content[0].text
        self._conversation_history.append(
            {"role": "assistant", "content": assistant_text}
        )

        return self._parse_message(message)

    def _parse_message(self, data: Any) -> LLMResponse:
        """Extract an LLMResponse from the raw API response."""
        usage = data.usage
        return LLMResponse(
            content=data.content[0].text,
            model=data.model,
            prompt_tokens=usage.input_tokens,
            completion_tokens=usage.output_tokens,
            total_tokens=usage.input_tokens + usage.output_tokens,
        )


class OpenAIClient(LLMClient):
    """LLM client for OpenAI."""

    """ID of the previous response to enable conversation history."""
    _previous_response_id: str | None = None

    def __init__(
        self,
        api_key: str,
        model: str,
    ) -> None:
        self._model = model
        self._client = OpenAI(api_key=api_key)

    def generate(
        self,
        payload: LLMPayload,
    ) -> LLMResponse:
        input_messages: list[Any] = [
            {
                "role": "user",
                "content": payload.user,
            }
        ]
        if payload.system is not None:
            input_messages.append(
                {
                    "role": "developer",
                    "content": payload.system,
                },
            )

        response = self._client.responses.create(
            model=self._model,
            previous_response_id=omit_none(self._previous_response_id),
            store=False,
            input=input_messages,
        )
        self._previous_response_id = response.id

        return self._parse_response(response)

    def _parse_response(self, data: Any) -> LLMResponse:
        """Extract an LLMResponse from the raw API JSON."""
        return LLMResponse(
            content=data.output_text[0].content[0].text,
            model=data.model,
            prompt_tokens=data.usage.input_tokens,
            completion_tokens=data.usage.output_tokens,
            total_tokens=data.usage.total_tokens,
        )


def omit_none(value: Any) -> Any:
    return value if value is not None else NOT_GIVEN
