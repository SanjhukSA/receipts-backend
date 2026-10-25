"""Pydantic schemas for request validation and response serialization."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LineItemBase(BaseModel):
    """
    Represents a single line item extracted from or submitted with a receipt.
    """
    name: str
    quantity: float = 1.0
    unit_price: float = 0.0
    total_price: float = 0.0


class LineItemOut(LineItemBase):
    """
    Serializes a persisted receipt line item with its database UUID.
    """
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class UploadResponse(BaseModel):
    """
    Returned by POST /receipts/upload (Step 1) with image upload metadata before OCR runs.
    """
    upload_id: str
    filename: str
    size_kb: float


class ProcessResponse(BaseModel):
    """
    Returned by POST /receipts/{upload_id}/process (Step 2) with extracted OCR data and GST details for review.
    """
    upload_id: str
    is_receipt: bool
    rejection_reason: Optional[str] = None
    vendor_name: str = "Unknown Vendor"
    date: Optional[str] = None
    gst_number: Optional[str] = None
    invoice_number: Optional[str] = None
    total: float = 0.0
    category: str = "Other"
    confidence: str = "high"
    total_auto_corrected: bool = False
    items: List[LineItemBase] = []
    raw_ocr_text: str = ""


class ReceiptCreate(BaseModel):
    """
    Request payload sent to POST /receipts (Step 3) to save a user-confirmed receipt to the database.
    """
    upload_id: str
    vendor_name: str = "Unknown Vendor"
    date: Optional[str] = None
    total: float = 0.0
    category: str = "Other"
    confidence: str = "high"
    total_auto_corrected: bool = False
    items: List[LineItemBase] = []
    raw_ocr_text: str = ""


class ReceiptUpdate(BaseModel):
    """
    Request payload sent to PATCH /receipts/{receipt_id} for partial updates to an existing receipt.
    """
    vendor_name: Optional[str] = None
    date: Optional[str] = None
    total: Optional[float] = None
    category: Optional[str] = None
    items: Optional[List[LineItemBase]] = None


class ReceiptOut(BaseModel):
    """
    Full receipt representation returned by detail and list endpoints, including image URLs and line items.
    """
    id: UUID
    vendor_name: str
    date: Optional[str] = None
    total: float
    category: str
    confidence: str
    total_auto_corrected: bool
    items: List[LineItemOut] = []
    raw_ocr_text: str
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedReceipts(BaseModel):
    """
    Wraps a paginated list of receipts along with total count and page metadata.
    """
    items: List[ReceiptOut]
    total: int
    page: int
    per_page: int
    pages: int


class DailySpend(BaseModel):
    """
    Represents the total amount spent on a specific calendar date for charting.
    """
    date: str
    total: float


class MonthlySummary(BaseModel):
    """
    Returned by GET /analytics/monthly with monthly spend totals, averages, and daily breakdown.
    """
    month: int
    year: int
    total_spent: float
    receipt_count: int
    avg_per_receipt: float
    previous_month_total: float
    daily_breakdown: List[DailySpend]


class CategoryBreakdownItem(BaseModel):
    """
    Returned by GET /analytics/categories for a single expense category's total, percentage, and count.
    """
    category: str
    total: float
    percentage: float
    count: int