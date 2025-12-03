# Mechatronics Advisory & Design – invoiceMCP server

<img width="2048" height="786" alt="logo" src="https://github.com/user-attachments/assets/203a5a7b-4802-4edc-8250-ddaf7143186c" />

MAD invoiceMCP: Creating, storing, and rendering invoices as JSON + LaTeX + PDF. Designed for single-company workflows with local storage in `.mad_invoice/` (no external database required).

**What it does:**
- Create and manage invoices via MCP tools
- Render professional PDFs with LaTeX
- Track payment status and generate invoice numbers
- Support for German §19 UStG (small business) and VAT

**Why:**
- "Kraft" wasen't fexible enough
- the others where overkill or required web space
- The re-kp project had already done half the groundwork

## Setup: Choose your path

Pick the setup that matches your situation:

### Path A: MCP stdio (local pdflatex)

**When to use:** You have or can install TeX Live 2024+ locally.

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start MCP server (stdio)
MCP_ENABLE_WRITES=1 python -m bridge.cli --transport stdio
```

The server auto-discovers pdflatex in:
- System PATH
- `~/.local/texlive/*/bin/*/pdflatex`
- `/usr/local/texlive/*/bin/*/pdflatex`

**Manual override** for custom locations:
```bash
export PDFLATEX_PATH=/path/to/your/pdflatex
MCP_ENABLE_WRITES=1 python -m bridge.cli --transport stdio
```

---

### Path B: MCP stdio (via Docker)

**When to use:** You don't have TeX Live, or want to avoid version issues (TeX Live 2022 has known bugs).

```bash
# 1. Build image (includes TeX Live 2025)
docker build -t mad-invoice-mcp .

# 2. Run MCP server via Docker
docker run --rm -i \
  -e MCP_ENABLE_WRITES=1 \
  -v $(pwd)/.mad_invoice:/app/.mad_invoice \
  mad-invoice-mcp python -m bridge.cli --transport stdio
```

**What this does:**
- Bundles TeX Live 2025 (no local installation needed)
- Mounts `.mad_invoice/` so data persists on your host
- Runs stdio through the container

---

### Path C: Web UI / Development

**When to use:** You want the web interface or are developing the server itself.

```bash
# Local development server
./bin/dev                      # starts uvicorn on 127.0.0.1:8000
MCP_ENABLE_WRITES=1 ./bin/dev  # with write operations enabled
```

**Or via Docker:**
```bash
docker run --rm -p 8000:8000 \
  -e MCP_ENABLE_WRITES=1 \
  -v $(pwd)/.mad_invoice:/app/.mad_invoice \
  mad-invoice-mcp
```

Access web UI at `http://localhost:8000/invoices`

---

## Requirements

- **Python 3.11+** (for local setup)
- **pdflatex** (TeX Live 2024+ recommended, or use Docker)
- **MCP_ENABLE_WRITES=1** environment variable to enable write operations

## MCP Tools

The server exposes these tools for LLM/MCP clients:

### Draft vs. Final Workflow

Invoices follow a **draft → final** lifecycle:

- **Draft (`status="draft"`)**: Fully editable, can be deleted
- **Final (`status="final"`)**: Immutable "sargnagel" - only PDF rendering and reading allowed

### `create_invoice_draft(invoice: Invoice)`
Create and save a new invoice (always starts as draft).

**Key fields for LLMs:**
- `supplier.name`: Natural person name (required)
- `supplier.business_name`: Optional trade/brand name (renders as second line)
- `small_business=True`: German §19 UStG (no VAT)
- `small_business=False`: Set `vat_rate` (e.g., `0.19`)

Returns: `{invoice_path, index_path}`

### `update_invoice_draft(invoice_id: str, invoice: Invoice)`
Update the complete content of a draft invoice.

**Restrictions:**
- Only works for `status="draft"`
- Cannot edit finalized invoices

Use this to correct mistakes or make changes before finalizing.

Returns: `{invoice, invoice_path, index_path}`

### `delete_invoice_draft(invoice_id: str)`
Permanently delete a draft invoice.

