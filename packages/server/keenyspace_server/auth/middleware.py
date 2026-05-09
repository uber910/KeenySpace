from __future__ import annotations

from starlette.requests import Request
from starlette.responses import JSONResponse


async def on_auth_error(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse({"error": str(exc)}, status_code=401)
