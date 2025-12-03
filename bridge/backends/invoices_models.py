"""Pydantic models for invoice handling."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    confloat,
    conlist,
    field_validator,
    Field,
    model_validator,
)

PaymentStatus = Literal["open", "paid", "overdue", "cancelled"]


class Party(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    name: str = Field(max_length=256)
    street: str = Field(max_length=256)
    postal_code: str = Field(max_length=32)
    city: str = Field(max_length=128)
    country: str = "Deutschland"
    email: str | None = Field(default=None, max_length=256)
    phone: str | None = Field(default=None, max_length=64)
    tax_id: str | None = Field(default=None, max_length=64)


class LineItem(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    description: str = Field(max_length=512)
    quantity: confloat(gt=0) = 1.0
    unit: str = Field(default="Std.", max_length=32)
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

    payment_status: PaymentStatus = "open"
    language: Literal["de", "en"] = "de"
    supplier: Party
    customer: Party

    items: conlist(LineItem, min_length=1)

    currency: str = "EUR"
    small_business: bool = True  # §19 UStG
    vat_rate: confloat(ge=0, le=1) = 0.0  # applied when small_business is False

    intro_text: str | None = Field(default=None, max_length=2000)
    outro_text: str | None = Field(default=None, max_length=2000)
    payment_terms: str = Field(
        default="Zahlbar innerhalb von 14 Tagen ohne Abzug.", max_length=500
    )
    small_business_note: str = Field(
        "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet."
    )

    project: str | None = Field(default=None, max_length=256)
    footer_bank: str | None = Field(default=None, max_length=500)
    footer_tax: str | None = Field(default=None, max_length=500)

    @field_validator("due_date")
    def _due_date_not_before_invoice_date(cls, value: date, info):
        invoice_date = info.data.get("invoice_date")
        if invoice_date and value < invoice_date:
            raise ValueError("due_date cannot be before invoice_date")
        return value

    def subtotal(self) -> float:
        return sum(item.total for item in self.items)

    def total(self) -> float:
        if self.small_business:
            return self.subtotal()
        vat_amount = self.subtotal() * float(self.vat_rate)
        return self.subtotal() + vat_amount

    def vat_amount(self) -> float:
        if self.small_business:
            return 0.0
        return self.subtotal() * float(self.vat_rate)

    @model_validator(mode="after")
    def _ensure_non_negative_total(self) -> "Invoice":
        if self.subtotal() < 0:
            raise ValueError("Subtotal cannot be negative for invoices")
        return self

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
            "payment_status": self.payment_status,
            "status": self.status,
            "vat_rate": self.vat_rate,
            "language": self.language,
        }


__all__ = ["Invoice", "LineItem", "Party", "PaymentStatus"]
