"""Receipt OCR engines powered by Google Gemini Flash and local RapidOCR."""

import io
import json
import re
import uuid
from pathlib import Path

import numpy as np
from google import genai
from google.genai import types
from PIL import Image, ImageOps
from rapidocr_onnxruntime import RapidOCR
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.parser import parse_receipt_to_dict

_MAX_IMAGE_DIM = 1600
_THUMB_SIZE = (300, 300)

_EXTRACTION_PROMPT = """
You are a receipt and invoice data extractor. Analyze this image carefully.

STEP 1 — VALIDATE: Is this image a valid receipt, bill, or invoice?
A valid receipt has: items/services with prices AND evidence of a transaction (a total, payment info, or date).
NOT valid: photos of people/food/objects, government ID cards, menus or price lists (no transaction), blank/blurry images, documents without financial data, notes without prices.

If NOT a valid receipt, respond ONLY with:
{"is_receipt": false, "rejection_reason": "brief explanation"}

STEP 2 — EXTRACT: If it IS a valid receipt, extract and respond with:
{
  "is_receipt": true,
  "rejection_reason": null,
  "confidence": "high or medium or low",
  "vendor_name": "store/shop name",
  "date": "transaction date as printed, or null",
  "gst_number": "15-character GSTIN / tax registration number if printed, or null",
  "invoice_number": "receipt / bill / GST invoice serial number if printed, or null",
  "total": 0.00,
  "category": "one of: Groceries, Food & Dining, Transport, Shopping, Bills & Utilities, Health, Entertainment, Education, Other",
  "items": [
    {"name": "item name", "quantity": 1, "unit_price": 25.00, "total_price": 25.00}
  ],
  "raw_text": "all text visible on the receipt, line by line"
}

Rules:
- "confidence": "high" if printed and clear, "medium" if partially readable, "low" if handwritten on blank paper or damaged.
- "gst_number": extract the vendor's GSTIN (or tax ID) if present, otherwise null.
- "invoice_number": extract the invoice/bill/receipt number if present, otherwise null.
- For items: exclude tax lines, subtotals, and the grand total row.
- If quantity is not shown, default to 1. total_price = quantity × unit_price.
- "total" must be the final payable amount (not subtotal, not cash tendered).
- Reply with ONLY valid JSON — no markdown fences, no explanation.
"""


def _is_retryable(exc: BaseException) -> bool:
    """
    Args:
        exc: The exception raised during a Gemini API call.
    Return:
        True if the error is a transient 503 or 429 error, otherwise False.
    Determines whether a failed Gemini API request should be retried.
    """
    msg = str(exc)
    return "503" in msg or "429" in msg or "UNAVAILABLE" in msg or "RESOURCE_EXHAUSTED" in msg


def _safe_float(value) -> float:
    """
    Args:
        value: Numeric string, number, or None from OCR output.
    Return:
        Cleaned float value, defaulting to 0.0 on failure.
    Strips currency symbols and commas from a value and converts it to a float.
    """
    if value is None:
        return 0.0
    s = str(value).strip()
    if not s:
        return 0.0
    s = re.sub(r"[₹$€£¥]|Rs\.?|INR|USD", "", s, flags=re.IGNORECASE).strip()
    s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def preprocess_image(image_bytes: bytes) -> Image.Image:
    """
    Args:
        image_bytes: Raw uploaded image bytes.
    Return:
        Processed PIL Image in RGB mode.
    Fixes EXIF orientation, converts to RGB, and downscales oversized images.
    """
    image = Image.open(io.BytesIO(image_bytes))
    image = ImageOps.exif_transpose(image)
    image = image.convert("RGB")

    w, h = image.size
    if max(w, h) > _MAX_IMAGE_DIM:
        scale = _MAX_IMAGE_DIM / max(w, h)
        image = image.resize(
            (int(w * scale), int(h * scale)),
            Image.LANCZOS,
        )

    return image


