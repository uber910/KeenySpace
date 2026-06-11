from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from starlette.authentication import BaseUser


@dataclass
class User(BaseUser):
    sub: str
    _display_name: str
    source: Literal["oidc", "api_key"]
    groups: list[str] = field(default_factory=list)

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def identity(self) -> str:
        return self.sub
