import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

TOTAL_PATTERN = re.compile(
    r"(?i)(grand\s*total|net\s*amount|amount\s*payable|total\s*amt|total)\s*[:\-]?\s*(?:rs\.?|₹|inr|\$)?\s*([0-9]+(?:[.,][0-9]{1,2})?)"
)

DATE_PATTERN = re.compile(
    r"\b(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{4}[/\-]\d{1,2}[/\-]\d{1,2})\b"
)

GSTIN_PATTERN = re.compile(
    r"\b(\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}Z[A-Z\d]{1})\b",
    re.IGNORECASE,
)

INVOICE_PATTERN = re.compile(
    r"(?i)(?:invoice\s*(?:no|number|#)|inv\s*(?:no|#)|bill\s*(?:no|number|#)|receipt\s*(?:no|#))\s*[:.\-]?\s*([A-Z0-9/\-_]{2,25})"
)

LINE_ITEM_PATTERN = re.compile(
    r"^(.{2,40}?)\s+(?:x\s*\d+\s+)?(?:rs\.?|₹|inr|\$)?\s*([0-9]+(?:\.[0-9]{1,2})?)$",
    re.IGNORECASE,
)

_CATEGORY_KEYWORDS = {
    "Health": ["pharmacy", "medical", "hospital", "clinic", "apollo", "medplus", "doctor", "diagnostic", "rx", "tablet", "mg"],
    "Food & Dining": ["restaurant", "cafe", "coffee", "pizza", "burger", "swiggy", "zomato", "kitchen", "bistro", "dine", "hotel"],
    "Groceries": ["supermarket", "mart", "fresh", "grocery", "kirana", "blinkit", "zepto", "instamart", "reliance smart", "dmart"],
    "Transport": ["uber", "ola", "rapido", "petrol", "fuel", "indian oil", "hpcl", "bpcl", "parking", "toll", "irctc", "metro"],
    "Bills & Utilities": ["electricity", "water", "broadband", "airtel", "jio", "vi", "recharge", "gas", "bill"],
    "Shopping": ["fashion", "trends", "zudio", "myntra", "amazon", "flipkart", "mall", "apparel", "store"],
}


@dataclass
class ParsedReceipt:
    vendor_name_guess: str
    date: Optional[str]
    gst_number: Optional[str]
    invoice_number: Optional[str]
    total: float
    items: List[Tuple[str, str]] = field(default_factory=list)
    raw_text: str = ""


def parse_receipt(raw_text: str) -> ParsedReceipt:
    """
    Args:
        raw_text: Raw multiline text extracted from a receipt image.
    Return:
        ParsedReceipt dataclass containing vendor, date, GSTIN, invoice number, total, and items.
    Extracts structured receipt fields from raw text using regular expressions.
    """
    lines = [l.strip() for l in raw_text.split("\n") if l.strip()]

    vendor_guess = _guess_vendor_name(lines)

    total = 0.0
    for line in reversed(lines):
        total_match = TOTAL_PATTERN.search(line)
        if total_match:
            try:
                total = float(total_match.group(2).replace(",", ""))
                break
            except ValueError:
                pass

    date = None
    date_match = DATE_PATTERN.search(raw_text)
    if date_match:
        date = date_match.group(1)

    gst_number = None
    gst_match = GSTIN_PATTERN.search(raw_text)
    if gst_match:
        gst_number = gst_match.group(1).upper()

    invoice_number = None
    inv_match = INVOICE_PATTERN.search(raw_text)
    if inv_match:
        invoice_number = inv_match.group(1).strip()

    items: List[Tuple[str, str]] = []
    for line in lines:
        m = LINE_ITEM_PATTERN.match(line)
        if m:
            name, price = m.group(1).strip(), m.group(2).strip()
            if any(k in name.lower() for k in ("total", "tax", "cgst", "sgst", "igst", "subtotal", "discount", "cash", "change")):
                continue
            items.append((name, price))

    return ParsedReceipt(
        vendor_name_guess=vendor_guess,
        date=date,
        gst_number=gst_number,
        invoice_number=invoice_number,
        total=total,
        items=items,
        raw_text=raw_text,
    )


def _guess_vendor_name(lines: List[str]) -> str:
    """
    Args:
        lines: Non-empty text lines from the receipt.
    Return:
        Guessed vendor name string or 'Unknown Vendor'.
    Finds the first non-header line at the top of the receipt as the store name.
    """
    for line in lines:
        if line.lower() in ("tax invoice", "cash memo", "receipt", "bill of supply", "invoice"):
            continue
        if 3 <= len(line) <= 40:
            return line
    return "Unknown Vendor"


def _guess_category(raw_text: str) -> str:
    """
    Args:
        raw_text: Raw multiline OCR text.
    Return:
        Matched category name or 'Other'.
    Classifies the receipt into an expense category using keyword matching.
    """
    lower_text = raw_text.lower()
    for category, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in lower_text for kw in keywords):
            return category
    return "Other"


def parse_receipt_to_dict(raw_text: str) -> dict:
    """
    Args:
        raw_text: Raw multiline text from local OCR.
    Return:
        Dictionary normalized to the OcrEngine response format.
    Converts local regex-parsed receipt fields into the standard OCR response dict.
    """
    if not raw_text or len(raw_text.strip()) < 10:
        return {
            "is_receipt": False,
            "rejection_reason": "No readable text found on image (Local Privacy Mode).",
        }

    parsed = parse_receipt(raw_text)

    structured_items = []
    for name, price_str in parsed.items:
        try:
            price = float(price_str.replace(",", ""))
        except ValueError:
            price = 0.0
        if price > 0:
            structured_items.append(
                {
                    "name": name,
                    "quantity": 1.0,
                    "unit_price": price,
                    "total_price": price,
                }
            )

    item_sum = round(sum(i["total_price"] for i in structured_items), 2)
    total = parsed.total
    total_auto_corrected = False

    if total == 0.0 and item_sum > 0:
        total = item_sum
        total_auto_corrected = True

    if total == 0.0 and not structured_items:
        return {
            "is_receipt": False,
            "rejection_reason": "Could not detect prices or a transaction total (Local Privacy Mode).",
        }

    return {
        "is_receipt": True,
        "rejection_reason": None,
        "confidence": "medium",
        "vendor_name": parsed.vendor_name_guess,
        "date": parsed.date,
        "gst_number": parsed.gst_number,
        "invoice_number": parsed.invoice_number,
        "total": total,
        "category": _guess_category(raw_text),
        "total_auto_corrected": total_auto_corrected,
        "items": structured_items,
        "raw_text": raw_text,
    }