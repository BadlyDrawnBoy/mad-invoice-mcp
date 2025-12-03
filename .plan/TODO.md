"""
TODO – mad-invoice-mcp

Live task list for the project. Goal: lean, deterministic invoice MCP server with a simple web UI.
"""

---

## NOW (P1) – Small but valuable

- {MAD-INV-WEB-SORTING}
  Add sorting functionality to invoice overview (by customer, date, invoice number, amount).
  _Acceptance criteria_: Overview lists can be sorted by at least customer and date via a deterministic control (URL or UI toggle) with clear default ordering when no sort is provided.

- {MAD-INV-AUTO-NUMBER}
  Consider auto-generating invoice_number if not provided (optional feature).
  _Acceptance criteria_: Creating a draft without `invoice_number` produces a valid number using the sequence helper, while providing an explicit number still works unchanged.

## LATER (P2) – Nice to have

_(none)_

## BACKLOG

- {MAD-INV-CREDIT-NOTES}  \
  Design how to model credit notes (negative totals, invoice type/flag vs normal invoices,
  and decide if/when to allow negative subtotals/totals in the model and tools).
  - Update invoice model/type to represent credit notes and adjust amount sign handling.
  - Add validation rules for negative subtotals/totals (including VAT and item lines) where appropriate.
  - Extend LaTeX rendering and UI views to display credit notes correctly (labels, signage, totals).

---

## DONE

- {MAD-INV-DATE-STYLE}
  Added `date_style` field with defaults, validation, and rendering for ISO vs locale-specific formats.

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
- {MAD-INV-DRAFT-FINAL}
  Implemented draft/final workflow with update_invoice_draft, delete_invoice_draft tools.
  Added guards to prevent editing/deleting final invoices.
- {MAD-INV-WEB-DRAFT-FINAL}
  Added finalize and delete buttons to web UI with conditional rendering.
- {MAD-INV-PDFLATEX-DISCOVERY}
  Auto-discovery of pdflatex in system PATH and common TeX Live locations.
- {MAD-INV-WEB-CUSTOMER-DETAILS}
  Expanded customer/supplier display with full address and contact info.
- {MAD-INV-LOCALE-CONTACT}
  Localized contact labels (email/phone/tax ID) for German and English invoices.
- {MAD-INV-SMALL-BUSINESS-NOTE}
  Added German and English variants for the §19 UStG small-business note and hooked language-based rendering.
- {MAD-INV-VAT-LABELS}
  Language-aware VAT labels (`USt` vs `VAT`) in totals and VAT lines.
- {MAD-INV-DRAFT-AUTONUM}
  `create_invoice_draft` now forces draft status and auto-generates ids/invoice numbers via the yearly sequence.
- {MAD-INV-TEMPLATE-DE-EN}
  `get_invoice_template` offers localized German/English sample payloads via a language parameter.
- {MAD-INV-INDEX-CLEANUP}
  Cleaned `Invoice.to_index_entry` to remove duplicate keys and align index fields with current invariants.
- {MAD-INV-GITIGNORE}
  Added `/.mad_invoice/` to `.gitignore` to avoid committing workspace artifacts.
***
