#!/usr/bin/env python3
"""Minimal OpenWebUI shim smoke test.

This script performs a simple GET against the shim's MCP OpenAPI endpoint to
verify that the bridge/shim is reachable. It prints a human-friendly success
message when the shim responds with JSON and exits non-zero with a readable
error message otherwise.
"""
from __future__ import annotations

import argparse
import sys

import httpx


DEFAULT_BASE_URL = "http://127.0.0.1:8081"


def run_smoke_check(base_url: str) -> int:
    """Perform the smoke check and return the desired exit code."""

    target = base_url.rstrip("/") + "/api/openapi.json"
    try:
        response = httpx.get(target, timeout=5)
    except httpx.RequestError as exc:
        print(
            f"ERROR: Unable to reach OpenWebUI shim at {target}: {exc}",
            file=sys.stderr,
        )
        return 1

    if response.status_code != 200:
        snippet = response.text[:200].replace("\n", " ")
        print(
            f"ERROR: Shim returned HTTP {response.status_code} for {target}: {snippet}",
            file=sys.stderr,
        )
        return 1

    try:
        payload = response.json()
    except ValueError:
        print(
            f"ERROR: Shim response from {target} was not valid JSON.",
            file=sys.stderr,
        )
        return 1

    info = payload.get("info", {})
    title = info.get("title", "unknown server")
    version = info.get("version", "unknown version")

    print(
        f"SUCCESS: OpenWebUI shim reachable at {target} ({title} v{version}).",
        "MCP metadata loaded.",
    )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Check that the OpenWebUI shim (python -m bridge --transport sse) responds to MCP metadata requests."
        )
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Base URL for the shim (default: {DEFAULT_BASE_URL})",
    )
    args = parser.parse_args()

    sys.exit(run_smoke_check(args.base_url))


if __name__ == "__main__":
    main()
