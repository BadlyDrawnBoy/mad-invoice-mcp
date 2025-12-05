import json
import os
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("MCP_ENABLE_WRITES", "1")

from mcp.server.fastmcp.exceptions import ToolError

from bridge.backends.invoices import update_invoice_draft_impl
from bridge.backends.invoices_models import Invoice


class UpdateInvoiceDraftTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)

        self.invoice_root = Path(self.tempdir.name) / ".mad_invoice"
        self.invoice_root.mkdir(parents=True, exist_ok=True)

        self.env_patch = unittest.mock.patch.dict(
            os.environ,
            {
                "MAD_INVOICE_ROOT": str(self.invoice_root),
                "MCP_ENABLE_WRITES": "1",
            },
        )
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

    def _write_invoice(self, invoice: Invoice) -> Path:
        invoices_dir = self.invoice_root / "invoices"
        invoices_dir.mkdir(parents=True, exist_ok=True)
        path = invoices_dir / f"{invoice.id}.json"
        path.write_text(invoice.model_dump_json(indent=2), encoding="utf-8")
        return path

    def _sample_invoice(self) -> Invoice:
        payload = {
            "id": "2024-0001",
            "invoice_number": "2024-0001",
            "status": "draft",
            "invoice_date": "2024-01-10",
            "due_date": "2024-01-24",
            "payment_status": "open",
            "language": "de",
            "supplier": {
                "name": "Alice Example",
                "business_name": None,
                "street": "Example Street 1",
                "postal_code": "12345",
                "city": "Example City",
                "country": "Deutschland",
                "email": "alice@example.com",
                "phone": None,
                "tax_id": None,
            },
            "customer": {
                "name": "Bob GmbH",
                "business_name": None,
                "street": "Customer Ave 2",
                "postal_code": "54321",
                "city": "Customer City",
                "country": "Deutschland",
                "email": None,
                "phone": None,
                "tax_id": None,
            },
            "items": [
                {
                    "description": "Consulting",
                    "quantity": 2,
                    "unit": "Std.",
                    "unit_price": 150.0,
                }
            ],
            "currency": "EUR",
            "small_business": True,
            "vat_rate": 0.0,
            "payment_terms": "Zahlbar innerhalb von 14 Tagen ohne Abzug.",
            "small_business_note": None,
            "intro_text": None,
            "outro_text": None,
            "project": None,
            "footer_bank": None,
            "footer_tax": None,
            "date_style": "iso",
        }

        return Invoice.model_validate(payload)

    def test_rejects_status_change(self):
        invoice = self._sample_invoice()
        self._write_invoice(invoice)

        updated = invoice.model_copy(update={"status": "final"})

        with self.assertRaises(ToolError) as ctx:
            update_invoice_draft_impl(invoice.id, updated)

        self.assertIn("status='draft'", str(ctx.exception))

    def test_rejects_invoice_number_change(self):
        invoice = self._sample_invoice()
        self._write_invoice(invoice)

        updated = invoice.model_copy(update={"invoice_number": "2024-0099"})

        with self.assertRaises(ToolError) as ctx:
            update_invoice_draft_impl(invoice.id, updated)

        self.assertIn("invoice_number", str(ctx.exception))

    def test_rejects_payment_status_change(self):
        invoice = self._sample_invoice()
        self._write_invoice(invoice)

        updated = invoice.model_copy(update={"payment_status": "paid"})

        with self.assertRaises(ToolError) as ctx:
            update_invoice_draft_impl(invoice.id, updated)

        self.assertIn("payment_status", str(ctx.exception))

    def test_accepts_content_edits_when_fields_match(self):
        invoice = self._sample_invoice()
        self._write_invoice(invoice)

        updated_supplier = invoice.supplier.model_copy(update={"name": "Alice Updated"})
        updated = invoice.model_copy(update={"supplier": updated_supplier})

        result = update_invoice_draft_impl(invoice.id, updated)

        persisted = json.loads((self.invoice_root / "invoices" / f"{invoice.id}.json").read_text())

        self.assertEqual(result["invoice"]["supplier"]["name"], "Alice Updated")
        self.assertEqual(persisted["supplier"]["name"], "Alice Updated")
        self.assertEqual(persisted["status"], "draft")
        self.assertEqual(persisted["invoice_number"], invoice.invoice_number)
        self.assertEqual(persisted["payment_status"], invoice.payment_status)


if __name__ == "__main__":
    unittest.main()
