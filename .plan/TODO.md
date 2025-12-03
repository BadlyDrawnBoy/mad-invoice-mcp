"""
TODO – mad-invoice-mcp

Live task list for the project. Goal: lean, deterministic invoice MCP server with a simple web UI.
"""

---

## NOW (P1) – Small but valuable

- {MAD-INV-GITIGNORE}  
  Ensure `.mad_invoice/` is not committed to git (add `/.mad_invoice/` to `.gitignore`).

- {MAD-INV-LANGUAGE}  
  Add `language: Literal["de", "en"] = "de"` to `Invoice`.  
  Optional follow-up: prepare a label table so renderer can switch key strings (Invoice/Rechnung) based on `invoice.language`.

- {MAD-INV-INVARIANTS}  
  Add light guards to `Invoice`: e.g., disallow negative totals for normal invoices; add simple length limits for free-text fields (`description`, `intro_text`, `outro_text`) to avoid LLM outliers.

- {MAD-INV-TEMPLATE-TOOL}  
  Add read-only MCP tool `get_invoice_template()` returning a sample `Invoice` JSON with sensible defaults for LLMs to fill.

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
***
