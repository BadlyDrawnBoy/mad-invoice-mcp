"""Minimal CLI helpers for running the MCP server."""
from __future__ import annotations

import argparse
import logging
import threading
from typing import Callable

import uvicorn
from starlette.applications import Starlette

ShimFactory = Callable[[str], Starlette]
StartSSE = Callable[[str, int], None]
RunStdIO = Callable[[], None]


def build_parser() -> argparse.ArgumentParser:
    """Create an argument parser for the runtime."""

    parser = argparse.ArgumentParser(description="mad-invoice-mcp server")
    parser.add_argument(
        "--transport",
        type=str,
        default="sse",
        choices=["stdio", "sse"],
        help="Transport mechanism to expose (default: sse)",
    )
    parser.add_argument(
        "--mcp-host",
        type=str,
        default="127.0.0.1",
        help="Host for the internal MCP SSE server",
    )
    parser.add_argument(
        "--mcp-port",
        type=int,
        default=8099,
        help="Port for the internal MCP SSE server",
    )
    parser.add_argument(
        "--shim-host",
        type=str,
        default="127.0.0.1",
        help="Host for the optional OpenWebUI shim",
    )
    parser.add_argument(
        "--shim-port",
        type=int,
        default=8081,
        help="Port for the optional OpenWebUI shim",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser


def run(
    args: argparse.Namespace,
    *,
    logger: logging.Logger,
    start_sse: StartSSE,
    run_stdio: RunStdIO,
    shim_factory: ShimFactory,
) -> None:
    """Execute the CLI behaviour shared by legacy and modular entry points."""

    if args.debug:
        logger.setLevel(logging.DEBUG)

    if args.transport == "sse":
        thread = threading.Thread(
            target=start_sse, args=(args.mcp_host, args.mcp_port), daemon=True
        )
        thread.start()

        upstream_base = f"http://{args.mcp_host}:{args.mcp_port}"
        app = shim_factory(upstream_base)
        logger.info(
            "[Shim] OpenWebUI endpoint on http://%s:%s/openapi.json",
            args.shim_host,
            args.shim_port,
        )
        uvicorn.run(app, host=args.shim_host, port=int(args.shim_port))
    else:
        logger.info("[MCP] Running in stdio mode (no SSE).")
        run_stdio()


__all__ = ["build_parser", "run"]
