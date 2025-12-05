import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.server.fastmcp.exceptions import ToolError

from bridge.backends.invoices import get_invoice


class GetInvoiceTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)

        self.invoice_root = Path(self.tempdir.name) / ".mad_invoice"
        self.invoice_root.mkdir(parents=True, exist_ok=True)

        self.env_patch = unittest.mock.patch.dict(
            os.environ, {"MAD_INVOICE_ROOT": str(self.invoice_root)}
        )
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

    def _write_invoice(self, invoice_id: str, payload: dict) -> Path:
        invoices_dir = self.invoice_root / "invoices"
        invoices_dir.mkdir(parents=True, exist_ok=True)
        path = invoices_dir / f"{invoice_id}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _sample_invoice(self) -> dict:
        return {
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

    def test_loads_valid_invoice(self):
        payload = self._sample_invoice()
        self._write_invoice(payload["id"], payload)

        invoice = get_invoice(payload["id"])

        self.assertEqual(invoice.id, payload["id"])
        self.assertEqual(invoice.invoice_number, payload["invoice_number"])
        self.assertEqual(invoice.customer.name, payload["customer"]["name"])
        self.assertEqual(len(invoice.items), 1)

    def test_missing_invoice_raises_tool_error(self):
        with self.assertRaises(ToolError) as ctx:
            get_invoice("missing-id")

        self.assertIn("Invoice missing-id not found", str(ctx.exception))

    def test_invalid_invoice_payload_raises_tool_error(self):
        payload = self._sample_invoice()
        payload.pop("due_date")  # invalid payload
        self._write_invoice(payload["id"], payload)

        with self.assertRaises(ToolError) as ctx:
            get_invoice(payload["id"])

        self.assertIn("is invalid", str(ctx.exception))

    def test_blank_invoice_id_rejected(self):
        with self.assertRaises(ToolError) as ctx:
            get_invoice("  ")

        self.assertIn("invoice_id is required", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