def save_upload(image_bytes: bytes, upload_dir: str) -> tuple[str, str, str]:
    """
    Args:
        image_bytes: Raw uploaded image bytes.
        upload_dir: Directory path where image files are stored.
    Return:
        Tuple of (upload_id, image_path, thumb_path) relative to upload_dir.
    Preprocesses and saves the full-size JPEG image and its thumbnail to disk.
    """
    upload_id = str(uuid.uuid4())
    base_dir = Path(upload_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    image = preprocess_image(image_bytes)

    image_path = f"{upload_id}.jpg"
    image.save(base_dir / image_path, format="JPEG", quality=85)

    thumb = image.copy()
    thumb.thumbnail(_THUMB_SIZE, Image.LANCZOS)
    thumb_path = f"{upload_id}_thumb.jpg"
    thumb.save(base_dir / thumb_path, format="JPEG", quality=75)

    return upload_id, image_path, thumb_path


class OcrEngine:
    def __init__(self, api_key: str, model: str = "gemini-3.6-flash"):
        """
        Args:
            api_key: Google Gemini API key.
            model: Gemini model identifier string.
        Return:
            None.
        Initializes the Gemini client and model configuration.
        """
        self.client = genai.Client(api_key=api_key)
        self.model = model

    @retry(
        retry=retry_if_exception(_is_retryable),
        wait=wait_exponential(multiplier=1, min=2, max=16),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def extract_receipt(self, image_bytes: bytes) -> dict:
        """
        Args:
            image_bytes: Raw receipt image bytes.
        Return:
            Dictionary containing extracted receipt data or rejection reason.
        Sends the preprocessed receipt image to Gemini and normalizes the extracted JSON.
        """
        image = preprocess_image(image_bytes)

        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=85)
        jpeg_bytes = buf.getvalue()

        image_part = types.Part.from_bytes(data=jpeg_bytes, mime_type="image/jpeg")

        response = self.client.models.generate_content(
            model=self.model,
            contents=[_EXTRACTION_PROMPT, image_part],
        )

        raw = response.text.strip()

        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1].lstrip("json").strip() if len(parts) > 1 else raw

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Gemini returned non-JSON response: {raw[:300]}"
            ) from exc

        if data.get("is_receipt", True):
            data["total"] = _safe_float(data.get("total"))
            for item in data.get("items", []):
                item["quantity"] = _safe_float(item.get("quantity")) or 1.0
                item["unit_price"] = _safe_float(item.get("unit_price"))
                item["total_price"] = _safe_float(item.get("total_price"))
                expected = round(item["quantity"] * item["unit_price"], 2)
                if item["total_price"] == 0 and expected > 0:
                    item["total_price"] = expected

            item_sum = round(sum(i["total_price"] for i in data.get("items", [])), 2)
            stated_total = data["total"]

            if stated_total == 0 and item_sum > 0:
                data["total"] = item_sum
                data["total_auto_corrected"] = True
            elif item_sum > 0 and stated_total > 0:
                diff_pct = abs(item_sum - stated_total) / stated_total
                if diff_pct > 0.30:
                    data["total"] = item_sum
                    data["total_auto_corrected"] = True
                else:
                    data["total_auto_corrected"] = False
            else:
                data["total_auto_corrected"] = False

        return data

    def extract_text(self, image_bytes: bytes, language_hints=None) -> str:
        """
        Args:
            image_bytes: Raw receipt image bytes.
            language_hints: Optional unused parameter for backward compatibility.
        Return:
            Raw OCR text string from the receipt.
        Extracts and returns only the raw text portion of a receipt image.
        """
        return self.extract_receipt(image_bytes).get("raw_text", "")


class LocalOcrEngine:
    def __init__(self):
        """
        Args:
            None.
        Return:
            None.
        Initializes the offline RapidOCR ONNX engine.
        """
        self.ocr = RapidOCR()

    def extract_receipt(self, image_bytes: bytes) -> dict:
        """
        Args:
            image_bytes: Raw receipt image bytes.
        Return:
            Dictionary of extracted receipt fields parsed offline.
        Runs offline OCR, groups text by horizontal line, and parses fields via regex.
        """
        image = preprocess_image(image_bytes)
        img_array = np.array(image)

        result, _ = self.ocr(img_array)
        if not result:
            return {
                "is_receipt": False,
                "rejection_reason": "No text detected in image (Local Privacy Mode).",
            }

        rows = []
        sorted_boxes = sorted(result, key=lambda item: item[0][0][1])

        for box, text, _score in sorted_boxes:
            y_top = box[0][1]
            x_left = box[0][0]
            placed = False
            for row in rows:
                if abs(row["y"] - y_top) <= 15:
                    row["items"].append((x_left, text))
                    placed = True
                    break
            if not placed:
                rows.append({"y": y_top, "items": [(x_left, text)]})

        lines = []
        for row in rows:
            row_items = sorted(row["items"], key=lambda x: x[0])
            lines.append("   ".join(text for _, text in row_items))

        raw_text = "\n".join(lines)
        return parse_receipt_to_dict(raw_text)