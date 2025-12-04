"""
TODO – mad-invoice-mcp

Live task list for the project. Goal: lean, deterministic invoice MCP server with a simple web UI.
"""

---

## NOW (P1) – Small but valuable

- {MAD-INV-INVOICE-READ-TOOLS}
  Define LLM-friendly read-only MCP tools for listing and fetching invoices so that agents can inspect existing data without file system access, while avoiding huge result sets.
  _Acceptance criteria_: The plan describes at least two tools:
  - `list_invoices`: reads `index.json` and returns a list of lightweight invoice summaries with strict pagination and filters:
    - supports filters for `status`, `payment_status`, `customer_query` (case-insensitive substring), and an optional date range (`invoice_date` from/to);
    - always enforces a `limit` parameter with a reasonable default (e.g. 20) and a hard maximum (e.g. 100), plus an `offset` or `cursor` for pagination;
    - results are returned in a deterministic order (e.g. newest `invoice_date` first, then by `invoice_number`), and the response includes metadata such as `total_count` (optional) and `has_more`/`next_offset`.
    - each summary object only contains id, invoice_number, customer_name, invoice_date, currency, total amount, status and payment_status (no full line items) to keep responses small.
  - `get_invoice`: loads a full invoice JSON by id and returns the complete `Invoice` object for detailed inspection.

## LATER (P2) – Nice to have

- {MAD-INV-CLIENTS-MCPO-EVAL}
  Evaluate whether the custom OpenWebUI shim should be replaced by mcpo, or whether the existing shim is intentionally kept.
  _Acceptance criteria_: A short decision note (e.g. in ADVANCED or `.plan/DECISIONS.md`) records: (a) whether mcpo works reliably with the current OpenWebUI version, (b) whether the project standard is "OpenWebUI via mcpo" or "OpenWebUI via internal shim", and (c) what changes would be required. The decision is briefly mirrored in README/ADVANCED.

- {MAD-INV-BRIDGE-DEPRECATION-PLAN}
  If mcpo or another standard path is adopted, define a clear deprecation plan for the current shim/SSE paths.
  _Acceptance criteria_: `.plan` contains a short deprecation note that states: (a) which paths/commands will be replaced long term, (b) from when on new users should only use the new path, and (c) how existing users can migrate. Shim/SSE are marked as "deprecated" or "legacy" in the docs once the alternative is considered stable.

## BACKLOG

- {MAD-INV-CREDIT-NOTES}  \
  Design how to model credit notes (negative totals, invoice type/flag vs normal invoices,
  and decide if/when to allow negative subtotals/totals in the model and tools).
  - Update invoice model/type to represent credit notes and adjust amount sign handling.
  - Add validation rules for negative subtotals/totals (including VAT and item lines) where appropriate.
  - Extend LaTeX rendering and UI views to display credit notes correctly (labels, signage, totals).

- {MAD-INV-BUILD-TIDY}
  Tidy up LaTeX artefacts in the build directory so that only the final PDF is kept by default.
  _Acceptance criteria_: After a successful PDF render, transient LaTeX files (e.g. `invoice.tex` and auxiliary files) are removed from `build/<invoice-id>/` while `invoice.pdf` is kept. There is an opt-in debug flag (e.g. `MAD_INVOICE_KEEP_TEX=1`) that, when enabled, keeps the LaTeX sources for troubleshooting.

- {MAD-INV-DEFAULT-SUPPLIER-CONFIG}
  Introduce a local config for default supplier details so LLMs and clients do not have to repeat them on every draft.
  _Acceptance criteria_: A config file under `.mad_invoice/` (e.g. `config.json`) supports a `default_supplier` object with fields such as name, business_name, address, tax IDs and contact info. `get_invoice_template()` and `create_invoice_draft()` automatically populate missing supplier fields from `default_supplier`, while still allowing explicit overrides from the client.

- {MAD-INV-DEFAULT-BANK-FOOTER}
  Add default bank/payment details to the MAD Invoice config so LLMs do not have to invent them on every draft.
  _Acceptance criteria_: The local config supports a `default_footer_bank` field containing bank name, IBAN, BIC and account holder. `get_invoice_template()` and `create_invoice_draft()` automatically use this value when `footer_bank` is missing or empty, while still allowing explicit overrides from the client. The docs explain that bank details normally come from this default and that agents should only override them when intentionally using a different account.

