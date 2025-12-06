"""Minimal CLI helpers for running the MCP server."""
from __future__ import annotations

import argparse
import logging
import socket
import threading
from typing import Callable

import uvicorn
from starlette.applications import Starlette

from bridge.utils.config import ENABLE_WRITES

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
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)

    logger.info(
        "Starting MCP server (transport=%s, mcp=%s:%s, shim=%s:%s, writes=%s)",
        args.transport,
        args.mcp_host,
        args.mcp_port,
        args.shim_host,
        args.shim_port,
        "enabled" if ENABLE_WRITES else "disabled",
    )

    def _validate_port(value: int, *, flag: str) -> None:
        if value <= 0 or value > 65535:
            logger.error("Invalid %s: %s (must be between 1 and 65535)", flag, value)
            raise SystemExit(2)

    def _check_port_available(host: str, port: int, *, label: str, flag: str) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
            except OSError as exc:  # pragma: no cover - depends on local env
                hint = f"Use {flag} to pick a free port."
                logger.error(
                    "%s port %s is unavailable on %s: %s. %s",
                    label,
                    port,
                    host,
                    exc.strerror or exc,
                    hint,
                )
                raise SystemExit(1)

    _validate_port(args.mcp_port, flag="--mcp-port")
    _validate_port(args.shim_port, flag="--shim-port")

    if args.transport == "sse":
        if args.mcp_host == args.shim_host and args.mcp_port == args.shim_port:
            logger.error(
                "Shim port conflicts with MCP SSE port (%s:%s). Use --shim-port to separate them.",
                args.shim_host,
                args.shim_port,
            )
            raise SystemExit(2)

        _check_port_available(
            args.mcp_host,
            args.mcp_port,
            label="MCP SSE",
            flag="--mcp-port",
        )
        _check_port_available(
            args.shim_host,
            args.shim_port,
            label="OpenWebUI shim",
            flag="--shim-port",
        )

        logger.debug("Transport: SSE proxy")
        logger.debug(
            "MCP SSE server listening on http://%s:%s", args.mcp_host, args.mcp_port
        )
        logger.debug(
            "OpenWebUI shim enabled at http://%s:%s (proxied to MCP)",
            args.shim_host,
            args.shim_port,
        )
        if not ENABLE_WRITES:
            logger.warning(
                "Write-capable tools disabled (set MCP_ENABLE_WRITES=1 to enable writes)."
            )

        thread = threading.Thread(
            target=start_sse, args=(args.mcp_host, args.mcp_port), daemon=True
        )
        thread.start()

        upstream_base = f"http://{args.mcp_host}:{args.mcp_port}"
        app = shim_factory(upstream_base)
        logger.debug(
            "[Shim] OpenWebUI endpoint on http://%s:%s/openapi.json",
            args.shim_host,
            args.shim_port,
        )
        try:
            uvicorn.run(app, host=args.shim_host, port=int(args.shim_port))
        except OSError as exc:  # pragma: no cover - depends on local env
            logger.error(
                "Failed to start OpenWebUI shim on %s:%s: %s",
                args.shim_host,
                args.shim_port,
                exc.strerror or exc,
            )
            raise SystemExit(1)
    else:
        logger.debug("Transport: stdio")
        logger.debug("OpenWebUI shim disabled in stdio mode.")
        run_stdio()


__all__ = ["build_parser", "run"]
