from __future__ import annotations

from pydantic import BaseModel


class CompileSettings(BaseModel):
    """Compile-pipeline defaults. Loaded via Settings nesting (KEENYSPACE_COMPILE__*)."""

    debounce_seconds: int = 30
    backstop_interval_minutes: int = 15
    max_tool_calls: int = 20
    max_input_tokens: int = 50_000
    max_output_tokens: int = 20_000
    max_seconds: int = 180
    daily_token_ceiling: int = 500_000
    # Provider is pydantic-ai's provider id (anthropic | openai | google-gla | ...).
    # `model` is the bare model name; the agent joins them as "<provider>:<model>".
    # A fully-qualified `model` ("openai:gpt-4o") overrides `provider`. Anthropic
    # stays the default (D-04); other providers are opt-in via KEENYSPACE_COMPILE__*.
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-6"
