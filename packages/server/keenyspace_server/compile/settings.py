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
    model: str = "claude-sonnet-4-6"
