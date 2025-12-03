# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`mad-invoice-mcp` is an MCP (Model Context Protocol) server for creating, storing, and rendering invoices as JSON + LaTeX + PDF. Data is stored locally in `.mad_invoice/` (gitignored) with no external database dependency. The project is designed for single-company/single-user workflows.

## Development Commands

### Start the server
```bash
./bin/dev                      # create .venv and start uvicorn on 127.0.0.1:8000
MCP_ENABLE_WRITES=1 ./bin/dev  # enable write-capable tools
```

### Docker
```bash
docker build -t mad-invoice-mcp .
docker run --rm -p 8000:8000 -e MCP_ENABLE_WRITES=1 \
  -v $(pwd)/.mad_invoice:/app/.mad_invoice \
  mad-invoice-mcp
```

### Environment Setup
- Python 3.11+
- `pdflatex` from TeX Live 2024+ required for PDF rendering
  - Auto-discovered in system PATH, `~/.local/texlive/`, `/usr/local/texlive/`
  - Override with `PDFLATEX_PATH=/path/to/pdflatex`
  - Docker image includes TeX Live 2025 to avoid pdflatex bugs (optional)
- Requirements: `pip install -r requirements.txt`

## Architecture

### Data Model (`bridge/backends/invoices_models.py`)
- **Party**: Represents supplier or customer. Supports:
  - `name`: Natural person name (required, appears first)
  - `business_name`: Optional trade/brand name (renders as second line)
  - Address, contact, and tax fields with validation
- **LineItem**: Invoice line with description, quantity, unit, unit_price
- **Invoice**: Main entity with:
  - Strict Pydantic validation (`extra="forbid"` rejects unexpected fields)
  - `status`: Lifecycle flag ("draft" | "final")
  - `payment_status`: Payment tracking ("open" | "paid" | "overdue" | "cancelled")
  - `small_business`: Boolean for German §19 UStG (VAT exemption)
  - `vat_rate`: Float 0-1 for VAT calculation when `small_business=False`
  - `language`: "de" | "en" for localization
  - Validation: due_date >= invoice_date, subtotal >= 0

### Storage (`bridge/backends/invoices_storage.py`)
Directory structure under `.mad_invoice/`:
```
.mad_invoice/
  invoices/<invoice-id>.json    # Individual invoice files
  index.json                     # Aggregated list for quick queries
  sequence.json                  # Yearly counters for invoice numbering
  build/<invoice-id>/            # LaTeX and PDF outputs
    invoice.tex
    invoice.pdf
```

