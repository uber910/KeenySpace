"""Split-horizon issuer — public oidc_issuer_url (token `iss`, client-facing)
vs internal metadata_issuer_url (server back-channel for discovery + JWKS).

Lets the host CLI + token `iss` use http://localhost:9000/... while the
server, in a container, fetches JWKS from http://authentik:9000/... — so dev
login works without an /etc/hosts entry for `authentik`.
"""

from __future__ import annotations

from keenyspace_server.auth.oidc import build_oauth
from keenyspace_server.config import AuthSettings, Settings


def _auth(**overrides: object) -> AuthSettings:
    base: dict[str, object] = {
        "oidc_issuer_url": "http://localhost:9000/application/o/keenyspace/",
        "oidc_client_id": "keenyspace-cli",
        "oidc_client_secret": "secret",
        "oidc_redirect_uri": "http://localhost:8000/v1/api/auth/callback",
        "oidc_post_logout_redirect_uri": "http://localhost:8000/",
        "session_secret_key": "session-secret-32chars-padded-here!",
        "api_key_pepper": "pepper-32chars-padded-here-xxxxx!",
    }
    base.update(overrides)
    return AuthSettings(**base)  # type: ignore[arg-type]


def test_metadata_issuer_defaults_to_public_issuer() -> None:
    auth = _auth()
    assert auth.oidc_internal_issuer_url is None
    assert auth.metadata_issuer_url == auth.oidc_issuer_url


def test_metadata_issuer_uses_internal_when_set() -> None:
    auth = _auth(
        oidc_internal_issuer_url="http://authentik:9000/application/o/keenyspace/",
    )
    # Public issuer (what lands in the token `iss`) stays localhost...
    assert auth.oidc_issuer_url == "http://localhost:9000/application/o/keenyspace/"
    # ...while the back-channel metadata/JWKS fetch targets the internal host.
    assert auth.metadata_issuer_url == "http://authentik:9000/application/o/keenyspace/"


def test_build_oauth_fetches_metadata_from_internal_issuer(monkeypatch) -> None:
    for key, value in {
        "KEENYSPACE_DB__URL": "postgresql+asyncpg://x:y@localhost:5432/z",
        "KEENYSPACE_FS__ROOT": "/tmp/ks-split-issuer-test",
        "KEENYSPACE_AUTH__OIDC_ISSUER_URL": "http://localhost:9000/application/o/keenyspace/",
        "KEENYSPACE_AUTH__OIDC_INTERNAL_ISSUER_URL": "http://authentik:9000/application/o/keenyspace/",
        "KEENYSPACE_AUTH__OIDC_CLIENT_ID": "keenyspace-cli",
        "KEENYSPACE_AUTH__OIDC_CLIENT_SECRET": "secret",
        "KEENYSPACE_AUTH__OIDC_REDIRECT_URI": "http://localhost:8000/v1/api/auth/callback",
        "KEENYSPACE_AUTH__OIDC_POST_LOGOUT_REDIRECT_URI": "http://localhost:8000/",
        "KEENYSPACE_AUTH__SESSION_SECRET_KEY": "session-secret-32chars-padded-he!",
        "KEENYSPACE_AUTH__API_KEY_PEPPER": "pepper-32chars-padded-here-xxxxx!",
    }.items():
        monkeypatch.setenv(key, value)

    settings = Settings()  # type: ignore[call-arg]
    oauth = build_oauth(settings)
    _, register_kwargs = oauth._registry["authentik"]
    assert (
        register_kwargs["server_metadata_url"]
        == "http://authentik:9000/application/o/keenyspace/.well-known/openid-configuration"
    )
