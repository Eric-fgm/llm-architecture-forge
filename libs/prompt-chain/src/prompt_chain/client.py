"""LLM client for chat completions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

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
        input_messages: list[Any] = [
            {
                "role": "user",
                "content": payload.user,
            }
        ]
        if payload.system is not None:
            input_messages.append(
                {
                    "role": "model",
                    "content": payload.system,
                },
            )

        interaction = self._client.interactions.create(
            model=self._model,
            previous_interaction_id=omit_none(self._previous_interaction_id),
            store=False,
            input=input_messages,
        )
        self._previous_interaction_id = interaction.id

        return self._parse_interaction(interaction)

    def _parse_interaction(self, data: Any) -> LLMResponse:
        """Extract an LLMResponse from the raw API JSON."""
        return LLMResponse(
            content=data.outputs[-1].text,
            model=data.model,
            prompt_tokens=data.usage.total_input_tokens,
            completion_tokens=data.usage.total_output_tokens,
            total_tokens=data.usage.total_tokens,
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