**Restrictions:**
- Only works for `status="draft"`
- Cannot delete finalized invoices
- Irreversible operation

Returns: `{deleted_invoice_id, deleted_path, index_path}`

### `render_invoice_pdf(invoice_id: str)`
Render invoice to PDF using LaTeX template.

Works for both draft and final invoices.

Returns: `{pdf_path, tex_path}`

### `update_invoice_status(invoice_id, payment_status, status?)`
Update payment tracking and lifecycle status.

**payment_status:** `open | paid | overdue | cancelled`
**status:** `draft | final` (one-way: cannot change final → draft)

Use `status="final"` to finalize an invoice (makes it immutable).

Returns: `{invoice, invoice_path, index_path}`

### `generate_invoice_number(separator="-")`
Generate next invoice number (format: `YYYY-####`).

Pass `separator=""` or `null` for no separator.

Returns: `{invoice_number, sequence_path}`

### `get_invoice_template()`
Get example invoice payload with field documentation.

Returns: Example `Invoice` object

## Data storage

Invoices are stored locally (gitignored by default):

```
.mad_invoice/
  invoices/<invoice-id>.json       # Individual invoices
  index.json                        # Quick lookup index
  sequence.json                     # Invoice number counters
  build/<invoice-id>/invoice.pdf   # Rendered PDFs
```

**Override storage location:**
```bash
export MAD_INVOICE_ROOT=/custom/path
```

## Invoice data model

### Party (supplier/customer)
- `name`: Natural person or company name (required)
- `business_name`: Optional trade/brand name (e.g., "M.A.D. Solutions")
- Address: `street`, `postal_code`, `city`, `country`
- Contact: `email`, `phone`, `tax_id`

### LineItem
- `description`: Service/product description
- `quantity`: Amount (default: 1.0)
- `unit`: Unit of measure (default: "Std.")
- `unit_price`: Price per unit (can be negative for discounts)

### Invoice
- IDs: `id`, `invoice_number`
- Dates: `invoice_date`, `due_date`
- Status: `status` (draft/final), `payment_status` (open/paid/overdue/cancelled)
- Parties: `supplier`, `customer`
- Items: `items[]`
- VAT: `small_business` (bool), `vat_rate` (0-1)
- Text: `intro_text`, `outro_text`, `payment_terms`
- Footer: `footer_bank`, `footer_tax`
- Language: `language` ("de" | "en")

## VAT handling

**Small business mode** (`small_business=True`):
- German §19 UStG (no VAT)
- Shows `small_business_note` on invoice
- Only subtotal displayed

**Regular mode** (`small_business=False`):
- Set `vat_rate` (0-1, e.g., `0.19`)
- Calculates VAT amount
- Shows gross total (subtotal + VAT)

## LaTeX template customization

Edit `templates/invoice.tex` directly for branding (logo, colors, layout).

Placeholders use format: `%%VARIABLE%%` (e.g., `%%INVOICE_NUMBER%%`)

## Web UI endpoints

- `GET /invoices` – Invoice overview
- `GET /invoices/{id}` – Detail view
- `POST /invoices/{id}/render` – Render PDF
- `POST /invoices/{id}/mark-paid` – Mark as paid

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests (if available)
pytest

# Development server with auto-reload
./bin/dev
```

## Troubleshooting

**"pdflatex not found"**
- Install TeX Live 2024+: https://tug.org/texlive/
- Or use Docker (Path B above)
- Or set `PDFLATEX_PATH` for custom locations

**"Write operations disabled"**
- Set `MCP_ENABLE_WRITES=1` environment variable

**Port 8000 already in use**
- Change port: `uvicorn bridge.app:create_app --factory --port 8001`

## Configuration

**Environment variables:**
- `MCP_ENABLE_WRITES`: Enable write operations (default: `0`)
- `MAD_INVOICE_ROOT`: Storage location (default: `.mad_invoice/`)
- `PDFLATEX_PATH`: Custom pdflatex binary path (auto-discovered if not set)

## License & Contributing

See repository for details.
