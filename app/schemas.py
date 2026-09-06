from typing import List, Optional
from pydantic import BaseModel


class LineItem(BaseModel):
    name: str
    price: str


class ParsedReceiptOut(BaseModel):
    vendor_name_guess: str
    date: Optional[str] = None
    total: float
    items: List[LineItem] = []
    raw_ocr_text: str
