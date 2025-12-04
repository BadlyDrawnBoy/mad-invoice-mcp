import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridge.backends.invoices import list_invoices_impl


class ListInvoicesTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)

        self.invoice_root = Path(self.tempdir.name) / ".mad_invoice"
        self.invoice_root.mkdir(parents=True, exist_ok=True)

        self.env_patch = patch.dict(os.environ, {"MAD_INVOICE_ROOT": str(self.invoice_root)})
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

    def _write_index(self, entries: list[dict]):
        payload = {"count": len(entries), "invoices": entries}
        index_path = self.invoice_root / "index.json"
        index_path.write_text(json.dumps(payload), encoding="utf-8")

    def test_default_sort_and_pagination(self):
        entries = [
            {
                "id": "3",
                "invoice_number": "2024-0003",
                "invoice_date": "2024-03-05",
                "customer": "Zeta Corp",
                "currency": "EUR",
                "total": 300.0,
                "status": "final",
                "payment_status": "paid",
            },
            {
                "id": "1",
                "invoice_number": "2024-0001",
                "invoice_date": "2024-01-10",
                "customer": "Alpha GmbH",
                "currency": "EUR",
                "total": 100.0,
                "status": "draft",
                "payment_status": "open",
            },
            {
                "id": "2",
                "invoice_number": "2024-0002",
                "invoice_date": "2024-03-05",
                "customer": "Beta LLC",
                "currency": "USD",
                "total": 200.0,
                "status": "final",
                "payment_status": "open",
            },
        ]
        self._write_index(entries)

        response = list_invoices_impl(limit=2)

        invoice_numbers = [entry["invoice_number"] for entry in response["invoices"]]
        self.assertEqual(invoice_numbers, ["2024-0003", "2024-0002"])
        self.assertTrue(response["has_more"])
        self.assertEqual(response["next_offset"], 2)
        self.assertEqual(response["total_count"], 3)
        self.assertEqual(response["limit"], 2)
        self.assertEqual(response["offset"], 0)

    def test_filters_by_status_payment_and_customer(self):
        entries = [
            {
                "id": "1",
                "invoice_number": "2024-0001",
                "invoice_date": "2024-02-01",
                "customer": "Gamma Industries",
                "currency": "EUR",
                "total": 150.0,
                "status": "draft",
                "payment_status": "open",
            },
            {
                "id": "2",
                "invoice_number": "2024-0002",
                "invoice_date": "2024-02-02",
                "customer": "Acme Corporation",
                "currency": "EUR",
                "total": 200.0,
                "status": "final",
                "payment_status": "paid",
            },
            {
                "id": "3",
                "invoice_number": "2024-0003",
                "invoice_date": "2024-02-03",
                "customer": "Beta Labs",
                "currency": "USD",
                "total": 250.0,
                "status": "final",
                "payment_status": "overdue",
            },
        ]
        self._write_index(entries)

        response = list_invoices_impl(
            status="final",
            payment_status="paid",
            customer_query="acme",
        )

        self.assertEqual(len(response["invoices"]), 1)
        invoice = response["invoices"][0]
        self.assertEqual(invoice["invoice_number"], "2024-0002")
        self.assertEqual(invoice["customer_name"], "Acme Corporation")
        self.assertFalse(response["has_more"])
        self.assertIsNone(response["next_offset"])

    def test_invoice_date_range_and_limit_cap(self):
        entries = [
            {
                "id": "1",
                "invoice_number": "2024-0001",
                "invoice_date": "2024-01-10",
                "customer": "Alpha GmbH",
                "currency": "EUR",
                "total": 100.0,
                "status": "draft",
                "payment_status": "open",
            },
            {
                "id": "2",
                "invoice_number": "2024-0002",
                "invoice_date": "2024-02-15",
                "customer": "Beta GmbH",
                "currency": "EUR",
                "total": 200.0,
                "status": "final",
                "payment_status": "paid",
            },
            {
                "id": "3",
                "invoice_number": "2024-0003",
                "invoice_date": "2024-03-20",
                "customer": "Gamma GmbH",
                "currency": "EUR",
                "total": 300.0,
                "status": "final",
                "payment_status": "overdue",
            },
        ]
        self._write_index(entries)

        response = list_invoices_impl(
            invoice_date_from="2024-02-01",
            invoice_date_to="2024-02-28",
            limit=500,  # should be capped to hard max
        )

        invoice_numbers = [entry["invoice_number"] for entry in response["invoices"]]
        self.assertEqual(invoice_numbers, ["2024-0002"])
        self.assertEqual(response["limit"], 100)
        self.assertEqual(response["offset"], 0)
        self.assertFalse(response["has_more"])
        self.assertIsNone(response["next_offset"])


if __name__ == "__main__":
    unittest.main()
