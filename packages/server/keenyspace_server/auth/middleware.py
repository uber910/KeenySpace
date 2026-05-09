from __future__ import annotations

from starlette.requests import HTTPConnection
from starlette.responses import JSONResponse


def on_auth_error(conn: HTTPConnection, exc: Exception) -> JSONResponse:
    return JSONResponse({"error": str(exc)}, status_code=401)
