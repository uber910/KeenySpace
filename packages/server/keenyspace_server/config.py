from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict

from keenyspace_server.compile.settings import CompileSettings


class ServerSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    public_url: str = "http://localhost:8000"
    log_level: str = "INFO"


class DBSettings(BaseModel):
    url: str
    pool_size: int = 5
    pool_pre_ping: bool = True


class FSSettings(BaseModel):
    root: Path = Path("/var/lib/keenyspace")
    blueprints_dir: Path | None = None


class WALSettings(BaseModel):
    max_entry_bytes: int = 256 * 1024
    retention_days: int | None = None


class AuthSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    oidc_issuer_url: str
    oidc_client_id: str
    oidc_client_secret: str
    oidc_redirect_uri: str
    oidc_post_logout_redirect_uri: str

    session_secret_key: str
    cookie_path_ks_at: str = "/v1"
    cookie_path_ks_rt: str = "/v1/api/auth"
    cookie_samesite_ks_at: str = "lax"
    cookie_samesite_ks_rt: str = "strict"
    cookie_secure: bool = True

    # pepper защищает от offline rainbow-table при DB dump
    api_key_pepper: str

    jwks_ttl_seconds: int = 3600
    jwks_min_retry_interval_seconds: int = 30
    jwks_max_retry_interval_seconds: int = 300

    refresh_threshold_seconds: int = 60

    api_key_last_used_debounce_seconds: int = 300

    multi_worker: bool = False


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="KEENYSPACE_",
        env_nested_delimiter="__",
        case_sensitive=False,
        env_ignore_empty=True,
        extra="forbid",
    )

    server: ServerSettings = ServerSettings()
    db: DBSettings
    fs: FSSettings = FSSettings()
    wal: WALSettings = WALSettings()
    auth: AuthSettings
    compile: CompileSettings = CompileSettings()
    auto_migrate: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
