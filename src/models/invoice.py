"""
Invoice Data Models
Single source of truth for:
- OCR → Table parsing
- LLM semantic extraction
- Validation agents
- API responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional


# =========================
# INVOICE ITEM
# =========================
class InvoiceItem(BaseModel):
    """
    Represents a single invoice line item
    """

    item_no: Optional[int] = Field(
        None, description="Line number in invoice"
    )

    description: str = Field(
        ..., description="Item description"
    )

    quantity: Optional[float] = Field(
        None, description="Quantity"
    )

    unit_price: Optional[float] = Field(
        None, description="Unit price"
    )

    gross_amount: Optional[float] = Field(
        None, description="Total amount for this line"
    )

    confidence: Optional[float] = Field(
        None, description="Extraction confidence score"
    )


# =========================
# PARTY INFO
# =========================
class PartyInfo(BaseModel):
    """
    Seller or Buyer information
    """

    name: Optional[str] = Field(
        None, description="Company or person name"
    )

    address: Optional[str] = Field(
        None, description="Full address"
    )

    tax_id: Optional[str] = Field(
        None, description="Tax ID / VAT number"
    )

    tax_office: Optional[str] = Field(
        None, description="Tax office"
    )

    iban: Optional[str] = Field(
        None, description="IBAN"
    )

    phone: Optional[str] = Field(
        None, description="Phone number"
    )

    email: Optional[str] = Field(
        None, description="Email address"
    )


# =========================
# INVOICE ROOT
# =========================
class InvoiceData(BaseModel):
    """
    Root invoice structure
    """

    # ---- Identity ----
    invoice_number: Optional[str] = Field(
        None, description="Invoice number"
    )

    invoice_date: Optional[str] = Field(
        None, description="Invoice date"
    )

    currency: Optional[str] = Field(
        None, description="Currency code (TRY, USD, EUR)"
    )

    language: Optional[str] = Field(
        None, description="Detected language"
    )

    # ---- Parties ----
    seller: PartyInfo = Field(
        default_factory=PartyInfo
    )

    buyer: PartyInfo = Field(
        default_factory=PartyInfo
    )

    # ---- Items ----
    items: List[InvoiceItem] = Field(
        default_factory=list
    )

    # ---- Totals ----
    subtotal: Optional[float] = Field(
        None, description="Subtotal"
    )

    vat_total: Optional[float] = Field(
        None, description="Total VAT"
    )

    vat_rate: Optional[float] = Field(
        None, description="VAT rate"
    )

    grand_total: Optional[float] = Field(
        None, description="Final payable amount"
    )
