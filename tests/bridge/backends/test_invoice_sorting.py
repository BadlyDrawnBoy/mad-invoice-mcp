import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridge.backends import invoices


def test_total_sort_handles_non_numeric_values():
    entries = [
        {
            "id": "valid",
            "invoice_number": "2024-0003",
            "total": 150.0,
        },
        {
            "id": "string-total",
            "invoice_number": "2024-0002",
            "total": "not-a-number",
        },
        {
            "id": "none-total",
            "invoice_number": "2024-0001",
            "total": None,
        },
    ]

    sorted_entries = invoices._sort_index_entries(entries, sort_by="total", direction="desc")
    invoice_numbers = [entry["invoice_number"] for entry in sorted_entries]

    assert invoice_numbers == [
        "2024-0003",  # highest numeric total first
        "2024-0002",  # both coerced to 0, invoice number is descending tiebreaker
        "2024-0001",
    ]
