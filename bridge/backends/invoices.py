"""MCP backend for invoice creation and LaTeX rendering."""
from __future__ import annotations

import json
import logging
import subprocess
from datetime import date
from pathlib import Path
from typing import Any, Dict, Literal

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import ValidationError

from ..utils.config import ENABLE_WRITES, get_pdflatex_path
from ..utils.logging import record_write_attempt
from .invoices_models import (
    Invoice,
    LineItem,
    Party,
    PaymentStatus,
    _DATE_STYLE_DEFAULTS,
)
from .invoices_storage import (
    build_index,
    ensure_structure,
    get_invoice_root,
    next_invoice_number,
    save_index,
    save_invoice,
    with_index_lock,
    load_invoice,
)

_LOGGER = logging.getLogger("bridge.backends.invoices")
_TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "templates" / "invoice.tex"

# Discover pdflatex once at module load
_PDFLATEX_PATH = get_pdflatex_path()

DEFAULT_LIST_LIMIT = 20
MAX_LIST_LIMIT = 100


class WritesDisabled(RuntimeError):
    """Raised when write operations are attempted while disabled."""


def _require_writes_enabled() -> None:
    if not ENABLE_WRITES:
        raise WritesDisabled(
            "Write-capable tools are disabled. Set MCP_ENABLE_WRITES=1 to allow writes."
        )


def _load_index_payload() -> dict[str, object]:
    index_path = get_invoice_root() / "index.json"
    try:
        with index_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return {"count": 0, "invoices": []}


def _normalize_sort(sort_by: str | None, direction: str | None) -> tuple[str, str]:
    allowed_sort = {"invoice_date", "customer", "invoice_number", "total"}
    normalized_sort = sort_by if sort_by in allowed_sort else "invoice_date"
    normalized_direction = direction if direction in {"asc", "desc"} else "desc"
    return normalized_sort, normalized_direction


def coerce_total(entry: dict) -> float:
    """Convert an invoice entry's ``total`` field to a float safely."""

    try:
        return float(entry.get("total", 0) or 0)
    except (TypeError, ValueError):
        return 0.0


def _validate_limit(limit: int | None) -> int:
    try:
        parsed = int(limit) if limit is not None else DEFAULT_LIST_LIMIT
    except (TypeError, ValueError) as exc:
        raise ToolError("limit must be an integer") from exc

    if parsed < 1:
        raise ToolError("limit must be a positive integer")

    return min(parsed, MAX_LIST_LIMIT)


def _validate_offset(offset: int | None) -> int:
    try:
        parsed = int(offset) if offset is not None else 0
    except (TypeError, ValueError) as exc:
        raise ToolError("offset must be an integer") from exc

    if parsed < 0:
        raise ToolError("offset cannot be negative")

    return parsed


def get_invoice(invoice_id: str) -> Invoice:
    """Load an invoice by id with consistent error handling."""

    normalized_id = str(invoice_id).strip() if invoice_id is not None else ""
    if not normalized_id:
        raise ToolError("invoice_id is required")

    try:
        return load_invoice(normalized_id)
    except FileNotFoundError as exc:
        raise ToolError(f"Invoice {normalized_id} not found") from exc
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ToolError(f"Invoice {normalized_id} is invalid") from exc


def _sort_index_entries(entries: list[dict], sort_by: str, direction: str) -> list[dict]:
    key_funcs = {
        "invoice_date": lambda entry: (
            str(entry.get("invoice_date", "")),
            str(entry.get("invoice_number", "")),
        ),
        "customer": lambda entry: (
            str(entry.get("customer", "")).lower(),
            str(entry.get("invoice_number", "")),
        ),
        "invoice_number": lambda entry: (str(entry.get("invoice_number", "")),),
        "total": lambda entry: (
            coerce_total(entry),
            str(entry.get("invoice_number", "")),
        ),
    }

    key_func = key_funcs.get(sort_by, key_funcs["invoice_date"])
    reverse = direction == "desc"
    return sorted(entries, key=key_func, reverse=reverse)