Key functions:
- `get_invoice_root()`: Resolves storage location (respects `MAD_INVOICE_ROOT` env var)
- `ensure_structure()`: Creates required directories
- `save_invoice()`, `load_invoice()`: JSON serialization with Pydantic validation
- `build_index()`, `save_index()`: Rebuild index from all invoice files
- `with_index_lock()`: File-based mutex using portalocker for safe concurrent writes
- `next_invoice_number()`: Atomic yearly sequence generation (format: YYYY-####)

### MCP Tools (`bridge/backends/invoices.py`)

#### Draft/Final Lifecycle

Invoices follow a **draft → final** workflow:
- **Draft (`status="draft"`)**: Fully editable, can be deleted
- **Final (`status="final"`)**: Immutable - only PDF rendering allowed
- **One-way street**: Cannot change `final` back to `draft`

#### Tools

1. **create_invoice_draft(invoice: Invoice)**
   - Validates and persists invoice JSON (always starts as draft)
   - Rebuilds index atomically
   - Requires `MCP_ENABLE_WRITES=1`

2. **update_invoice_draft(invoice_id: str, invoice: Invoice)**
   - Updates complete invoice content
   - Only works for `status="draft"`
   - Cannot edit finalized invoices

3. **delete_invoice_draft(invoice_id: str)**
   - Permanently deletes invoice
   - Only works for `status="draft"`
   - Cannot delete finalized invoices

4. **render_invoice_pdf(invoice_id: str)**
   - Loads invoice, fills `templates/invoice.tex` placeholders
   - Runs pdflatex twice (for reference resolution)
   - Escapes LaTeX special chars and formats currency/dates by language
   - Works for both draft and final invoices

5. **update_invoice_status(invoice_id, payment_status, status?)**
   - Updates payment tracking and lifecycle status
   - Prevents `final` → `draft` changes (immutability guard)
   - Use `status="final"` to finalize invoice
   - Rebuilds index

6. **generate_invoice_number(separator="-")**
   - Returns next invoice number from yearly sequence
   - Default format: "YYYY-####" (pass `separator=""` for "YYYY####")

7. **get_invoice_template()**
   - Returns example Invoice payload with field documentation

### LaTeX Rendering
- Template: `templates/invoice.tex` with `%%PLACEHOLDER%%` markers
- Logic in `_invoice_replacements()`: escapes text, formats dates/currency by language, handles VAT conditionally
- Two-pass pdflatex execution for correct page references
- Fonts: lmodern + microtype for sharp output
- Party names render on multiple lines when `business_name` is set

### Web UI (`bridge/api/routes.py`, `bridge/web/`)
Minimal FastHTML interface:
- `GET /invoices` – overview table from index.json
- `GET /invoices/{id}` – detail view with line items
- `POST /invoices/{id}/render` – trigger PDF generation
- `POST /invoices/{id}/mark-paid` – set payment_status="paid"

### Application Wiring (`bridge/app.py`)
- SSE-based MCP server with single-connection guard (409 on conflict)
- State management: readiness tracking, connection lifecycle logging
- API routes: `/api/state`, `/api/openapi.json`
- Startup: `configure()` registers tools and logging

## Design Constraints

**Critical principles to maintain:**
1. **No database**: JSON files are the source of truth
2. **Strict validation**: Pydantic models reject invalid/unexpected fields with hard errors
3. **Write gate**: All write operations must check `MCP_ENABLE_WRITES` and use `record_write_attempt()`
4. **Deterministic behavior**: Operations succeed cleanly or fail loudly; no partial writes
5. **Single-project scope**: One `.mad_invoice/` store per repository; no multi-project switching

## Key Implementation Patterns

### Adding New MCP Tools
1. Define in `bridge/backends/invoices.py` within `register(server)` function
2. Use `@server.tool()` decorator
3. Call `_require_writes_enabled()` for mutations
4. Call `record_write_attempt()` for audit trail
5. Use `with_index_lock()` when modifying multiple files
6. Raise `ToolError` (from `mcp.server.fastmcp.exceptions`) for user-facing errors

### Modifying Invoice Model
1. Update Pydantic models in `bridge/backends/invoices_models.py`
2. Add field validators if needed (`@field_validator`, `@model_validator`)
3. Use `extra="forbid"` to reject unknown fields
4. Update `to_index_entry()` if field should appear in index
5. Update LaTeX replacements in `_invoice_replacements()` if rendering changes

### LaTeX Customization
- Edit `templates/invoice.tex` directly for branding (logo, colors, layout)
- Add new placeholders as `%%VARIABLE%%` and populate in `_invoice_replacements()`
- Escape all text with `_escape_tex()` or `_escape_multiline()` to prevent LaTeX injection
- Use `_LABELS` dict for multi-language label support

### Testing Patterns
- No test suite currently exists (TODO)
- Manual testing via Web UI or direct MCP tool calls
- Docker setup useful for testing pdflatex reliability

## Common Pitfalls

1. **Forgetting LaTeX escaping**: Always use `_escape_tex()` for user input to prevent compilation errors
2. **Index out of sync**: Use `with_index_lock()` and rebuild index after every invoice write
3. **Pydantic validation bypass**: Never construct Invoice from `dict` without `.model_validate()`
4. **Write operations without gate**: Check `_require_writes_enabled()` first
5. **Missing party.name vs. business_name**: `name` is required (natural person); `business_name` is optional trade name

## File Organization

```
bridge/
  backends/
    invoices_models.py    # Pydantic models (Party, LineItem, Invoice)
    invoices_storage.py   # Filesystem operations, JSON serialization
    invoices.py           # MCP tool implementations
  api/
    routes.py             # HTTP API routes
    tools.py              # Tool registration orchestration
    envelopes.py          # API response wrappers
  web/                    # FastHTML web UI
  utils/
    config.py             # Environment config (ENABLE_WRITES)
    logging.py            # Structured logging setup
  app.py                  # Application factory, SSE/API wiring
  cli.py                  # CLI entrypoint (if needed)
templates/
  invoice.tex             # LaTeX template with placeholders
bin/
  dev                     # Development server startup script
```

## Configuration

### Environment Variables
- `MCP_ENABLE_WRITES`: Set to `1` to enable write operations (default: disabled)
- `MAD_INVOICE_ROOT`: Override storage location (default: `.mad_invoice/` in repo root)
- `PDFLATEX_PATH`: Override pdflatex binary location (auto-discovered if not set)

### Storage Location Priority
1. `MAD_INVOICE_ROOT` env var (absolute or relative to cwd)
2. Explicit base_path parameter (internal use)
3. Repository root (parent of bridge/) – default

## Localization

Language support via `Invoice.language` field ("de" | "en"):
- Date formatting: `_format_date()` respects `Invoice.date_style` ("iso" | "locale") with language-aware defaults
- Currency formatting: `_format_currency()` uses comma (de) or dot (en) as decimal separator
- LaTeX labels: `_LABELS` dict provides translations for invoice title, dates, totals
- Expand by adding entries to `_LABELS` and updating `_invoice_replacements()`

## VAT Handling

- **Small business mode** (`small_business=True`): No VAT calculation, shows `small_business_note`
- **VAT mode** (`small_business=False`): Requires `vat_rate` (0-1), calculates VAT amount, shows gross total
- VAT line conditionally rendered via `%%VAT_LINE%%` placeholder replacement
- `Invoice.total()` returns subtotal (small business) or subtotal + VAT (regular)

## Party Naming Convention

Critical for LLM callers:
- `supplier.name`: Natural person or primary entity name (required, appears first)
- `supplier.business_name`: Optional trade/brand name (renders as second line in header/footer)
- Example: `name="Max Mustermann"`, `business_name="M.A.D. Solutions"`
- Both supplier and customer support this pattern

## Planning Context

`.plan/` directory (not part of runtime):
- `ORIENTATION.md`: High-level design constraints and agent expectations
- `TODO.md`: Task backlog with done/pending items
- `tasks.manifest.json`, `state.json`: Task tracking metadata

When implementing features, consult `.plan/TODO.md` for context on pending work.
