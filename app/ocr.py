import base64
import io
import json

from google import genai
from google.genai import types
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception


_EXTRACTION_PROMPT = """
You are a receipt data extractor. Look at this receipt image carefully and extract:

1. vendor_name  — The shop / store / restaurant name (string)
2. date         — The transaction date exactly as printed (string, or null if absent)
3. total        — The final payable amount as a number (float, 0 if not found)
4. items        — Line items: a list of {"name": string, "price": string} objects.
                  Exclude tax lines, subtotals, and the grand total itself.
5. raw_text     — The complete text you can read on the receipt, line by line.

Reply with ONLY a single valid JSON object — no markdown, no explanation.

Example output:
{
  "vendor_name": "Sanjhukchaiwala",
  "date": "12/04/2024",
  "total": 65.00,
  "items": [{"name": "Milk", "price": "25.00"}, {"name": "Bread", "price": "40.00"}],
  "raw_text": "Sanjhukchaiwala\\nDate: 12/04/2024\\nMilk 25.00\\nBread 40.00\\nTotal 65.00"
}
"""


def _is_retryable(exc: BaseException) -> bool:
    """Retry on 503 (overloaded) and 429 (rate limited) Gemini API errors."""
    msg = str(exc)
    return "503" in msg or "429" in msg or "UNAVAILABLE" in msg or "RESOURCE_EXHAUSTED" in msg


class OcrEngine:
    

    def __init__(self, api_key: str, model: str = "gemini-3.6-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = model


    # Primary method:returns a dict ready for ParsedReceiptOut
    @retry(
        retry=retry_if_exception(_is_retryable),
        wait=wait_exponential(multiplier=1, min=2, max=16),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def extract_receipt(self, image_bytes: bytes) -> dict:
        
        # Normalise to JPEG so we always send a known mime type
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=90)
        jpeg_bytes = buf.getvalue()

        image_part = types.Part.from_bytes(data=jpeg_bytes, mime_type="image/jpeg")

        response = self.client.models.generate_content(
            model=self.model,
            contents=[_EXTRACTION_PROMPT, image_part],
        )

        raw = response.text.strip()

        # Strip markdown code fences if Gemini wraps the JSON anyway
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1].lstrip("json").strip() if len(parts) > 1 else raw

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Gemini returned non-JSON response: {raw[:300]}"
            ) from exc

        return data

    
    # Legacy compat — kept so nothing else breaks if called
    def extract_text(self, image_bytes: bytes, language_hints=None) -> str:
        #This Thin wrapper that returns only the raw_text field.
        return self.extract_receipt(image_bytes).get("raw_text", "")