def _filter_index_entries(
    entries: list[dict],
    *,
    status: str | None = None,
    payment_status: PaymentStatus | None = None,
    customer_query: str | None = None,
    invoice_date_from: date | None = None,
    invoice_date_to: date | None = None,
) -> list[dict]:
    filtered: list[dict] = []
    for entry in entries:
        if status and entry.get("status") != status:
            continue
        if payment_status and entry.get("payment_status") != payment_status:
            continue

        if customer_query:
            customer = str(entry.get("customer", ""))
            if customer_query.lower() not in customer.lower():
                continue

        invoice_date_value = None
        if invoice_date_from or invoice_date_to:
            try:
                invoice_date_value = date.fromisoformat(str(entry.get("invoice_date")))
            except Exception:
                continue

        if invoice_date_from and invoice_date_value and invoice_date_value < invoice_date_from:
            continue
        if invoice_date_to and invoice_date_value and invoice_date_value > invoice_date_to:
            continue

        filtered.append(entry)
    return filtered


def _parse_iso_date(value: str | None, field_name: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ToolError(f"Invalid {field_name}: expected YYYY-MM-DD") from exc


def list_invoices_impl(
    *,
    status: str | None = None,
    payment_status: PaymentStatus | None = None,
    customer_query: str | None = None,
    invoice_date_from: str | None = None,
    invoice_date_to: str | None = None,
    limit: int = DEFAULT_LIST_LIMIT,
    offset: int = 0,
    sort_by: str | None = None,
    direction: str | None = None,
    include_total_count: bool = True,
) -> Dict[str, Any]:
    """List invoice summaries from index.json with filters and pagination."""

    index = _load_index_payload()
    entries: list[dict] = index.get("invoices", []) if index else []

    date_from = _parse_iso_date(invoice_date_from, "invoice_date_from")
    date_to = _parse_iso_date(invoice_date_to, "invoice_date_to")

    filtered = _filter_index_entries(
        entries,
        status=status,
        payment_status=payment_status,
        customer_query=customer_query,
        invoice_date_from=date_from,
        invoice_date_to=date_to,
    )

    normalized_sort, normalized_dir = _normalize_sort(sort_by, direction)
    sorted_entries = _sort_index_entries(filtered, normalized_sort, normalized_dir)

    safe_limit = _validate_limit(limit)
    safe_offset = _validate_offset(offset)

    page = sorted_entries[safe_offset : safe_offset + safe_limit]
    summaries = [
        {
            "id": entry.get("id"),
            "invoice_number": entry.get("invoice_number"),
            "customer_name": entry.get("customer"),
            "invoice_date": entry.get("invoice_date"),
            "currency": entry.get("currency"),
            "total": entry.get("total"),
            "status": entry.get("status"),
            "payment_status": entry.get("payment_status"),
        }
        for entry in page
    ]

    total_count = len(filtered) if include_total_count else None
    has_more = safe_offset + safe_limit < len(filtered)
    next_offset = safe_offset + safe_limit if has_more else None

    return {
        "invoices": summaries,
        "total_count": total_count,
        "limit": safe_limit,
        "offset": safe_offset,
        "has_more": has_more,
        "next_offset": next_offset,
        "sort": {"by": normalized_sort, "direction": normalized_dir},
        "filters": {
            "status": status,
            "payment_status": payment_status,
            "customer_query": customer_query,
            "invoice_date_from": invoice_date_from,
            "invoice_date_to": invoice_date_to,
        },
    }


_LATEX_REPLACEMENTS = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "\\": r"\textbackslash{}",
}

_DATE_STYLES = {"iso", "locale"}


def _escape_tex(text: str) -> str:
    return "".join(_LATEX_REPLACEMENTS.get(ch, ch) for ch in text)


