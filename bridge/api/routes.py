"""HTTP route definitions for the MCP server."""
from __future__ import annotations

from typing import List

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from .envelopes import envelope_ok


async def ping(_: Request) -> JSONResponse:
    """Return a deterministic ping response."""

    return JSONResponse(envelope_ok({"pong": True}))


async def version(_: Request) -> JSONResponse:
    """Expose a placeholder semantic version for the template."""

    return JSONResponse(envelope_ok({"version": "0.0.0"}))


def make_routes() -> List[Route]:
    """Construct the public HTTP routes for the server."""

    return [
        Route("/api/ping.json", ping, methods=["GET", "HEAD"], name="ping"),
        Route("/api/version.json", version, methods=["GET", "HEAD"], name="version"),
    ]


__all__ = ["make_routes", "ping", "version"]
