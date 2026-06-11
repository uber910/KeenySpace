"""D-05 group entry gate in CompositeAuthBackend.authenticate.

Five test cases exercise the OIDC-only group gate (D-15):
  1. OIDC user in required group -> admitted.
  2. OIDC user not in required group -> AuthenticationError.
  3. api_key user bypasses gate regardless of groups (D-15).
  4. Empty required_group disables the gate.
  5. Error message does not leak the group name (ASVS V7).
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from keenyspace_server.auth.composite import CompositeAuthBackend
from keenyspace_server.auth.user import User
from starlette.authentication import AuthenticationError
from starlette.requests import HTTPConnection


def _conn(path: str, headers: dict[str, str] | None = None) -> HTTPConnection:
    raw_headers = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    scope = {
        "type": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": raw_headers,
        "scheme": "http",
        "server": ("test", 80),
    }
    return HTTPConnection(scope)


@pytest.mark.asyncio
async def test_oidc_user_in_required_group_passes() -> None:
    user = User(sub="u", _display_name="u", source="oidc", groups=["keenyspace-users"])
    fake_keys = AsyncMock()
    backend = CompositeAuthBackend(
        oidc_client=None,
        api_key_service=fake_keys,
        required_group="keenyspace-users",
    )
    backend._try_oidc_bearer = AsyncMock(return_value=user)  # type: ignore[method-assign]
    backend._try_api_key = AsyncMock(return_value=None)  # type: ignore[method-assign]

    result = await backend.authenticate(_conn("/v1/api/workspaces/"))
    assert result is not None
    creds, returned_user = result
    assert "authenticated" in creds.scopes
    assert returned_user.sub == "u"


@pytest.mark.asyncio
async def test_oidc_user_not_in_required_group_raises() -> None:
    user = User(sub="u", _display_name="u", source="oidc", groups=[])
    fake_keys = AsyncMock()
    backend = CompositeAuthBackend(
        oidc_client=None,
        api_key_service=fake_keys,
        required_group="keenyspace-users",
    )
    backend._try_oidc_bearer = AsyncMock(return_value=user)  # type: ignore[method-assign]
    backend._try_api_key = AsyncMock(return_value=None)  # type: ignore[method-assign]

    with pytest.raises(AuthenticationError):
        await backend.authenticate(_conn("/v1/api/workspaces/"))


@pytest.mark.asyncio
async def test_api_key_user_bypasses_group_gate() -> None:
    user = User(sub="u", _display_name="u", source="api_key", groups=[])
    fake_keys = AsyncMock()
    backend = CompositeAuthBackend(
        oidc_client=None,
        api_key_service=fake_keys,
        required_group="keenyspace-users",
    )
    backend._try_api_key = AsyncMock(return_value=user)  # type: ignore[method-assign]

    result = await backend.authenticate(_conn("/v1/api/workspaces/"))
    assert result is not None
    creds, _ = result
    assert "authenticated" in creds.scopes


@pytest.mark.asyncio
async def test_group_gate_disabled_when_empty_string() -> None:
    user = User(sub="u", _display_name="u", source="oidc", groups=[])
    fake_keys = AsyncMock()
    backend = CompositeAuthBackend(
        oidc_client=None,
        api_key_service=fake_keys,
        required_group="",
    )
    backend._try_oidc_bearer = AsyncMock(return_value=user)  # type: ignore[method-assign]
    backend._try_api_key = AsyncMock(return_value=None)  # type: ignore[method-assign]

    result = await backend.authenticate(_conn("/v1/api/workspaces/"))
    assert result is not None


@pytest.mark.asyncio
async def test_group_gate_error_message_does_not_leak_group_name() -> None:
    user = User(sub="u", _display_name="u", source="oidc", groups=[])
    fake_keys = AsyncMock()
    backend = CompositeAuthBackend(
        oidc_client=None,
        api_key_service=fake_keys,
        required_group="keenyspace-users",
    )
    backend._try_oidc_bearer = AsyncMock(return_value=user)  # type: ignore[method-assign]
    backend._try_api_key = AsyncMock(return_value=None)  # type: ignore[method-assign]

    with pytest.raises(AuthenticationError) as exc_info:
        await backend.authenticate(_conn("/v1/api/workspaces/"))

    assert str(exc_info.value) == "forbidden"
    assert "keenyspace-users" not in str(exc_info.value)
