"""Tool registration for mad-invoice-mcp."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from bridge.backends import invoices


def register_tools(server: FastMCP) -> list[str]:
    """Register built-in backends on the MCP server."""

    loaded: list[str] = []
    try:
        invoices.register(server)
        loaded.append("bridge.backends.invoices")
    except Exception:  # pragma: no cover - defensive
        import logging

        logging.getLogger("bridge.api.tools").exception("backend.import_error", extra={"module": "invoices"})
    return loaded


__all__ = ["register_tools"]
