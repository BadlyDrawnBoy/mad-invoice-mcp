"""Minimal OpenWebUI shim (placeholder)."""
from __future__ import annotations

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route


def build_openwebui_shim(upstream_base: str, extra_routes=()):
    async def openapi(_: object):
        return JSONResponse({"openapi": "3.1.0", "info": {"title": "mad-invoice-mcp", "version": "0.0.0"}})

    routes = [Route("/openapi.json", openapi, methods=["GET"])]
    routes.extend(extra_routes)
    return Starlette(routes=routes)


__all__ = ["build_openwebui_shim"]
