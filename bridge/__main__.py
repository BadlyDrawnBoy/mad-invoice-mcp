"""Entry point for python -m bridge."""
from __future__ import annotations

import sys


def main() -> None:
    """Forward to bridge.cli main entry point."""
    # Import here to avoid circular dependencies
    from bridge.app import MCP_SERVER, build_api_app
    from bridge.cli import build_parser, run
    from bridge.shim import build_openwebui_shim
    import logging

    logger = logging.getLogger("bridge.cli")

    def _start_sse(host: str, port: int) -> None:
        """Launch the MCP SSE server."""
        MCP_SERVER.settings.host = host
        MCP_SERVER.settings.port = int(port)
        MCP_SERVER.run(transport="sse")

    def _run_stdio() -> None:
        """Run stdio transport."""
        MCP_SERVER.run()

    parser = build_parser()
    args = parser.parse_args()

    routes = build_api_app().routes

    def shim_factory(upstream_base: str):
        return build_openwebui_shim(upstream_base, extra_routes=routes)

    run(
        args,
        logger=logger,
        start_sse=_start_sse,
        run_stdio=_run_stdio,
        shim_factory=shim_factory,
    )


if __name__ == "__main__":
    main()
