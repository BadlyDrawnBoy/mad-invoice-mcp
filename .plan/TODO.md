"""
TODO – mad-invoice-mcp

Live task list for the project. Goal: lean, deterministic invoice MCP server with a simple web UI.
"""

---

## NOW (P1) – Small but valuable

- {MAD-INV-LOCALE-CONTACT}  \
  Make the contact line (email, phone, tax ID) language-aware, using German labels for `language="de"`
  and English equivalents for `language="en"`.

- {MAD-INV-SMALL-BUSINESS-NOTE}  \
  Provide German and English variants for the small-business note text referencing German VAT law,
  and wire it into replacements based on invoice language.

- {MAD-INV-VAT-LABELS}  \
  Use `USt` vs `VAT` labels in the LaTeX VAT line (and related labels) depending on invoice language,
  while keeping semantics tied to German VAT law.

- {MAD-INV-DRAFT-AUTONUM}  \
  Make `create_invoice_draft` always enforce `status="draft"` and always auto-generate `id` and
  `invoice_number` via the yearly sequence, ignoring any client-provided values; update README/LLM
  guidance accordingly.

- {MAD-INV-TEMPLATE-DE-EN}  \
  Split `get_invoice_template` into separate German/English examples (or add a language parameter),
  so sample invoices are fully consistent with their `language`.

- {MAD-INV-INDEX-CLEANUP}  \
  Clean up `Invoice.to_index_entry` (remove duplicate `status` key, ensure index fields match the
  current model and invariants).

## LATER (P2) – Nice to have

- {MAD-INV-WEB-SORTING}
  Add sorting functionality to invoice overview (by customer, date, invoice number, amount).
  Could use URL parameters (?sort=customer&order=asc) or JavaScript table sorting.

- {MAD-INV-AUTO-NUMBER}
  Consider auto-generating invoice_number if not provided (optional feature).
  Would call generate_invoice_number() automatically in create_invoice_draft.

## BACKLOG

- {MAD-INV-CREDIT-NOTES}  \
  Design how to model credit notes (negative totals, invoice type/flag vs normal invoices,
  and decide if/when to allow negative subtotals/totals in the model and tools).

- {MAD-INV-GITIGNORE}
  Ensure `.mad_invoice/` is not committed to git (add `/.mad_invoice/` to `.gitignore`).
  (Already done, but keeping for reference)

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
***
