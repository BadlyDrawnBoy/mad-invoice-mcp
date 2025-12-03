"""Envelope helpers for HTTP/MCP responses."""
from __future__ import annotations


def envelope_ok(data: object) -> dict[str, object]:
    return {"ok": True, "data": data, "errors": []}


__all__ = ["envelope_ok"]