def _escape_multiline(text: str | None) -> str:
    if not text:
        return ""
    escaped = _escape_tex(text)
    return escaped.replace("\n", r"\\ " + "\n")


def _format_party_name(party: Party) -> str:
    """Format the party name, optionally including a trade/brand name on the next line."""

    lines = [_escape_tex(party.name)]
    if party.business_name:
        lines.append(_escape_tex(party.business_name))
    return r"\\ ".join(lines)


def _format_party_block(party: Party) -> str:
    lines = [_format_party_name(party)]
    lines.extend(
        [
            _escape_tex(party.street),
            _escape_tex(f"{party.postal_code} {party.city}"),
            _escape_tex(party.country),
        ]
    )
    return r"\\ ".join(line for line in lines if line)


_CONTACT_LABELS: dict[str, dict[str, str]] = {
    "de": {"email": "E-Mail", "phone": "Tel", "tax_id": "Steuernummer"},
    "en": {"email": "Email", "phone": "Phone", "tax_id": "Tax ID"},
}


def _format_contact(party: Party, language: str) -> str:
    labels = _CONTACT_LABELS.get(language, _CONTACT_LABELS["de"])
    parts = []
    if party.email:
        parts.append(f"{labels['email']}: {_escape_tex(party.email)}")
    if party.phone:
        parts.append(f"{labels['phone']}: {_escape_tex(party.phone)}")
    if party.tax_id:
        parts.append(f"{labels['tax_id']}: {_escape_tex(party.tax_id)}")
    return r"\\ ".join(parts)


def _format_date(value: date, language: str, date_style: str | None) -> str:
    style = date_style or _DATE_STYLE_DEFAULTS.get(language, "iso")
    if style not in _DATE_STYLES:
        raise ValueError("date_style must be 'iso' or 'locale'")

    if style == "iso":
        return value.isoformat()

    if language == "en":
        return value.strftime("%B %d, %Y")
    return value.strftime("%d.%m.%Y")


def _format_currency(value: float, currency: str, language: str | None = None) -> str:
    decimal_sep = "." if language == "en" else ","
    formatted = f"{value:.2f}"
    if decimal_sep != ".":
        formatted = formatted.replace(".", decimal_sep)
    return f"{formatted} {currency}"


def _format_quantity(item: LineItem) -> str:
    unit = _escape_tex(item.unit) if item.unit else ""
    return f"{item.quantity:g} {unit}".strip()


def _format_item_rows(invoice: Invoice) -> str:
    rows = []
    for idx, item in enumerate(invoice.items, start=1):
        line = " & ".join(
            [
                str(idx),
                _escape_tex(item.description),
                _format_quantity(item),
                _format_currency(item.unit_price, invoice.currency, invoice.language),
                _format_currency(item.total, invoice.currency, invoice.language),
            ]
        )
        rows.append(f"{line}\\\\")
    return "\n".join(rows)


_LABELS: dict[str, dict[str, str]] = {
    "de": {
        "INVOICE_TITLE": "Rechnung",
        "INVOICE_NUMBER": "Rechnungsnummer",
        "INVOICE_DATE": "Rechnungsdatum",
        "DUE_DATE": "Fällig bis",
        "SUBTOTAL": "Zwischensumme",
        "TOTAL": "Gesamtbetrag",
    },
    "en": {
        "INVOICE_TITLE": "Invoice",
        "INVOICE_NUMBER": "Invoice No.",
        "INVOICE_DATE": "Invoice date",
        "DUE_DATE": "Due date",
        "SUBTOTAL": "Subtotal",
        "TOTAL": "Total",
    },
}

_VAT_LABELS: dict[str, dict[str, str]] = {
    "de": {"vat": "USt", "total_suffix": "inkl. USt."},
    "en": {"vat": "VAT", "total_suffix": "incl. VAT"},
}


