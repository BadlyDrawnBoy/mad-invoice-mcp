#!/usr/bin/env python3
"""
Lightweight smoke test for mad-invoice-mcp.

Creates a sample invoice under a temp MAD_INVOICE_ROOT, writes index.json,
runs LaTeX rendering (requires pdflatex), and prints resulting paths.
"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridge.backends.invoices import render_invoice_pdf_impl
from bridge.backends.invoices_models import Invoice, LineItem, Party
from bridge.backends.invoices_storage import (
    build_index,
    ensure_structure,
    get_invoice_root,
    save_index,
    save_invoice,
)


def main() -> None:
    # Isolate into a temp directory unless MAD_INVOICE_ROOT is already set
    if "MAD_INVOICE_ROOT" not in os.environ:
        os.environ["MAD_INVOICE_ROOT"] = tempfile.mkdtemp(prefix="mad-invoice-smoke-")
    root = get_invoice_root()
    ensure_structure()

    today = date.today()
    inv = Invoice(
        id="smoke-0001",
        invoice_number="SMOKE-0001",
        invoice_date=today,
        due_date=today + timedelta(days=14),
        supplier=Party(
            name="M.A.D. Solutions",
            street="Main St 1",
            postal_code="12345",
            city="Berlin",
            country="Germany",
            tax_id="DE123456789",
        ),
        customer=Party(
            name="ACME GmbH",
            street="Exampleweg 5",
            postal_code="54321",
            city="Hamburg",
            country="Germany",
        ),
        items=[
            LineItem(description="Consulting", quantity=2, unit="hrs", unit_price=150.0),
            LineItem(description="Implementation", quantity=1, unit="package", unit_price=800.0),
        ],
        small_business=False,
        vat_rate=0.19,
        payment_terms="Due in 14 days.",
        payment_status="open",
    )

    save_invoice(inv)
    save_index(build_index())
    render_result = render_invoice_pdf_impl(inv.id)

    print(f"[smoke] MAD_INVOICE_ROOT={root}")
    print(f"[smoke] Invoice JSON: {render_result['invoice_id']}")
    print(f"[smoke] index.json: {root / 'index.json'}")
    print(f"[smoke] LaTeX: {render_result['tex_path']}")
    print(f"[smoke] PDF:   {render_result['pdf_path']}")
    print("[smoke] Done.")


if __name__ == "__main__":  # pragma: no cover
    main()
