# prompt-chain

A shared library for LLM prompt chaining. Provides a simple API to send prompts to OpenAI-compatible endpoints and compose multi-step pipelines where each step's output feeds into the next.

## Installation

```bash
pip install -e ../../libs/prompt-chain
```

## Quick Start

```python
from prompt_chain import LLMClient, PromptChain

client = LLMClient(api_key="sk-...", model="gpt-4o")

chain = PromptChain(client)
chain.add_step(prompt_template="Summarize: {text}", output_key="summary")
chain.add_step(prompt_template="Key takeaways from: {summary}", output_key="takeaways")

result = chain.run({"text": "Your long text here..."})
print(result.outputs["takeaways"])
```

## Configuration

Set these environment variables (or pass directly to `LLMClient`):

| Variable | Default | Description |
|---|---|---|
| `LLM_BASE_URL` | `https://api.openai.com/v1` | API base URL |
| `LLM_API_KEY` | — | API key |
| `LLM_MODEL` | `gpt-4o` | Model name |
| `LLM_TEMPERATURE` | `0.7` | Sampling temperature |
| `LLM_MAX_TOKENS` | `2048` | Max response tokens |
