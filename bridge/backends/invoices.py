"""MCP backend for invoice creation and LaTeX rendering."""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from ..utils.config import ENABLE_WRITES
from ..utils.logging import record_write_attempt
from .invoices_models import Invoice, LineItem, Party, PaymentStatus
from .invoices_storage import (
    build_index,
    ensure_structure,
    get_invoice_root,
    save_index,
    save_invoice,
    with_index_lock,
    load_invoice,
)

_LOGGER = logging.getLogger("bridge.backends.invoices")
_TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "templates" / "invoice.tex"


class WritesDisabled(RuntimeError):
    """Raised when write operations are attempted while disabled."""


def _require_writes_enabled() -> None:
    if not ENABLE_WRITES:
        raise WritesDisabled(
            "Write-capable tools are disabled. Set MCP_ENABLE_WRITES=1 to allow writes."
        )


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


def _escape_tex(text: str) -> str:
    return "".join(_LATEX_REPLACEMENTS.get(ch, ch) for ch in text)


def _escape_multiline(text: str | None) -> str:
    if not text:
        return ""
    escaped = _escape_tex(text)
    return escaped.replace("\n", r"\\ " + "\n")


def _format_party_block(party: Party) -> str:
    lines = [
        _escape_tex(party.name),
        _escape_tex(party.street),
        _escape_tex(f"{party.postal_code} {party.city}"),
        _escape_tex(party.country),
    ]
    return r"\\ ".join(line for line in lines if line)


def _format_contact(party: Party) -> str:
    parts = []
    if party.email:
        parts.append(f"E-Mail: {_escape_tex(party.email)}")
    if party.phone:
        parts.append(f"Tel: {_escape_tex(party.phone)}")
    if party.tax_id:
        parts.append(f"Steuernummer: {_escape_tex(party.tax_id)}")
    return r"\\ ".join(parts)


def _format_currency(value: float, currency: str) -> str:
    return f"{value:.2f} {currency}"


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
                _format_currency(item.unit_price, invoice.currency),
                _format_currency(item.total, invoice.currency),
            ]
        )
        rows.append(f"{line}\\\\")
    return "\n".join(rows)


def _invoice_replacements(invoice: Invoice) -> Dict[str, str]:
    project_line = ""
    if invoice.project:
        project_line = f"Projekt: {_escape_tex(invoice.project)}\\\\"

    small_business_note = (
        invoice.small_business_note if invoice.small_business else ""
    )

    vat_line = ""
    vat_amount = invoice.vat_amount()
    if not invoice.small_business and invoice.vat_rate > 0:
        vat_line = _format_currency(vat_amount, invoice.currency)

    total_label = "Gesamtbetrag"
    if not invoice.small_business and invoice.vat_rate > 0:
        total_label = "Gesamtbetrag (inkl. USt.)"

    footer_tax = invoice.footer_tax
    if not footer_tax and invoice.supplier.tax_id:
        footer_tax = f"Steuernummer: {_escape_tex(invoice.supplier.tax_id)}"
    if not footer_tax:
        footer_tax = small_business_note

    return {
        "SENDER_NAME": _escape_tex(invoice.supplier.name),
        "SENDER_BLOCK": _format_party_block(invoice.supplier),
        "SENDER_CONTACT": _format_contact(invoice.supplier),
        "RECIPIENT_BLOCK": _format_party_block(invoice.customer),
        "INVOICE_NUMBER": _escape_tex(invoice.invoice_number),
        "INVOICE_DATE": invoice.invoice_date.isoformat(),
        "PROJECT_LINE": project_line,
        "DUE_DATE": invoice.due_date.isoformat(),
        "INTRO_TEXT": _escape_multiline(invoice.intro_text),
        "OUTRO_TEXT": _escape_multiline(invoice.outro_text),
        "ITEM_ROWS": _format_item_rows(invoice),
        "SUBTOTAL": _format_currency(invoice.subtotal(), invoice.currency),
        "VAT_RATE": f"{invoice.vat_rate * 100:.1f}%" if vat_line else "",
        "VAT_AMOUNT": vat_line,
        "TOTAL_LABEL": total_label,
        "TOTAL": _format_currency(invoice.total(), invoice.currency),
        "SMALL_BUSINESS_NOTE": _escape_multiline(small_business_note),
        "PAYMENT_TERMS": _escape_multiline(invoice.payment_terms),
        "FOOTER_BANK": _escape_multiline(invoice.footer_bank or ""),
        "FOOTER_TAX": _escape_multiline(footer_tax or ""),
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
            vat_line = f"USt ({replacements['VAT_RATE']}): & {replacements['VAT_AMOUNT']}\\\\"
        tex_source = tex_source.replace("%%VAT_LINE%%", vat_line)

    tex_path = build_dir / "invoice.tex"
    pdf_path = build_dir / "invoice.pdf"
    tex_path.write_text(tex_source, encoding="utf-8")

    try:
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", tex_path.name],
            cwd=build_dir,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as exc:
        raise ToolError("pdflatex not found. Install a TeX distribution to render PDFs.") from exc
    except subprocess.CalledProcessError as exc:
        _LOGGER.error("pdflatex failed", extra={"stderr": exc.stderr})
        raise ToolError(f"pdflatex failed with exit code {exc.returncode}") from exc

    _LOGGER.debug("pdflatex output", extra={"stdout": result.stdout})
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
    invoice = load_invoice(invoice_id)

    updated_fields: Dict[str, object] = {"payment_status": payment_status}
    if status is not None:
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


def render_invoice_pdf_impl(invoice_id: str) -> Dict[str, Any]:
    """Shared helper to render an invoice to PDF."""

    _require_writes_enabled()
    record_write_attempt()
    invoice = load_invoice(invoice_id)
    return _render_invoice(invoice)


def register(server: FastMCP) -> None:
    """Register invoice tools."""

    @server.tool()
    def create_invoice_draft(invoice: Invoice) -> Dict[str, Any]:
        """Persist a draft invoice to .mad_invoice/ and refresh the index."""

        _require_writes_enabled()
        record_write_attempt()
        ensure_structure()

        invoice_path = get_invoice_root() / "invoices" / f"{invoice.id}.json"
        if invoice_path.exists():
            raise ToolError(f"Invoice {invoice.id} already exists at {invoice_path}")

        with with_index_lock():
            save_invoice(invoice)
            index = build_index()
            save_index(index)

        return {
            "invoice": invoice.model_dump(mode="json"),
            "index_path": str(get_invoice_root() / "index.json"),
            "invoice_path": str(invoice_path),
        }

    @server.tool()
    def render_invoice_pdf(invoice_id: str) -> Dict[str, Any]:
        """Render an invoice to PDF using the LaTeX template."""

        return render_invoice_pdf_impl(invoice_id)

    @server.tool()
    def update_invoice_status(
        invoice_id: str,
        payment_status: PaymentStatus,
        status: str | None = None,
    ) -> Dict[str, Any]:
        """Update invoice payment_status and optionally status, then rebuild index."""

        return update_invoice_status_impl(invoice_id, payment_status, status)


__all__ = [
    "register",
    "render_invoice_pdf_impl",
    "update_invoice_status_impl",
]