def _invoice_replacements(invoice: Invoice) -> Dict[str, str]:
    project_line = ""
    if invoice.project:
        project_line = f"Projekt: {_escape_tex(invoice.project)}\\\\"

    vat_labels = _VAT_LABELS.get(invoice.language, _VAT_LABELS["de"])

    small_business_note = (
        invoice.small_business_note if invoice.small_business else ""
    )

    vat_line = ""
    vat_amount = invoice.vat_amount()
    if not invoice.small_business and invoice.vat_rate > 0:
        vat_line = _format_currency(vat_amount, invoice.currency, invoice.language)

    labels = _LABELS.get(invoice.language, _LABELS["de"])
    total_label = labels["TOTAL"]
    if not invoice.small_business and invoice.vat_rate > 0:
        total_label = f"{labels['TOTAL']} ({vat_labels['total_suffix']})"

    footer_tax = invoice.footer_tax
    if not footer_tax and invoice.supplier.tax_id:
        tax_label = _CONTACT_LABELS.get(invoice.language, _CONTACT_LABELS["de"])[
            "tax_id"
        ]
        footer_tax = f"{tax_label}: {_escape_tex(invoice.supplier.tax_id)}"
    if not footer_tax:
        footer_tax = small_business_note

    return {
        "SENDER_NAME": _format_party_name(invoice.supplier),
        "SENDER_BLOCK": _format_party_block(invoice.supplier),
        "SENDER_CONTACT": _format_contact(invoice.supplier, invoice.language),
        "RECIPIENT_BLOCK": _format_party_block(invoice.customer),
        "INVOICE_NUMBER": _escape_tex(invoice.invoice_number),
        "INVOICE_DATE": _format_date(
            invoice.invoice_date, invoice.language, invoice.date_style
        ),
        "PROJECT_LINE": project_line,
        "DUE_DATE": _format_date(invoice.due_date, invoice.language, invoice.date_style),
        "INTRO_TEXT": _escape_multiline(invoice.intro_text),
        "OUTRO_TEXT": _escape_multiline(invoice.outro_text),
        "ITEM_ROWS": _format_item_rows(invoice),
        "SUBTOTAL": _format_currency(invoice.subtotal(), invoice.currency, invoice.language),
        "VAT_RATE": f"{invoice.vat_rate * 100:.1f}%" if vat_line else "",
        "VAT_AMOUNT": vat_line,
        "VAT_LABEL": vat_labels["vat"],
        "TOTAL_LABEL": _escape_tex(total_label),
        "TOTAL": _format_currency(invoice.total(), invoice.currency, invoice.language),
        "SMALL_BUSINESS_NOTE": _escape_multiline(small_business_note),
        "PAYMENT_TERMS": _escape_multiline(invoice.payment_terms),
        "FOOTER_BANK": _escape_multiline(invoice.footer_bank or ""),
        "FOOTER_TAX": _escape_multiline(footer_tax or ""),
        "LABEL_INVOICE_TITLE": _escape_tex(labels["INVOICE_TITLE"]),
        "LABEL_INVOICE_NUMBER": _escape_tex(labels["INVOICE_NUMBER"]),
        "LABEL_INVOICE_DATE": _escape_tex(labels["INVOICE_DATE"]),
        "LABEL_DUE_DATE": _escape_tex(labels["DUE_DATE"]),
        "LABEL_SUBTOTAL": _escape_tex(labels["SUBTOTAL"]),
    }


