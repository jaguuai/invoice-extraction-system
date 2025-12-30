"""
Invoice Data Models
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from decimal import Decimal


class InvoiceItem(BaseModel):
    """Single item in invoice"""
    description: str = Field(..., description="Item description")
    quantity: float = Field(..., gt=0, description="Quantity")
    unit_price: float = Field(..., gt=0, description="Unit price")
    total_price: float = Field(..., gt=0, description="Total price")
    
    class Config:
        json_schema_extra = {
            "example": {
                "description": "Bilgisayar",
                "quantity": 2.0,
                "unit_price": 15000.0,
                "total_price": 30000.0
            }
        }


class InvoiceData(BaseModel):
    """Complete invoice data structure"""
    invoice_number: str = Field(..., description="Invoice number")
    invoice_date: str = Field(..., description="Invoice date (YYYY-MM-DD)")
    supplier_name: str = Field(..., description="Supplier name")
    supplier_tax_id: Optional[str] = Field(None, description="Supplier tax ID")
    supplier_address: Optional[str] = Field(None, description="Supplier address")
    customer_name: str = Field(..., description="Customer name")
    customer_tax_id: Optional[str] = Field(None, description="Customer tax ID")
    customer_address: Optional[str] = Field(None, description="Customer address")
    items: List[InvoiceItem] = Field(..., description="Invoice items")
    subtotal: float = Field(..., gt=0, description="Subtotal amount")
    vat_amount: float = Field(..., ge=0, description="VAT amount")
    vat_rate: float = Field(0.18, description="VAT rate (default 18%)")
    total_amount: float = Field(..., gt=0, description="Total amount")
    currency: str = Field("TRY", description="Currency code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "invoice_number": "2024/001",
                "invoice_date": "2024-12-29",
                "supplier_name": "ABC Teknoloji Ltd. Şti.",
                "supplier_tax_id": "1234567890",
                "customer_name": "XYZ Şirketi",
                "items": [
                    {
                        "description": "Laptop",
                        "quantity": 2,
                        "unit_price": 15000,
                        "total_price": 30000
                    }
                ],
                "subtotal": 30000.0,
                "vat_amount": 5400.0,
                "vat_rate": 0.18,
                "total_amount": 35400.0,
                "currency": "TRY"
            }
        }


class ExtractionRequest(BaseModel):
    """Request model for extraction endpoint"""
    file_name: str = Field(..., description="Uploaded file name")


class ExtractionResponse(BaseModel):
    """Response model for extraction endpoint"""
    status: str = Field(..., description="Status: success, error, processing")
    message: Optional[str] = Field(None, description="Status message")
    data: Optional[InvoiceData] = Field(None, description="Extracted invoice data")
    errors: Optional[List[str]] = Field(None, description="List of errors if any")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Invoice extracted successfully",
                "data": {
                    "invoice_number": "2024/001",
                    "invoice_date": "2024-12-29",
                    "total_amount": 35400.0
                },
                "errors": None
            }
        }
