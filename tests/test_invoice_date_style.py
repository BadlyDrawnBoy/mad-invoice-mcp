from datetime import date
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridge.backends.invoices import _format_date, _invoice_replacements
from bridge.backends.invoices_models import Invoice, LineItem, Party


class InvoiceDateStyleTests(unittest.TestCase):
    def _base_invoice(self, **overrides) -> Invoice:
        payload = dict(
            id="2024-0001",
            invoice_number="2024-0001",
            invoice_date=date(2024, 3, 5),
            due_date=date(2024, 3, 20),
            supplier=Party(
                name="Max Mustermann",
                street="Main St 1",
                postal_code="12345",
                city="Berlin",
                country="Deutschland",
            ),
            customer=Party(
                name="ACME GmbH",
                street="Exampleweg 5",
                postal_code="54321",
                city="Hamburg",
                country="Deutschland",
            ),
            items=[
                LineItem(description="Consulting", quantity=1, unit="hrs", unit_price=100.0)
            ],
        )
        payload.update(overrides)
        return Invoice(**payload)

    def test_defaults_follow_language(self):
        de_invoice = self._base_invoice(language="de")
        en_invoice = self._base_invoice(language="en")
        self.assertEqual(de_invoice.date_style, "locale")
        self.assertEqual(en_invoice.date_style, "iso")

    def test_formatting_by_style(self):
        sample_date = date(2024, 3, 5)
        self.assertEqual(_format_date(sample_date, "de", "iso"), "2024-03-05")
        self.assertEqual(_format_date(sample_date, "de", "locale"), "05.03.2024")
        self.assertEqual(
            _format_date(sample_date, "en", "locale"),
            "March 05, 2024",
        )

    def test_formatting_defaults_when_none(self):
        sample_date = date(2024, 3, 5)
        self.assertEqual(_format_date(sample_date, "de", None), "05.03.2024")
        self.assertEqual(_format_date(sample_date, "en", None), "2024-03-05")

    def test_invalid_style_raises(self):
        sample_date = date(2024, 3, 5)
        with self.assertRaises(ValueError):
            _format_date(sample_date, "en", "fancy")

    def test_replacements_use_invoice_date_style(self):
        invoice_locale = self._base_invoice(language="en", date_style="locale")
        replacements_locale = _invoice_replacements(invoice_locale)
        self.assertEqual(replacements_locale["INVOICE_DATE"], "March 05, 2024")
        self.assertEqual(replacements_locale["DUE_DATE"], "March 20, 2024")

        invoice_iso = self._base_invoice(language="de", date_style="iso")
        replacements_iso = _invoice_replacements(invoice_iso)
        self.assertEqual(replacements_iso["INVOICE_DATE"], "2024-03-05")
        self.assertEqual(replacements_iso["DUE_DATE"], "2024-03-20")


if __name__ == "__main__":
    unittest.main()