def _render_invoice(invoice: Invoice, root: Path | None = None) -> dict[str, Any]:
    if not _TEMPLATE_PATH.is_file():
        raise ToolError(f"Template not found at {_TEMPLATE_PATH}")

    ensure_structure(root)
    build_dir = get_invoice_root(root) / "build" / invoice.id
    build_dir.mkdir(parents=True, exist_ok=True)

    replacements = _invoice_replacements(invoice)
    tex_source = _TEMPLATE_PATH.read_text(encoding="utf-8")
    for key, value in replacements.items():
        tex_source = tex_source.replace(f"%%{key}%%", value)
    # Handle conditional VAT line placeholder
    if "%%VAT_LINE%%" in tex_source:
        vat_line = ""
        if replacements.get("VAT_AMOUNT"):
            vat_label = replacements.get("VAT_LABEL", "USt")
            vat_line = (
                f"{vat_label} ({replacements['VAT_RATE']}): & "
                f"{replacements['VAT_AMOUNT']}\\\\"
            )
        tex_source = tex_source.replace("%%VAT_LINE%%", vat_line)

    tex_path = build_dir / "invoice.tex"
    pdf_path = build_dir / "invoice.pdf"
    tex_path.write_text(tex_source, encoding="utf-8")

    # Check if pdflatex is available
    if not _PDFLATEX_PATH:
        error_msg = (
            "pdflatex not found. Please install TeX Live 2024+ or use one of these options:\n"
            "  1. Install TeX Live: https://tug.org/texlive/\n"
            "  2. Set PDFLATEX_PATH environment variable to your pdflatex binary\n"
            "  3. Use Docker: docker run -v $(pwd)/.mad_invoice:/app/.mad_invoice mad-invoice-mcp\n"
            "  4. For Debian/Ubuntu: apt-get install texlive-latex-base texlive-latex-extra"
        )
        raise ToolError(error_msg)

    last_result: subprocess.CompletedProcess[str] | None = None
    try:
        for _ in range(2):
            last_result = subprocess.run(
                [_PDFLATEX_PATH, "-interaction=nonstopmode", tex_path.name],
                cwd=build_dir,
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                check=True,
            )
    except FileNotFoundError as exc:
        error_msg = (
            f"pdflatex not found at: {_PDFLATEX_PATH}\n"
            "Please check your PDFLATEX_PATH or install TeX Live."
        )
        raise ToolError(error_msg) from exc
    except subprocess.CalledProcessError as exc:
        _LOGGER.error("pdflatex failed", extra={"stderr": exc.stderr})
        raise ToolError(f"pdflatex failed with exit code {exc.returncode}") from exc

    if last_result is not None:
        _LOGGER.debug("pdflatex output", extra={"stdout": last_result.stdout})
    return {
        "invoice_id": invoice.id,
        "tex_path": str(tex_path),
        "pdf_path": str(pdf_path),
    }


def update_invoice_status_impl(
    invoice_id: str, payment_status: PaymentStatus, status: str | None = None
) -> Dict[str, Any]:
    """Shared helper to update invoice statuses and rebuild index."""

    _require_writes_enabled()
    record_write_attempt()
    invoice = get_invoice(invoice_id)

    updated_fields: Dict[str, object] = {"payment_status": payment_status}
    if status is not None:
        # Prevent changing from "final" back to "draft" (one-way street)
        if invoice.status == "final" and status == "draft":
            raise ToolError(
                "Cannot change status from 'final' back to 'draft'. "
                "Finalized invoices are immutable."
            )
        updated_fields["status"] = status

    try:
        updated = invoice.model_copy(update=updated_fields)
    except Exception as exc:  # pydantic validation error
        raise ToolError(f"Failed to update invoice: {exc}") from exc

    with with_index_lock():
        save_invoice(updated)
        index = build_index()
        save_index(index)

    return {
        "invoice": updated.model_dump(mode="json"),
        "invoice_path": str(get_invoice_root() / "invoices" / f"{updated.id}.json"),
        "index_path": str(get_invoice_root() / "index.json"),
    }


