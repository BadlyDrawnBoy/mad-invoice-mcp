# Orientation for agents (mad-invoice-mcp)

This repository hosts **mad-invoice-mcp**, a Python-based MCP server for
generating invoices as JSON + LaTeX + PDF for M.A.D. Solutions.

The goal:

- Provide a small, JSON-based invoice store that lives inside the project repo (`.mad_invoice/`),
- expose a minimal set of MCP tools for creating draft invoices and rendering them to PDF,
- keep the implementation **simple and deterministic** so it plays nicely with local LLM tools (OpenWebUI, Claude Code, Aider, etc.),
- avoid all the heavy Kraft/KDE / Office / Docker complexity.

Core behaviour:

- Invoices are stored as JSON files under `.mad_invoice/invoices/<id>.json`.
- `index.json` is a derived index built from all invoices.
- `render_invoice_pdf` fills `templates/invoice.tex` and runs `pdflatex`, writing PDFs under `.mad_invoice/build/<id>/invoice.pdf`.
- The server is intended for a **single company / single user** setup (M.A.D. Solutions).

For details on the current data model, see `bridge/backends/invoices_models.py`.  
For the storage layout and tools, see `bridge/backends/invoices_storage.py` and `bridge/backends/invoices.py`.

---

## Scope

You are **not** building a new MCP server from scratch.

The generic server wiring already exists under `bridge/app.py` and `bridge/api/`.  

Your job going forward is to:

1. **Polish and extend the invoice backend** (data model, tools, web UI).
2. Keep `.mad_invoice/` JSON storage simple, robust, and well-documented.
3. Add small quality-of-life features (status flags, web overview) that stay within the current design.

---

## Important constraints

- **Language:** Python only. Do not introduce other runtimes.
- **Storage:**
  - All invoice data lives as **plain JSON files** under `.mad_invoice/` in this repo.
  - No external database, no binary formats as primary source of truth.
- **Write gate:**
  - JSON under `.mad_invoice/` must only be modified via MCP tools.
  - Tools must validate data against Pydantic models (`Invoice`, `LineItem`, `Party`).
- **Safety:**
  - Respect existing write guards (`MCP_ENABLE_WRITES`, write counters, logging).

---

## Files and areas you SHOULD touch

- `bridge/backends/invoices_models.py` – extend the invoice model (e.g. payment status).  
- `bridge/backends/invoices_storage.py` – invoice filesystem helpers, index builder.  
- `bridge/backends/invoices.py` – MCP tools for creating drafts and rendering PDFs.  
- `templates/invoice.tex` – LaTeX layout and placeholders.  
- `bridge/app.py`, `scripts/bridge_stdio.py` – only if needed for wiring / transports.  

---

## Files and areas you SHOULD NOT touch without a good reason

- Generic logging / config helpers under `bridge/utils/` (beyond adding small flags).
- MCP core plumbing in `bridge/app.py` (except for minimal route additions).
- GitHub workflows or CI configuration (unless the task explicitly says so).

---

## Project root behaviour

By default the invoice store is expected under:

```text
.mad_invoice/
  invoices/<id>.json
  index.json
  build/<id>/invoice.tex|pdf
````

The working directory (or an optional env var like `MAD_INVOICE_ROOT`, if/when implemented) controls where this directory lives. The intent is: **single company, single invoice store**, no multi-project routing logic.
````
