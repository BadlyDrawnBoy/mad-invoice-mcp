"""Pydantic models for invoice handling."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, confloat, conlist, field_validator


class Party(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    name: str
    street: str
    postal_code: str
    city: str
    country: str = "Deutschland"
    email: str | None = None
    phone: str | None = None
    tax_id: str | None = None


class LineItem(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    description: str
    quantity: confloat(gt=0) = 1.0
    unit: str = "Std."
    unit_price: float  # may be negative for goodwill/discounts

    @property
    def total(self) -> float:
        return float(self.quantity) * float(self.unit_price)


class Invoice(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    id: str
    status: Literal["draft", "final"] = "draft"

    invoice_number: str
    invoice_date: date
    due_date: date

    supplier: Party
    customer: Party

    items: conlist(LineItem, min_items=1)

    currency: str = "EUR"
    small_business: bool = True  # §19 UStG

    intro_text: str | None = None
    outro_text: str | None = None
    payment_terms: str = "Zahlbar innerhalb von 14 Tagen ohne Abzug."
    small_business_note: str = (
        "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet."
    )

    project: str | None = None
    footer_bank: str | None = None
    footer_tax: str | None = None

    @field_validator("due_date")
    def _due_date_not_before_invoice_date(cls, value: date, info):
        invoice_date = info.data.get("invoice_date")
        if invoice_date and value < invoice_date:
            raise ValueError("due_date cannot be before invoice_date")
        return value

    def subtotal(self) -> float:
        return sum(item.total for item in self.items)

    def total(self) -> float:
        # Small business customers do not add VAT; extend here if VAT is added later.
        return self.subtotal()

    def to_index_entry(self) -> dict[str, object]:
        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "status": self.status,
            "invoice_date": self.invoice_date.isoformat(),
            "due_date": self.due_date.isoformat(),
            "customer": self.customer.name,
            "total": self.total(),
            "currency": self.currency,
        }


__all__ = ["Invoice", "LineItem", "Party"]
