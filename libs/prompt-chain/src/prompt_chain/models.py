"""Pydantic models for prompt_chain."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChainStep(BaseModel):
    """A single step in a prompt chain."""

    prompt_template: str
    output_key: str
    system_prompt: str | None = None


class LLMPayload(BaseModel):
    """Payload for the LLM API."""

    user: str
    system: str | None = None


class LLMResponse(BaseModel):
    """Parsed response from the LLM API."""

    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChainResult(BaseModel):
    """Accumulated result of running a full prompt chain."""

    outputs: dict[str, str] = Field(default_factory=dict)
    responses: list[LLMResponse] = Field(default_factory=list)

    @property
    def final_output(self) -> str:
        """Return the output of the last step."""
        if not self.responses:
            return ""
        return self.responses[-1].content
