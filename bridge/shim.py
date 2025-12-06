"""OpenWebUI shim for MCP SSE transport."""
from __future__ import annotations

import json
import logging
from typing import Any, Sequence

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, StreamingResponse
from starlette.routing import Route

logger = logging.getLogger("bridge.shim")


def build_openwebui_shim(
    upstream_base: str, *, extra_routes: Sequence[Route] | None = None
) -> Starlette:
    """Create a Starlette app exposing OpenWebUI-compatible MCP shim routes.

    OpenWebUI recognizes the x-openwebui-mcp extension and connects via MCP protocol.
    The shim proxies SSE and messages endpoints to the upstream MCP server.
    """

    async def openapi_get(request: Request):
        """Return OpenAPI schema with x-openwebui-mcp extension."""
        client_ip = request.client.host if request.client else "unknown"
        ua = request.headers.get("user-agent", "")
        logger.info("GET /openapi.json client=%s ua=%s", client_ip, ua)
        return JSONResponse(
            {
                "openapi": "3.1.0",
                "info": {"title": "MAD Invoice MCP", "version": "0.1.0"},
                "x-openwebui-mcp": {
                    "transport": "sse",
                    "sse_url": "/sse",
                    "messages_url": "/messages",
                },
            }
        )

    async def openapi_post(request: Request):
        """Handle MCP initialization via POST to /openapi.json."""
        client_ip = request.client.host if request.client else "unknown"
        ua = request.headers.get("user-agent", "")
        try:
            body = await request.json()
            req_id = body.get("id", 0)
        except Exception:
            req_id = 0
        logger.info(
            "POST /openapi.json client=%s ua=%s request_id=%s", client_ip, ua, req_id
        )

        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "experimental": {},
                        "prompts": {"listChanged": False},
                        "resources": {"subscribe": False, "listChanged": False},
                        "tools": {"listChanged": False},
                    },
                    "serverInfo": {"name": "mad-invoice-mcp", "version": "0.1.0"},
                },
            }
        )

    async def health(request: Request):
        """Health check endpoint."""
        return JSONResponse(
            {
                "ok": True,
                "type": "mcp-sse",
                "endpoints": {"sse": "/sse", "messages": "/messages"},
            }
        )

    async def root_post_ok(request: Request):
        """Root POST handler."""
        return JSONResponse({"jsonrpc": "2.0", "id": 0, "result": {"ok": True}})

    async def sse_proxy(request: Request):
        """Proxy SSE connection to upstream MCP server."""
        url = upstream_base + "/sse"
        headers = {"accept": "text/event-stream"}
        params = dict(request.query_params)
        client_ip = request.client.host if request.client else "unknown"
        ua = request.headers.get("user-agent", "")
        logger.info("SSE connect client=%s ua=%s", client_ip, ua)

        async def event_generator():
            try:
                async with httpx.AsyncClient(timeout=None) as client:
                    async with client.stream(
                        "GET", url, params=params, headers=headers
                    ) as upstream:
                        async for chunk in upstream.aiter_bytes():
                            yield chunk
            finally:
                logger.info("SSE disconnect client=%s ua=%s", client_ip, ua)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
        )

    async def messages_proxy(request: Request):
        """Proxy messages to upstream MCP server and handle initialization."""
        url = upstream_base + request.url.path
        data = await request.body()
        headers = {
            "content-type": request.headers.get("content-type", "application/json")
        }
        params = dict(request.query_params)
        client_ip = request.client.host if request.client else "unknown"
        ua = request.headers.get("user-agent", "")
        method: str | None = None

        # Check if this is an initialize message
        should_send_initialized = False
        if headers["content-type"].startswith("application/json") and data:
            try:
                payload: Any = json.loads(data)
                if isinstance(payload, dict):
                    method = payload.get("method")
                    should_send_initialized = method == "initialize"
            except json.JSONDecodeError:
                pass
        logger.info(
            "Proxying message client=%s ua=%s method=%s", client_ip, ua, method
        )

        async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
            resp = await client.post(url, content=data, headers=headers, params=params)

            # Send initialized notification after successful initialize
            if should_send_initialized and resp.status_code < 400:
                init_headers = {"content-type": "application/json"}
                init_payload = json.dumps(
                    {"jsonrpc": "2.0", "method": "initialized", "params": {}}
                )
                try:
                    await client.post(
                        url,
                        content=init_payload,
                        headers=init_headers,
                        params=params,
                    )
                except Exception:
                    pass  # Shim must remain permissive

            if resp.status_code >= 500:
                logger.error(
                    "Upstream error status=%s client=%s ua=%s method=%s",
                    resp.status_code,
                    client_ip,
                    ua,
                    method,
                )
            elif resp.status_code >= 400:
                logger.warning(
                    "Upstream warning status=%s client=%s ua=%s method=%s",
                    resp.status_code,
                    client_ip,
                    ua,
                    method,
                )

            return PlainTextResponse(
                resp.text,
                status_code=resp.status_code,
                headers={"content-type": resp.headers.get("content-type", "application/json")},
            )

    routes = [
        Route("/openapi.json", openapi_get, methods=["GET"]),
        Route("/openapi.json", openapi_post, methods=["POST"]),
        Route("/health", health, methods=["GET"]),
        Route("/", root_post_ok, methods=["POST"]),
        Route("/sse", sse_proxy, methods=["GET"]),
        Route("/messages", messages_proxy, methods=["POST"]),
        Route("/messages/", messages_proxy, methods=["POST"]),
    ]
    if extra_routes:
        routes.extend(extra_routes)
    return Starlette(debug=False, routes=routes)


__all__ = ["build_openwebui_shim"]