def update_invoice_draft_impl(invoice_id: str, invoice: Invoice) -> Dict[str, Any]:
    """Update an existing draft invoice with new content."""

    _require_writes_enabled()
    record_write_attempt()

    # Load existing invoice
    existing = get_invoice(invoice_id)

    # Only allow editing drafts
    if existing.status != "draft":
        raise ToolError(
            f"Cannot edit invoice {invoice_id}: status is '{existing.status}'. "
            "Only drafts (status='draft') can be edited."
        )

    # Ensure the new invoice has the same ID
    if invoice.id != invoice_id:
        raise ToolError(
            f"Invoice ID mismatch: expected '{invoice_id}', got '{invoice.id}'"
        )

    # Enforce immutable draft-only fields
    if invoice.status != "draft":
        raise ToolError(
            "Draft edits must keep status='draft'. "
            f"Received status '{invoice.status}'."
        )

    if invoice.invoice_number != existing.invoice_number:
        raise ToolError(
            "Draft edits cannot change invoice_number. "
            f"Expected '{existing.invoice_number}', got '{invoice.invoice_number}'."
        )

    if invoice.payment_status != existing.payment_status:
        raise ToolError(
            "Draft edits cannot change payment_status. "
            f"Expected '{existing.payment_status}', got '{invoice.payment_status}'."
        )

    enforced_invoice = invoice.model_copy(
        update={
            "status": existing.status,
            "invoice_number": existing.invoice_number,
            "payment_status": existing.payment_status,
        }
    )

    with with_index_lock():
        save_invoice(enforced_invoice)
        index = build_index()
        save_index(index)

    return {
        "invoice": enforced_invoice.model_dump(mode="json"),
        "invoice_path": str(
            get_invoice_root() / "invoices" / f"{enforced_invoice.id}.json"
        ),
        "index_path": str(get_invoice_root() / "index.json"),
    }


def delete_invoice_draft_impl(invoice_id: str) -> Dict[str, Any]:
    """Delete a draft invoice."""

    _require_writes_enabled()
    record_write_attempt()

    # Load existing invoice
    existing = get_invoice(invoice_id)

    # Only allow deleting drafts
    if existing.status != "draft":
        raise ToolError(
            f"Cannot delete invoice {invoice_id}: status is '{existing.status}'. "
            "Only drafts (status='draft') can be deleted."
        )

    invoice_path = get_invoice_root() / "invoices" / f"{invoice_id}.json"

    with with_index_lock():
        invoice_path.unlink(missing_ok=True)
        index = build_index()
        save_index(index)

    return {
        "deleted_invoice_id": invoice_id,
        "deleted_path": str(invoice_path),
        "index_path": str(get_invoice_root() / "index.json"),
    }


def render_invoice_pdf_impl(invoice_id: str) -> Dict[str, Any]:
    """Shared helper to render an invoice to PDF."""

    _require_writes_enabled()
    record_write_attempt()
    invoice = get_invoice(invoice_id)
    return _render_invoice(invoice)


