# mad-invoice-mcp

MCP server for invoices with JSON storage and LaTeX→PDF rendering. Data lives in `.mad_invoice/` inside the repo; no external DB required.

## Quick start

```bash
./bin/dev                      # create .venv and start uvicorn on 127.0.0.1:8000
MCP_ENABLE_WRITES=1 ./bin/dev  # enable write-capable tools
```

Requirements:
- Python 3.11+
- `pdflatex` (TeX Live/MiKTeX) for PDF rendering

Storage location:
- Default: `.mad_invoice/` under the current project
- Override: `MAD_INVOICE_ROOT=/path/to/store ./bin/dev`

## Data model & layout

See `bridge/backends/invoices_models.py` (Party, LineItem, Invoice). Files live under:

```
.mad_invoice/
  invoices/<invoice-id>.json
  index.json
  build/<invoice-id>/invoice.tex|pdf   # created by render_invoice_pdf
```

`invoice.payment_status` tracks `"open" | "paid" | "overdue" | "cancelled"` and is included in the index.

## LaTeX template

`templates/invoice.tex` contains `%%PLACEHOLDER%%` markers that are filled before running `pdflatex`. Customize directly for branding (logo, colors, etc.).

## MCP tools (bridge/backends/invoices.py)

- `create_invoice_draft(invoice: Invoice) -> {invoice_path, index_path}`  
  Saves the invoice JSON and rewrites the index.
- `render_invoice_pdf(invoice_id: str) -> {pdf_path, tex_path}`  
  Fills the template and runs `pdflatex`.
- `update_invoice_status(invoice_id, payment_status, status?)`  
  Updates payment/status fields and rewrites the index.

Writes require `MCP_ENABLE_WRITES=1`.

## Web UI (minimal)

- `GET /invoices` – overview from `index.json`
- `GET /invoices/{id}` – detail view with line items and PDF presence
- `POST /invoices/{id}/render` – render PDF
- `POST /invoices/{id}/mark-paid` – set `payment_status="paid"`

## Development

- Install deps: `pip install -r requirements.txt`
- Run server: `./bin/dev`
- Example backend scaffold: `bridge/backends/example.py`

## Roadmap

- Polish styling and add VAT logic when needed.
- Expand docs with sample invoice JSON and OpenWebUI workflow examples.