- {MAD-INV-CUSTOMER-NORMALIZATION}
  Add a light-weight normalisation step for customer data so that company names end up in `business_name` where appropriate.
  _Acceptance criteria_: When creating or updating an invoice, if `customer.business_name` is empty and `customer.name` looks like a company name (e.g. ends with common company suffixes such as "GmbH", "UG", "AG"), the system copies `name` into `business_name`. Rendering prefers `business_name` for company customers. The normalisation is best-effort only and does not block invoices if the heuristic does not apply.

- {MAD-INV-BACKUP-SCRIPT}
  Provide a simple backup script for the MAD Invoice data directory.
  _Acceptance criteria_: There is a script (e.g. `scripts/backup_mad_invoice.*`) that creates a timestamped archive (e.g. tar/zip) of the relevant `.mad_invoice/` contents (at least invoices, index, sequence and config). The script can be run manually and is documented briefly in the advanced docs.

- {MAD-INV-CHECKSUMS}
  Provide a checksum-based integrity check for the MAD Invoice data directory.
  _Acceptance criteria_: There is a script that computes SHA-256 (or similar) hashes for relevant files (invoice JSONs, `index.json`, `sequence.json`, config) and writes them to a manifest file. The script can also run in a verification mode that compares current hashes against the manifest and reports mismatches. This is intended as a tamper/integrity check, not as a security guarantee.

- {MAD-INV-HEALTHCHECK}
  Provide a simple healthcheck command for the MAD Invoice data store.
  _Acceptance criteria_: There is a script or command that reports basic health information: number of invoices, newest invoice (date/number) and whether `index.json` is consistent with the `invoices/` directory. A non-zero exit code indicates problems, which are described in the output.

- {MAD-INV-API-DOCS-AUTO}
  Add a small automation to regenerate the MCP tool/API documentation.
  _Acceptance criteria_: There is a script (e.g. `scripts/generate_api_docs.py`) and a build target (e.g. `make api-docs` or similar) that regenerates the MCP tool documentation file (e.g. `docs/api.md` or `docs/tools.md`) from the code. The README or docs mention how to run this command.

- {MAD-INV-DOCKER-GETTING-STARTED}
  Provide a step-by-step Docker-based getting started guide for new users.
  _Acceptance criteria_: There is a dedicated document (e.g. `docs/getting-started-docker.md` or a Docker section in `GETTING_STARTED.md`) that walks a new user through: prerequisites (Docker/Compose), building the image, starting a container with appropriate volumes/ports, and connecting a client (e.g. Claude Desktop or OpenWebUI). README contains a short "Getting Started" section with a brief Docker path and a link to this document.

- {MAD-INV-INVOICE-LLM-GUIDE}
  Provide a short guide or prompt snippet for LLMs that generate invoices via MAD Invoice.
  _Acceptance criteria_: There is a document (e.g. `docs/llm-invoice-guide.md`) that explains to agents how to use the tools correctly: how to fill supplier/customer fields (business_name vs. name), that `invoice_number` is assigned server-side, that bank details usually come from defaults, and that `list_invoices`/`get_invoice` should be used to inspect existing invoices. The guide is referenced from the main docs so it is discoverable for agent-focused setups.

---

## DONE

- {MAD-INV-WEB-SORTING}
  Added deterministic sorting controls to the invoice overview (customer, dates, invoice number, amount) with a clear default order when no sort is provided.

- {MAD-INV-ORIENTATION-DATA-ACCESS}
  Updated orientation/docs to steer agents toward MCP tools instead of direct `.mad_invoice/` access.

- {MAD-INV-CLIENTS-TARGETS}
  Supported MCP clients documented with usage modes; README includes the supported-clients table.

- {MAD-INV-OPENWEBUI-FLOW}
  OpenWebUI end-to-end flow documented with tested commands in ADVANCED.

- {MAD-INV-BRIDGE-LOGGING}
  Bridge/SSE entrypoint logs transport choice, ports, shim status, and write-mode warnings; port conflicts surface as explicit errors.

- {MAD-INV-OPENWEBUI-SMOKETEST}
  Added `scripts/smoke_openwebui_bridge.py` to probe the shim and return appropriate exit codes.

- {MAD-INV-BRIDGE-CODE-SCAN}
  Unified bridge entrypoint (`python -m bridge`) documented as the recommended path; legacy helpers marked as dev-only.

- {MAD-INV-AUTO-NUMBER}
  Draft creation enforces auto-generated IDs and invoice numbers via the yearly sequence helper.

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
