"""
TODO – mad-invoice-mcp

Live task list for the project. Goal: lean, deterministic invoice MCP server with a simple web UI.
"""

---

## NOW (P1) – Small but valuable

- {MAD-INV-GITIGNORE}  
  Ensure `.mad_invoice/` is not committed to git (add `/.mad_invoice/` to `.gitignore`).

---

## DONE

- {MAD-INV-BOOTSTRAP}  
  Derived from re-kb-mcp, rebranded, implemented invoice models and LaTeX renderer, added `create_invoice_draft` and `render_invoice_pdf`.
- {MAD-INV-PAYMENT-STATUS}  
  Added `payment_status` to `Invoice` and index entries.
- {MAD-INV-STATUS-TOOL}  
  Implemented `update_invoice_status` MCP tool.
- {MAD-INV-WEB-OVERVIEW}  
  `GET /invoices` renders overview table from `index.json`.
- {MAD-INV-WEB-DETAIL}  
  `GET /invoices/{id}` shows metadata, items, PDF presence.
- {MAD-INV-WEB-ACTIONS}  
  POST actions for render and mark-paid wired to backend.
- {MAD-INV-VAT}  
  Optional VAT fields/logic added with template and detail view support.
- {MAD-INV-LANGUAGE}  
  Added `language` field on Invoice (de/en) for future label switching.
- {MAD-INV-INVARIANTS}  
  Added light validation guards and length limits for key fields; disallow negative subtotal.
- {MAD-INV-TEMPLATE-TOOL}  
  Added read-only `get_invoice_template` MCP tool returning sample payload.
- {MAD-INV-LOCALE-DATES}  
  Language-aware date formatting (`_format_date`) wired into replacements.
- {MAD-INV-LOCALE-CURRENCY}  
  Language-aware currency formatting (dot for English, comma otherwise).
- {MAD-INV-LANG-LABELS}  
  Language-aware labels and LaTeX placeholders added.
- {MAD-INV-PDF-DOUBLE-RUN}  
  `pdflatex` runs twice to resolve references.
- {MAD-INV-FONTS}  
  `lmodern` and `microtype` added for sharper PDF output.
- {MAD-INV-AUTONUM}  
  Implemented yearly sequence generator (`generate_invoice_number` tool, `sequence.json`).
***
