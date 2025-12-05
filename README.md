# MAD invoiceMCP server
_Mechatronics Advisory & Design (M.A.D. Solutions) – JSON → LaTeX → PDF invoicing server with local file storage._

<img width="2048" height="786" alt="logo" src="https://github.com/user-attachments/assets/203a5a7b-4802-4edc-8250-ddaf7143186c" />

MAD invoiceMCP lets you create, store, and render invoices using JSON + LaTeX + PDF.  It is designed for single-company workflows with local storage in `.mad_invoice/` (no external database or cloud service required). Inspect invoices through the read-only MCP tools (e.g., `list_invoices`, `get_invoice`) rather than opening files under `.mad_invoice/`, since the storage location may be mounted elsewhere or read-only in hosted environments.

**_What it does:_**
- Create and manage invoices via MCP tools
- Render professional PDFs using LaTeX templates
- Track payment status and generate invoice numbers
- Support for German §19 UStG (small business) and standard VAT

**_Why:_**
- “Kraft” wasn’t flexible enough
- Other tools were overkill or required web hosting
- The re-kp project had already done half the groundwork

## Supported clients

Officially supported MCP clients and their intended usage:

| Client | Type | OS | Status | Usage |
| --- | --- | --- | --- | --- |
| OpenWebUI (with MAD shim) | Web UI (MCP over SSE) | Linux, macOS, Windows | Supported | Everyday |
| Claude Desktop | Desktop app (MCP stdio) | macOS, Windows | Supported | Everyday |
| Continue.dev | IDE extension (MCP stdio) | Linux, macOS, Windows | Supported | Dev only |
| Cline | IDE extension (MCP stdio) | Linux, macOS, Windows | Supported | Dev only |
| Claude Code (VS Code) | IDE extension (MCP stdio) | Linux, macOS, Windows | Supported | Dev only |

## Quickstart

### Path A: MCP stdio (local pdflatex)

Use when TeX Live 2024+ is installed locally.

```bash
# Install dependencies
pip install -r requirements.txt

# Start MCP server (stdio)
MCP_ENABLE_WRITES=1 python -m bridge --transport stdio
```

Auto-discovers `pdflatex` on PATH or typical TeX Live install locations. Set `PDFLATEX_PATH` to override.

### Path C: Web UI / Development

Use for the web interface or local development.

```bash
# Local development server
./bin/dev                      # starts uvicorn on 127.0.0.1:8000
MCP_ENABLE_WRITES=1 ./bin/dev  # with write operations enabled
```

Or via Docker:

```bash
docker run --rm -p 8000:8000 \
  -e MCP_ENABLE_WRITES=1 \
  -v $(pwd)/.mad_invoice:/app/.mad_invoice \
  mad-invoice-mcp
```

Access the web UI at `http://localhost:8000/invoices`.

## More documentation

- [Advanced setup, SSE transport, and production notes](ADVANCED.md)
- [MCP client configuration examples](docs/clients.md)
- [MCP tools reference](docs/tools.md)
- [Agent orientation and data access expectations](.plan/ORIENTATION.md)
