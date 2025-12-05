# Docker Quickstart

This guide shows how to build and run the MAD invoiceMCP container, mount your invoice data, and connect common MCP clients.

## Prerequisites

- Docker or a compatible runtime installed locally
- Host directory for invoice data (default: `.mad_invoice/` in your current project)
- Optional: set `MAD_INVOICE_ROOT` if you want invoices stored somewhere other than `/app/.mad_invoice`

The image contains TeX Live 2025 and all runtime dependencies (no external database required).

## Build the image

Run from the repository root:

```bash
docker build -t mad-invoice-mcp .
```

## Run the default server (web UI + API)

Start the bundled Uvicorn server exposed on container port `8000` (from the Dockerfile `CMD`).

```bash
docker run --rm \
  -p 8000:8000 \
  -v $(pwd)/.mad_invoice:/app/.mad_invoice \
  -e MCP_ENABLE_WRITES=1 \
  mad-invoice-mcp
```

- The container listens on `0.0.0.0:8000`; adjust the host port via `-p <host-port>:8000`.
- Data is stored in `/app/.mad_invoice` (override with `-e MAD_INVOICE_ROOT=/data/invoices`).
- Write-capable tools are disabled by default; set `MCP_ENABLE_WRITES=1` to allow writes.

## Connect Claude Desktop (Docker + stdio)

Claude Desktop can launch the MCP server inside Docker via stdio. Example snippet for your Claude config:

```json
{
  "mcpServers": {
    "mad-invoice": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "/absolute/path/to/.mad_invoice:/app/.mad_invoice",
        "-e", "MCP_ENABLE_WRITES=1",
        "mad-invoice-mcp",
        "python", "-m", "bridge", "--transport", "stdio"
      ]
    }
  }
}
```

- Build the image first (`docker build -t mad-invoice-mcp .`).
- Replace `/absolute/path/to/.mad_invoice` with your host path (Windows: `C:/Users/You/.mad_invoice:/app/.mad_invoice`).

## Connect OpenWebUI (Docker + SSE shim)

Run the unified bridge entrypoint for SSE + OpenWebUI shim and map the required ports:

```bash
docker run --rm \
  -p 8099:8099 -p 8081:8081 \
  -v $(pwd)/.mad_invoice:/app/.mad_invoice \
  -e MCP_ENABLE_WRITES=1 \
  mad-invoice-mcp \
  python -m bridge --transport sse \
    --mcp-host 0.0.0.0 --mcp-port 8099 \
    --shim-host 0.0.0.0 --shim-port 8081
```

Then point OpenWebUI to `http://localhost:8081/openapi.json` (it advertises the SSE endpoints at port 8099). You can change the exposed host ports if 8099/8081 are already in use.
