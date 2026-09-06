import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

TOTAL_PATTERN = re.compile(
    r"(?i)(grand\s*total|total\s*amt|total)\s*[:\-]?\s*(?:rs\.?|₹|inr)?\s*([0-9]+(?:[.,][0-9]{1,2})?)"
)

DATE_PATTERN = re.compile(
    r"\b(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{4}[/\-]\d{1,2}[/\-]\d{1,2})\b"
)

LINE_ITEM_PATTERN = re.compile(
    r"^(.{2,40}?)\s+(?:x\s*\d+\s+)?([0-9]+(?:\.[0-9]{1,2})?)$"
)


@dataclass
class ParsedReceipt:
    vendor_name_guess: str
    date: Optional[str]
    total: float
    items: List[Tuple[str, str]] = field(default_factory=list)
    raw_text: str = ""


def parse_receipt(raw_text: str) -> ParsedReceipt:
    lines = [l.strip() for l in raw_text.split("\n")]

    vendor_guess = _guess_vendor_name(lines)

    total = 0.0
    total_match = TOTAL_PATTERN.search(raw_text)
    if total_match:
        try:
            total = float(total_match.group(2).replace(",", ""))
        except ValueError:
            pass

    date = None
    date_match = DATE_PATTERN.search(raw_text)
    if date_match:
        date = date_match.group(1)

    items: List[Tuple[str, str]] = []
    for line in lines:
        m = LINE_ITEM_PATTERN.match(line)
        if m:
            name, price = m.group(1).strip(), m.group(2).strip()
            if "total" in name.lower() or "tax" in name.lower():
                continue
            items.append((name, price))

    return ParsedReceipt(
        vendor_name_guess=vendor_guess,
        date=date,
        total=total,
        items=items,
        raw_text=raw_text,
    )


def _guess_vendor_name(lines: List[str]) -> str:
    for line in lines:
        if 3 <= len(line) <= 40:
            return line
    return "Unknown Vendor"
