import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridge.web import DEFAULT_DIRECTION, DEFAULT_SORT, _normalize_sort, _sort_index_entries


class InvoiceSortingTests(unittest.TestCase):
    def setUp(self):
        self.sample_entries = [
            {
                "id": "c",
                "invoice_number": "2024-0003",
                "invoice_date": "2024-03-15",
                "due_date": "2024-03-30",
                "customer": "Beta",
                "total": 150.0,
            },
            {
                "id": "b",
                "invoice_number": "2024-0002",
                "invoice_date": "2024-03-15",
                "due_date": "2024-03-28",
                "customer": "Alpha",
                "total": 200.0,
            },
            {
                "id": "a",
                "invoice_number": "2024-0001",
                "invoice_date": "2024-03-15",
                "due_date": "2024-03-28",
                "customer": "alpha",
                "total": 200.0,
            },
        ]

    def test_normalize_sort_defaults_and_rejections(self):
        sort_by, direction = _normalize_sort(None, None)
        self.assertEqual(sort_by, DEFAULT_SORT)
        self.assertEqual(direction, DEFAULT_DIRECTION)

        sort_by, direction = _normalize_sort("total", "asc")
        self.assertEqual(sort_by, "total")
        self.assertEqual(direction, "asc")

        # invalid entries fall back to defaults
        sort_by, direction = _normalize_sort("bogus", "sideways")
        self.assertEqual(sort_by, DEFAULT_SORT)
        self.assertEqual(direction, DEFAULT_DIRECTION)

    def test_customer_sort_is_stable(self):
        sorted_entries = _sort_index_entries(self.sample_entries, sort_by="customer", direction="asc")
        invoice_numbers = [entry["invoice_number"] for entry in sorted_entries]
        self.assertEqual(invoice_numbers, ["2024-0001", "2024-0002", "2024-0003"])

    def test_due_date_sort_desc(self):
        sorted_entries = _sort_index_entries(self.sample_entries, sort_by="due_date", direction="desc")
        invoice_numbers = [entry["invoice_number"] for entry in sorted_entries]
        # Two entries share the same due date; invoice_number acts as tiebreaker
        self.assertEqual(invoice_numbers, ["2024-0003", "2024-0002", "2024-0001"])

    def test_invoice_date_sort_desc_defaults(self):
        sorted_entries = _sort_index_entries(self.sample_entries, sort_by="invoice_date", direction="desc")
        invoice_numbers = [entry["invoice_number"] for entry in sorted_entries]
        # All entries share the same date so invoice number is used to ensure deterministic ordering
        self.assertEqual(invoice_numbers, ["2024-0003", "2024-0002", "2024-0001"])

    def test_total_sort_handles_non_numeric(self):
        entries = self.sample_entries + [
            {
                "id": "d",
                "invoice_number": "2024-0004",
                "invoice_date": "2024-03-16",
                "due_date": "2024-03-29",
                "customer": "Gamma",
                "total": "invalid",
            }
        ]

        sorted_entries = _sort_index_entries(entries, sort_by="total", direction="desc")
        invoice_numbers = [entry["invoice_number"] for entry in sorted_entries]

        self.assertEqual(invoice_numbers, [
            "2024-0002",
            "2024-0001",
            "2024-0003",
            "2024-0004",
        ])


if __name__ == "__main__":
    unittest.main()
