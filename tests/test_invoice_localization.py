from datetime import date

from bridge.backends.invoices import _invoice_replacements
from bridge.backends.invoices_models import Invoice, LineItem, Party


def _build_invoice(**kwargs) -> Invoice:
    base = dict(
        id="2025-0001",
        invoice_number="2025-0001",
        invoice_date=date(2025, 1, 1),
        due_date=date(2025, 1, 10),
        supplier=Party(
            name="Max Mustermann",
            street="Hauptstr. 1",
            postal_code="10115",
            city="Berlin",
            country="Deutschland",
        ),
        customer=Party(
            name="ACME GmbH",
            street="Beispielweg 5",
            postal_code="54321",
            city="Hamburg",
            country="Deutschland",
        ),
        items=[LineItem(description="Dienstleistung", quantity=1, unit_price=100.0)],
    )
    base.update(kwargs)
    return Invoice(**base)


def test_small_business_note_defaults_by_language():
    de_invoice = _build_invoice(language="de", small_business=True, small_business_note=None)
    assert (
        de_invoice.small_business_note
        == "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet."
    )

    en_invoice = _build_invoice(language="en", small_business=True, small_business_note=None)
    assert (
        en_invoice.small_business_note
        == "According to section 19 UStG (German VAT law), no VAT is charged."
    )


def test_invoice_replacements_use_language_labels():
    invoice = _build_invoice(
        language="en",
        small_business=False,
        vat_rate=0.19,
        supplier=Party(
            name="Max Mustermann",
            street="Main Street 1",
            postal_code="10115",
            city="Berlin",
            country="Germany",
            email="hello@example.com",
            phone="+49 30 123456",
            tax_id="DE123456789",
        ),
    )

    replacements = _invoice_replacements(invoice)

    assert "Email:" in replacements["SENDER_CONTACT"]
    assert "Phone:" in replacements["SENDER_CONTACT"]
    assert replacements["VAT_LABEL"] == "VAT"
    assert "(incl. VAT)" in replacements["TOTAL_LABEL"]
