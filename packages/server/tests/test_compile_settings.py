from __future__ import annotations

import os
from unittest.mock import patch

from keenyspace_server.compile.settings import CompileSettings
from keenyspace_server.config import Settings


def test_compile_settings_defaults_match_d09() -> None:
    cs = CompileSettings()
    assert cs.debounce_seconds == 30
    assert cs.backstop_interval_minutes == 15
    assert cs.max_tool_calls == 20
    assert cs.max_input_tokens == 50_000
    assert cs.max_output_tokens == 20_000
    assert cs.max_seconds == 180
    assert cs.daily_token_ceiling == 500_000
    assert cs.model == "claude-sonnet-4-6"
    assert not hasattr(cs, "temperature")


def test_settings_compile_field_loads_env() -> None:
    env = {
        "KEENYSPACE_DB__URL": "postgresql+asyncpg://x:x@localhost/x",
        "KEENYSPACE_COMPILE__MODEL": "claude-opus-4-7",
        "KEENYSPACE_COMPILE__MAX_TOOL_CALLS": "10",
    }
    with patch.dict(os.environ, env, clear=True):
        s = Settings()  # type: ignore[call-arg]
        assert s.compile.model == "claude-opus-4-7"
        assert s.compile.max_tool_calls == 10
        assert s.compile.daily_token_ceiling == 500_000