def register(server: FastMCP) -> None:
    """Register invoice tools."""

    @server.tool()
    def list_invoices(
        status: str | None = None,
        payment_status: PaymentStatus | None = None,
        customer_query: str | None = None,
        invoice_date_from: str | None = None,
        invoice_date_to: str | None = None,
        limit: int = DEFAULT_LIST_LIMIT,
        offset: int = 0,
        sort_by: str | None = None,
        direction: str | None = None,
        include_total_count: bool = True,
    ) -> Dict[str, Any]:
        """Read-only listing of invoice summaries from index.json with filters/pagination."""
        return list_invoices_impl(
            status=status,
            payment_status=payment_status,
            customer_query=customer_query,
            invoice_date_from=invoice_date_from,
            invoice_date_to=invoice_date_to,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            direction=direction,
            include_total_count=include_total_count,
        )

    @server.tool(name="get_invoice")
    def get_invoice_tool(invoice_id: str) -> Dict[str, Any]:
        """Read a full invoice JSON payload by id (read-only)."""

        invoice = get_invoice(invoice_id)
        return invoice.model_dump(mode="json")

    @server.tool()
    def create_invoice_draft(invoice: Invoice) -> Dict[str, Any]:
        """Persist a draft invoice to .mad_invoice/ and refresh the index.

        Input expectations for LLM callers:
        - supplier.name: Natural person name (required).
        - supplier.business_name: Optional trade/brand name; renders as second line under name.
        - footer_bank/footer_tax: Free-text blocks for payment and tax info (max ~500 chars each).
        - small_business=True disables VAT (German §19 UStG) and shows small_business_note; set vat_rate when False.

        Note: The backend enforces draft status and auto-generates both `id` and
        `invoice_number` using the yearly sequence, ignoring any client-provided
        values for those fields.
        """

        _require_writes_enabled()
        record_write_attempt()
        ensure_structure()

        number = next_invoice_number()

        enforced_invoice = invoice.model_copy(
            update={"id": number, "invoice_number": number, "status": "draft"}
        )

        invoice_path = get_invoice_root() / "invoices" / f"{enforced_invoice.id}.json"
        if invoice_path.exists():
            raise ToolError(
                f"Invoice {enforced_invoice.id} already exists at {invoice_path}"
            )

        with with_index_lock():
            save_invoice(enforced_invoice)
            index = build_index()
            save_index(index)

        return {
            "invoice": enforced_invoice.model_dump(mode="json"),
            "index_path": str(get_invoice_root() / "index.json"),
            "invoice_path": str(invoice_path),
        }

    @server.tool()
    def render_invoice_pdf(invoice_id: str) -> Dict[str, Any]:
        """Render an invoice to PDF using the LaTeX template.

        Resolves invoice JSON by id, fills `templates/invoice.tex`, and runs pdflatex.
        Keeps the sender name on two lines when both name and business_name are provided.
        """

        return render_invoice_pdf_impl(invoice_id)

    @server.tool()
    def update_invoice_status(
        invoice_id: str,
        payment_status: PaymentStatus,
        status: str | None = None,
    ) -> Dict[str, Any]:
        """Update invoice payment_status and optionally status, then rebuild index.

        payment_status must be one of: open | paid | overdue | cancelled.
        status is a free-form lifecycle flag (e.g., draft/final); pass when you need to change it.

        Note: Cannot change from 'final' back to 'draft' (finalized invoices are immutable).
        """

        return update_invoice_status_impl(invoice_id, payment_status, status)

    @server.tool()
    def update_invoice_draft(invoice_id: str, invoice: Invoice) -> Dict[str, Any]:
        """Update the complete content of a draft invoice.

        Allows editing all fields (parties, items, amounts, dates, etc.) of an invoice
        that is still in draft status.

        Restrictions:
        - Only works for invoices with status='draft'
        - The invoice.id in the payload must match invoice_id parameter
        - Once an invoice is finalized (status='final'), it cannot be edited

        Use this to correct mistakes or make changes before finalizing the invoice.
        """

        return update_invoice_draft_impl(invoice_id, invoice)

    @server.tool()
    def delete_invoice_draft(invoice_id: str) -> Dict[str, Any]:
        """Delete a draft invoice completely.

        Permanently removes an invoice and rebuilds the index.

        Restrictions:
        - Only works for invoices with status='draft'
        - Finalized invoices (status='final') cannot be deleted
        - The operation is irreversible

        Use this to remove unwanted or mistaken draft invoices.
        """

        return delete_invoice_draft_impl(invoice_id)

    @server.tool()
    def generate_invoice_number(separator: str | None = "-") -> Dict[str, Any]:
        """Return the next invoice number using a yearly counter (default: YYYY-####).

        - separator: defaults to "-", set to "" or null for no separator.
        - Counters are stored in .mad_invoice/sequence.json, one counter per year.
        """

        _require_writes_enabled()
        record_write_attempt()
        number = next_invoice_number(separator=separator)
        return {
            "invoice_number": number,
            "sequence_path": str(get_invoice_root() / "sequence.json"),
        }

    @server.tool()
    def get_invoice_template(
        language: Literal["de", "en"] = "de",
    ) -> Dict[str, Any]:
        """Return an example Invoice payload with sensible defaults and field hints.

        Field guidance for LLMs:
        - supplier.name: Natural person name (required).
        - supplier.business_name: Optional trade/brand name; appears under supplier.name in header/signature.
        - customer also supports business_name for B2B aliases.
        - footer_bank: Free text for payment details (IBAN, BIC, account holder).
        - footer_tax: Free text for tax info (Steuernummer/USt-IdNr.).
        - small_business=True: Apply German §19 UStG (no VAT); small_business_note is rendered.
        - small_business=False: Provide vat_rate between 0 and 1 (e.g., 0.19) to show VAT lines.
        - date_style: "iso" (YYYY-MM-DD) or "locale" (language-aware human format; default per language).
        - language: "de" or "en" for a localized example payload.
        """

        template_language: Literal["de", "en"] = (
            language if language in ("de", "en") else "de"
        )

        if template_language == "en":
            example = Invoice(
                id="2025-0001",
                invoice_number="2025-0001",
                invoice_date=date(2025, 3, 4),
                due_date=date(2025, 3, 18),
                date_style="iso",
                supplier=Party(
                    name="Max Mustermann",
                    business_name="M.A.D. Solutions",
                    street="Main Street 1",
                    postal_code="10115",
                    city="Berlin",
                    country="Germany",
                    email="hello@example.com",
                    phone="+49 30 123456",
                    tax_id="DE123456789",
                ),
                customer=Party(
                    name="ACME Ltd.",
                    street="42 Example Road",
                    postal_code="EC1A 1AA",
                    city="London",
                    country="United Kingdom",
                    email="accounts@acme.example",
                ),
                items=[
                    LineItem(
                        description="Consulting (architecture)",
                        quantity=2,
                        unit="hours",
                        unit_price=150.0,
                    ),
                    LineItem(
                        description="Implementation package",
                        quantity=1,
                        unit="package",
                        unit_price=800.0,
                    ),
                ],
                small_business=True,
                vat_rate=0.0,
                payment_terms="Payable within 14 days without deduction.",
                intro_text="Thanks for the collaboration!",
                outro_text="Please include the invoice number in all payments.",
                payment_status="open",
                status="draft",
                language="en",
                project="Sample Project",
            )
        else:
            example = Invoice(
                id="2025-0001",
                invoice_number="2025-0001",
                invoice_date=date(2025, 1, 15),
                due_date=date(2025, 1, 29),
                date_style="locale",
                supplier=Party(
                    name="Max Mustermann",
                    business_name="M.A.D. Solutions",
                    street="Hauptstr. 1",
                    postal_code="12345",
                    city="Berlin",
                    country="Deutschland",
                    email="info@example.com",
                    phone="+49 30 123456",
                    tax_id="DE123456789",
                ),
                customer=Party(
                    name="ACME GmbH",
                    street="Beispielweg 5",
                    postal_code="54321",
                    city="Hamburg",
                    country="Deutschland",
                ),
                items=[
                    LineItem(description="Beratung", quantity=2, unit="Std.", unit_price=150.0),
                    LineItem(description="Implementierung", quantity=1, unit="Paket", unit_price=800.0),
                ],
                small_business=False,
                vat_rate=0.19,
                payment_terms="Zahlbar innerhalb von 14 Tagen ohne Abzug.",
                intro_text="Vielen Dank für die Zusammenarbeit!",
                outro_text="Bitte geben Sie die Rechnungsnummer bei Zahlungen an.",
                payment_status="open",
                status="draft",
                language="de",
                project="Beispielprojekt",
            )
        return example.model_dump(mode="json")


__all__ = [
    "register",
    "render_invoice_pdf_impl",
    "update_invoice_status_impl",
    "update_invoice_draft_impl",
    "delete_invoice_draft_impl",
]
