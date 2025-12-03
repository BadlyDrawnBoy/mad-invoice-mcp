# mad-invoice-mcp

MCP server for invoices with JSON storage and LaTeX→PDF rendering. Data lives in `.mad_invoice/` alongside the project; no external DB required. Keep `.mad_invoice/` out of git to avoid uploading real invoices (see `.gitignore`).

## Quick start

```bash
./bin/dev                      # create .venv and start uvicorn on 127.0.0.1:8000
MCP_ENABLE_WRITES=1 ./bin/dev  # enable write-capable tools
```

Requirements:
- Python 3.11+
- `pdflatex` (TeX Live/MiKTeX) for PDF rendering

Storage location:
- Default: `.mad_invoice/` under the current project (gitignored)
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
Parties support an optional `business_name` to place a trade/brand line under your personal name (useful for sole proprietors).

### Field notes

- `supplier.name`: Natural person name (appears first in header and signature).
- `supplier.business_name`: Optional trade/brand line below the natural name.
- `footer_bank`: Free-text payment block (e.g., IBAN, BIC, account holder).
- `footer_tax`: Free-text tax block (e.g., Steuernummer/USt-IdNr.).
- `small_business`: Enables §19 UStG; when true, VAT is omitted and `small_business_note` is shown.

## LaTeX template

`templates/invoice.tex` contains `%%PLACEHOLDER%%` markers that are filled before running `pdflatex`. Customize directly for branding (logo, colors, etc.).

## MCP tools (bridge/backends/invoices.py)

- `create_invoice_draft(invoice: Invoice) -> {invoice_path, index_path}`  
  Saves the invoice JSON and rewrites the index. LLM hints: `supplier.name` is the natural person; `supplier.business_name` is an optional trade/brand line. `small_business=True` disables VAT (§19 UStG) and shows `small_business_note`; when False, set `vat_rate`.
- `render_invoice_pdf(invoice_id: str) -> {pdf_path, tex_path}`  
  Resolves invoice JSON by id, fills `templates/invoice.tex`, and runs `pdflatex` (renders name + business_name on two lines).
- `update_invoice_status(invoice_id, payment_status, status?)`  
  `payment_status` must be one of `open|paid|overdue|cancelled`; `status` is a free-form lifecycle flag (e.g., draft/final).
- `generate_invoice_number(separator="-") -> {invoice_number, sequence_path}`  
  Returns the next invoice number using a yearly counter in `.mad_invoice/sequence.json` (default format: `YYYY-####`; set `separator=""` or `null` for no dash).
- `get_invoice_template()`  
  Returns an example `Invoice` payload with defaults and field notes (name vs. business_name, VAT, footer blocks).

Writes require `MCP_ENABLE_WRITES=1`.

## Web UI (minimal)

- `GET /invoices` – overview from `index.json`
- `GET /invoices/{id}` – detail view with line items and PDF presence
- `POST /invoices/{id}/render` – render PDF
- `POST /invoices/{id}/mark-paid` – set `payment_status="paid"`

## VAT

- Small business mode (`small_business=True`) shows the VAT-free note and no VAT line.
- To apply VAT, set `small_business=False` and a `vat_rate` between 0 and 1 (e.g. `0.19`).
- The LaTeX output shows VAT and a gross total when VAT is enabled.

## Language

- `Invoice.language` supports `"de"` and `"en"`; renderer is currently German-first but ready for future label switching.

## Development

- Install deps: `pip install -r requirements.txt`
- Run server: `./bin/dev`
- Example backend scaffold: `bridge/backends/example.py`

## Roadmap

- Polish styling and add VAT logic when needed.
- Expand docs with sample invoice JSON and OpenWebUI workflow examples.
