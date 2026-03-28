"""Prompt chaining engine."""

from __future__ import annotations

import logging

from prompt_chain.client import LLMClient
from prompt_chain.models import ChainResult, ChainStep, LLMPayload

logger = logging.getLogger(__name__)


class PromptChain:
    """Sequential prompt chain that pipes outputs between steps.

    Each step's ``prompt_template`` may contain ``{variable}`` placeholders
    that are resolved from prior step outputs or the initial variables
    passed to ``run()``.

    Example::

        chain = PromptChain(client)
        chain.add_step(
            prompt_template="Summarize: {text}",
            output_key="summary",
        )
        chain.add_step(
            prompt_template="Extract keywords from: {summary}",
            output_key="keywords",
        )
        result = chain.run({"text": "..."})
        print(result.outputs["keywords"])
    """

    def __init__(self, client: LLMClient) -> None:
        self._client = client
        self._steps: list[ChainStep] = []

    def add_step(
        self,
        prompt_template: str,
        output_key: str,
        system_prompt: str | None = None,
    ) -> PromptChain:
        """Register a new step in the chain.

        Args:
            prompt_template: Prompt with ``{var}`` placeholders.
            output_key: Key under which the step's output is stored.
            system_prompt: Optional system message for this step.

        Returns:
            ``self`` for fluent chaining.
        """
        self._steps.append(
            ChainStep(
                prompt_template=prompt_template,
                output_key=output_key,
                system_prompt=system_prompt,
            )
        )
        return self

    def run(self, initial_vars: dict[str, str] | None = None) -> ChainResult:
        """Execute all steps sequentially.

        Args:
            initial_vars: Starting variables available to the first step's
                template (and all subsequent steps).

        Returns:
            A ``ChainResult`` containing every step's output and raw
            responses.
        """
        variables: dict[str, str] = dict(initial_vars or {})
        result = ChainResult()

        for i, step in enumerate(self._steps):
            logger.info(
                "Running step %d/%d (key=%s)", i + 1, len(self._steps), step.output_key
            )

            prompt = step.prompt_template.format(**variables)

            response = self._client.generate(
                LLMPayload(
                    user=prompt,
                    system=step.system_prompt,
                )
            )

            variables[step.output_key] = response.content
            result.outputs[step.output_key] = response.content
            result.responses.append(response)

            logger.debug(
                "Step %d output (%s): %s",
                i + 1,
                step.output_key,
                response.content[:200],
            )

        return result

    def clear(self) -> None:
        """Remove all registered steps."""
        self._steps.clear()

    @property
    def steps(self) -> list[ChainStep]:
        """Return a copy of the current steps."""
        return list(self._steps)
