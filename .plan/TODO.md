"""
TODO – mad-invoice-mcp

Live task list for the project. Goal: lean, deterministic invoice MCP server with a simple web UI.
"""

---

## NOW (P1) – Small but valuable

- {MAD-INV-GITIGNORE}  
  Ensure `.mad_invoice/` is not committed to git (add `/.mad_invoice/` to `.gitignore`).
- {MAD-INV-LOCALE-DATES}  
  Implement language-dependent date formatting in the renderer: in `bridge/backends/invoices.py`, add a function `_format_date(value: date, language: str)` which outputs `DD.MM.YYYY` for `language == "en"` and `YYYY-MM-DD` otherwise; in `_invoice_replacements()`, use `_format_date(..., invoice.language)` instead of `invoice.invoice_date.isoformat()` and `invoice.due_date.isoformat()`.
- {MAD-INV-LOCALE-CURRENCY}  
  Implement language-dependent currency formatting: extend `_format_currency(value, currency)` to optionally take the language into account (e.g., `_format_currency(value, currency, language)`); for `language == "en"`, use a comma as the decimal separator (`1234.56 EUR`), for other languages, use a period; adjust all calls to `_format_currency` so that `invoice.language` is passed.
- {MAD-INV-LANG-LABELS}  
  Introduce language-dependent labels for the LaTeX template: in `bridge/backends/invoices.py`, create a label map such as `_LABELS = {"de": {...}, "en": {...}}` with entries for e.g. “Rechnung”/“Invoice”, “Rechnungsnummer”/“Invoice No.”, “Rechnungsdatum”/“Invoice date”, “Fällig bis”/“Due date”, “Zwischensumme”/“Subtotal”, “Gesamtbetrag”/“Total”; in `_invoice_replacements()`, select the appropriate label set based on `invoice.language` and include placeholder values such as `LABEL_INVOICE_TITLE`, `LABEL_INVOICE_NUMBER`, `LABEL_INVOICE_DATE`, `LABEL_DUE_DATE`, `LABEL_SUBTOTAL`, `TOTAL_LABEL`; modify `templates/invoice.tex` to use these placeholders (e.g., `%%LABEL_INVOICE_TITLE%%` instead of hard-coded labels).
- {MAD-INV-PDF-DOUBLE-RUN}  
  Ensure that LaTeX runs at least twice for each invoice so that `\pageref{LastPage}` is resolved correctly: in `_render_invoice()` in `bridge/backends/invoices.py`, put the `pdflatex` call in a loop (e.g., `for _ in range(2): ...`) and abort cleanly in case of errors, as before.
- {MAD-INV-FONTS}  
  Improve the typeface in the LaTeX template: in `templates/invoice.tex`, add the packages `\usepackage{fontenc}`, `\usepackage{inputenc}`, `\usepackage{lmodern}`, and `\usepackage{microtype}` so that vector fonts and better kerning are used.
- {MAD-INV-AUTONUM}  
  Preparation for automatic invoice numbers: add a short TODO describing that invoice numbers should ideally be assigned by the backend in the future (e.g., via a sequence file under `.mad_invoice/sequence.json`) so the LLM does not generate numbers; only add the task description, not the implementation.

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
***
