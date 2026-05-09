from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastmcp.utilities.lifespan import combine_lifespans

from .api import health
from .mcp.server import build_mcp_skeleton


def build_app_skeleton() -> FastAPI:
    mcp = build_mcp_skeleton()
    mcp_app = mcp.http_app(path="/")

    @asynccontextmanager
    async def app_lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield

    app = FastAPI(
        title="KeenySpace-skeleton",
        lifespan=combine_lifespans(app_lifespan, mcp_app.lifespan),
    )

    app.include_router(health.router)
    app.mount("/v1/mcp", mcp_app)

    return app


app = build_app_skeleton()
