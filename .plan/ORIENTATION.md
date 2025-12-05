# Orientation for agents – mad-invoice-mcp

This repo contains **mad-invoice-mcp**, a small MCP server that creates and stores invoices
for M.A.D. Solutions as JSON + LaTeX + PDF.

Core behaviour:

- Invoices are Pydantic models (`Party`, `LineItem`, `Invoice`) defined in
  `bridge/backends/invoices_models.py`.
- Data is stored as plain JSON under a project-local directory:

```
.mad_invoice/
invoices/<invoice-id>.json
index.json
build/<invoice-id>/invoice.tex|pdf
```

- Primary MCP tools live in `bridge/backends/invoices.py`.

- **Read-only data access**: agents should inspect invoices via the **read-only
  MCP tools** (e.g. `list_invoices`, `get_invoice`) instead of opening files
  under `.mad_invoice/` directly. Storage may live outside the repo or be
  mounted read-only, so direct file reads are discouraged and may fail in
  hosted environments.
- **Write operations** go through the existing helpers:
  - `create_invoice_draft(invoice: Invoice)`
    → validates and writes `.mad_invoice/invoices/<id>.json` and rebuilds `index.json`.
  - `render_invoice_pdf(invoice_id: str)`
    → loads the invoice, fills `templates/invoice.tex`, runs `pdflatex` and writes
      `.mad_invoice/build/<id>/invoice.pdf`.

The server is intended for a **single company / single user** workflow:
one repo, one `.mad_invoice/` store, no multi-project switching.

## Design constraints

- **No database**: JSON files on disk are the source of truth.
- **Strict validation**: Only valid `Invoice` objects may be written.
  Unexpected fields must be rejected; invalid values should raise hard errors.
- **Write gate**: Any tool that writes under `.mad_invoice/` must:
  - respect `MCP_ENABLE_WRITES`,
  - go through the existing write-logging hooks.
- **Deterministic behaviour**:
  - Tools either succeed and write clean JSON/PDF,
  - or fail loudly with a clear error – no half-written or silently corrupted data.

## What agents are expected to do

When modifying or extending this project, agents should:

- Keep the invoice model small and explicit.
- Prefer additional Pydantic validation over “helpful” auto-fixing of bad input.
- Add new tools in `bridge/backends/invoices.py` instead of ad-hoc scripts.
- Avoid introducing additional external services or databases.

The remaining tasks live in `.plan/TODO.md` and `.plan/tasks.manifest.json`.
Update `.plan/state.json` as work progresses.
