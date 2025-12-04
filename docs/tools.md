# MCP Tools

The server exposes these tools for LLM/MCP clients.

## Draft vs. Final Workflow

Invoices follow a **draft → final** lifecycle:

- **Draft (`status="draft"`)**: Fully editable, can be deleted
- **Final (`status="final"`)**: Immutable "sargnagel" - only PDF rendering and reading allowed

## `create_invoice_draft(invoice: Invoice)`
Create and save a new invoice (always starts as draft).

**Key fields for LLMs:**
- `supplier.name`: Natural person name (required)
- `supplier.business_name`: Optional trade/brand name (renders as second line)
- `small_business=True`: German §19 UStG (no VAT)
- `small_business=False`: Set `vat_rate` (e.g., `0.19`)
- `id`, `invoice_number`, `status`: Ignored; backend forces `status="draft"` and auto-numbers using the yearly sequence

Returns: `{invoice_path, index_path}`

## `update_invoice_draft(invoice_id: str, invoice: Invoice)`
Update the complete content of a draft invoice.

**Restrictions:**
- Only works for `status="draft"`
- Cannot edit finalized invoices

Use this to correct mistakes or make changes before finalizing.

Returns: `{invoice, invoice_path, index_path}`

## `delete_invoice_draft(invoice_id: str)`
Permanently delete a draft invoice.

**Restrictions:**
- Only works for `status="draft"`
- Cannot delete finalized invoices
- Irreversible operation

Returns: `{deleted_invoice_id, deleted_path, index_path}`

## `render_invoice_pdf(invoice_id: str)`
Render invoice to PDF using LaTeX template.

Works for both draft and final invoices.

Returns: `{pdf_path, tex_path}`

## `update_invoice_status(invoice_id, payment_status, status?)`
Update payment tracking and lifecycle status.

**payment_status:** `open | paid | overdue | cancelled`
**status:** `draft | final` (one-way: cannot change final → draft)

Use `status="final"` to finalize an invoice (makes it immutable).

Returns: `{invoice, invoice_path, index_path}`

## `generate_invoice_number(separator="-")`
Generate next invoice number (format: `YYYY-####`).

Pass `separator=""` or `null` for no separator.

Returns: `{invoice_number, sequence_path}`

## `get_invoice_template(language="de" | "en")`
Get localized example invoice payload with field documentation.

Returns: Example `Invoice` object
