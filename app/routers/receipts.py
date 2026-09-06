from fastapi import APIRouter, UploadFile, File, HTTPException

from app import schemas
from app.config import settings
from app.ocr import OcrEngine

router = APIRouter(prefix="/receipts", tags=["receipts"])

_ocr_engine = None


def get_ocr_engine() -> OcrEngine:
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = OcrEngine(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        )
    return _ocr_engine


@router.post("/process", response_model=schemas.ParsedReceiptOut)
async def process_receipt(
    file: UploadFile = File(...),
):
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    try:
        # Gemini extracts everything in one shot — no separate regex parser needed
        extracted = get_ocr_engine().extract_receipt(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OCR failed: {e}")

    items = [
        schemas.LineItem(name=item.get("name") or "", price=str(item.get("price") or ""))
        for item in extracted.get("items") or []
    ]

    return schemas.ParsedReceiptOut(
        vendor_name_guess=extracted.get("vendor_name") or "Unknown Vendor",
        date=extracted.get("date") or None,
        total=float(extracted.get("total") or 0.0),
        items=items,
        raw_ocr_text=extracted.get("raw_text") or "",
    )
