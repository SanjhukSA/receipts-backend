"""Receipt endpoints: upload, process (OCR), save, list, detail, update, delete."""

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app import schemas
from app.config import settings
from app.dependencies import get_db
from app.models import Receipt, ReceiptItem
from app.ocr import LocalOcrEngine, OcrEngine, save_upload

router = APIRouter(prefix="/receipts", tags=["receipts"])

_ocr_engine = None
_local_ocr_engine = None


def get_ocr_engine() -> OcrEngine:
    """
    Args:
        None.
    Return:
        Singleton OcrEngine instance.
    Lazily initializes and returns the Gemini OCR engine.
    """
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = OcrEngine(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        )
    return _ocr_engine


def get_local_ocr_engine() -> LocalOcrEngine:
    """
    Args:
        None.
    Return:
        Singleton LocalOcrEngine instance.
    Lazily initializes and returns the offline RapidOCR engine.
    """
    global _local_ocr_engine
    if _local_ocr_engine is None:
        _local_ocr_engine = LocalOcrEngine()
    return _local_ocr_engine


@router.post("/upload", response_model=schemas.UploadResponse)
async def upload_receipt(file: UploadFile = File(...)):
    """
    Args:
        file: Uploaded receipt image file.
    Return:
        UploadResponse containing upload_id, filename, and size_kb.
    Validates and saves an uploaded receipt image and thumbnail to disk without running OCR.
    """
    image_bytes = await file.read()

    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    if len(image_bytes) > settings.max_upload_bytes:
        mb = len(image_bytes) // (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({mb} MB). Maximum is 10 MB.",
        )

    upload_id, image_path, thumb_path = await run_in_threadpool(
        save_upload, image_bytes, settings.upload_dir
    )

    return schemas.UploadResponse(
        upload_id=upload_id,
        filename=file.filename or "receipt.jpg",
        size_kb=round(len(image_bytes) / 1024, 1),
    )


@router.post("/{upload_id}/process", response_model=schemas.ProcessResponse)
async def process_receipt(
    upload_id: str,
    privacy_mode: bool = Query(
        False,
        description="If True, runs 100% offline OCR + regex parsing without calling Gemini API.",
    ),
):
    """
    Args:
        upload_id: Unique identifier of the previously uploaded image.
        privacy_mode: Boolean flag to toggle offline OCR versus Gemini OCR.
    Return:
        ProcessResponse with extracted vendor, date, GST/invoice numbers, total, and line items.
    Runs OCR on a saved image and returns structured receipt data for user review.
    """
    image_path = Path(settings.upload_dir) / f"{upload_id}.jpg"
    if not image_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Upload not found. It may have expired — please re-upload.",
        )

    image_bytes = image_path.read_bytes()

    try:
        engine = get_local_ocr_engine() if privacy_mode else get_ocr_engine()
        extracted = await run_in_threadpool(engine.extract_receipt, image_bytes)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OCR failed: {e}")

    if not extracted.get("is_receipt", True):
        return schemas.ProcessResponse(
            upload_id=upload_id,
            is_receipt=False,
            rejection_reason=extracted.get("rejection_reason", "Not a valid receipt"),
        )

    items = [
        schemas.LineItemBase(
            name=item.get("name") or "",
            quantity=item.get("quantity", 1.0),
            unit_price=item.get("unit_price", 0.0),
            total_price=item.get("total_price", 0.0),
        )
        for item in extracted.get("items") or []
    ]

    return schemas.ProcessResponse(
        upload_id=upload_id,
        is_receipt=True,
        rejection_reason=None,
        vendor_name=extracted.get("vendor_name") or "Unknown Vendor",
        date=extracted.get("date"),
        gst_number=extracted.get("gst_number"),
        invoice_number=extracted.get("invoice_number"),
        total=extracted.get("total", 0.0),
        category=extracted.get("category") or "Other",
        confidence=extracted.get("confidence") or "high",
        total_auto_corrected=extracted.get("total_auto_corrected", False),
        items=items,
        raw_ocr_text=extracted.get("raw_text") or "",
    )


@router.post("", response_model=schemas.ReceiptOut, status_code=201)
def save_receipt(
    body: schemas.ReceiptCreate,
    db: Session = Depends(get_db),
):
    """
    Args:
        body: Confirmed receipt payload from the client.
        db: SQLAlchemy database session.
    Return:
        ReceiptOut representing the persisted receipt and line items.
    Saves a confirmed receipt and its line items to the database.
    """
    image_path = f"{body.upload_id}.jpg"
    thumb_path = f"{body.upload_id}_thumb.jpg"
    full_image = Path(settings.upload_dir) / image_path
    if not full_image.exists():
        raise HTTPException(
            status_code=404,
            detail="Upload image not found. Please re-upload the receipt.",
        )

    receipt = Receipt(
        vendor_name=body.vendor_name,
        date=body.date,
        total=body.total,
        category=body.category,
        confidence=body.confidence,
        total_auto_corrected=body.total_auto_corrected,
        raw_ocr_text=body.raw_ocr_text,
        image_path=image_path,
        thumbnail_path=thumb_path,
    )
    db.add(receipt)
    db.flush()

    for item in body.items:
        db.add(ReceiptItem(
            receipt_id=receipt.id,
            name=item.name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.total_price,
        ))

    db.commit()
    db.refresh(receipt)

    return _receipt_to_out(receipt)


@router.get("", response_model=schemas.PaginatedReceipts)
def list_receipts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: str | None = Query(None),
    sort: str = Query("-created_at"),
    db: Session = Depends(get_db),
):
    """
    Args:
        page: Page number (1-indexed).
        per_page: Number of receipts per page.
        category: Optional category filter string.
        sort: Field name to sort by, prefixed with '-' for descending order.
        db: SQLAlchemy database session.
    Return:
        PaginatedReceipts containing the current page of receipts and pagination metadata.
    Lists receipts with optional category filtering, sorting, and pagination.
    """
    query = db.query(Receipt)

    if category:
        query = query.filter(Receipt.category == category)

    if sort.startswith("-"):
        col = getattr(Receipt, sort.lstrip("-"), Receipt.created_at)
        query = query.order_by(col.desc())
    else:
        col = getattr(Receipt, sort, Receipt.created_at)
        query = query.order_by(col.asc())

    total = query.count()
    pages = max(1, -(-total // per_page))
    receipts = query.offset((page - 1) * per_page).limit(per_page).all()

    return schemas.PaginatedReceipts(
        items=[_receipt_to_out(r) for r in receipts],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get("/{receipt_id}", response_model=schemas.ReceiptOut)
def get_receipt(
    receipt_id: str,
    db: Session = Depends(get_db),
):
    """
    Args:
        receipt_id: UUID string of the target receipt.
        db: SQLAlchemy database session.
    Return:
        ReceiptOut for the matching receipt.
    Fetches a single receipt and its line items by ID.
    """
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return _receipt_to_out(receipt)


@router.patch("/{receipt_id}", response_model=schemas.ReceiptOut)
def update_receipt(
    receipt_id: str,
    body: schemas.ReceiptUpdate,
    db: Session = Depends(get_db),
):
    """
    Args:
        receipt_id: UUID string of the target receipt.
        body: Partial update fields and optional replacement line items.
        db: SQLAlchemy database session.
    Return:
        Updated ReceiptOut object.
    Partially updates a receipt's scalar fields and replaces line items if provided.
    """
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    update_data = body.model_dump(exclude_unset=True)
    items_data = update_data.pop("items", None)

    for field, value in update_data.items():
        setattr(receipt, field, value)

    if items_data is not None:
        db.query(ReceiptItem).filter(ReceiptItem.receipt_id == receipt.id).delete()
        for item in items_data:
            db.add(ReceiptItem(
                receipt_id=receipt.id,
                name=item["name"],
                quantity=item.get("quantity", 1.0),
                unit_price=item.get("unit_price", 0.0),
                total_price=item.get("total_price", 0.0),
            ))

    db.commit()
    db.refresh(receipt)
    return _receipt_to_out(receipt)


@router.delete("/{receipt_id}", status_code=204)
def delete_receipt(
    receipt_id: str,
    db: Session = Depends(get_db),
):
    """
    Args:
        receipt_id: UUID string of the receipt to delete.
        db: SQLAlchemy database session.
    Return:
        None (204 No Content).
    Deletes a receipt record from the database and removes its image files from disk.
    """
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    if receipt.image_path:
        img = Path(settings.upload_dir) / receipt.image_path
        img.unlink(missing_ok=True)
    if receipt.thumbnail_path:
        thumb = Path(settings.upload_dir) / receipt.thumbnail_path
        thumb.unlink(missing_ok=True)

    db.delete(receipt)
    db.commit()


@router.get("/{receipt_id}/image")
def get_receipt_image(
    receipt_id: str,
    db: Session = Depends(get_db),
):
    """
    Args:
        receipt_id: UUID string of the target receipt.
        db: SQLAlchemy database session.
    Return:
        FileResponse streaming the full-resolution JPEG image.
    Serves the full-resolution receipt image file from disk.
    """
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt or not receipt.image_path:
        raise HTTPException(status_code=404, detail="Image not found")

    file_path = Path(settings.upload_dir) / receipt.image_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image file missing from disk")

    return FileResponse(file_path, media_type="image/jpeg")


@router.get("/{receipt_id}/thumbnail")
def get_receipt_thumbnail(
    receipt_id: str,
    db: Session = Depends(get_db),
):
    """
    Args:
        receipt_id: UUID string of the target receipt.
        db: SQLAlchemy database session.
    Return:
        FileResponse streaming the thumbnail JPEG image.
    Serves the compressed thumbnail image for a receipt from disk.
    """
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt or not receipt.thumbnail_path:
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    file_path = Path(settings.upload_dir) / receipt.thumbnail_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail file missing from disk")

    return FileResponse(file_path, media_type="image/jpeg")


def _receipt_to_out(receipt: Receipt) -> schemas.ReceiptOut:
    """
    Args:
        receipt: SQLAlchemy Receipt ORM instance.
    Return:
        ReceiptOut Pydantic schema populated with image URLs.
    Converts a Receipt ORM model into a serialized ReceiptOut response object.
    """
    return schemas.ReceiptOut(
        id=receipt.id,
        vendor_name=receipt.vendor_name,
        date=receipt.date,
        total=receipt.total,
        category=receipt.category,
        confidence=receipt.confidence,
        total_auto_corrected=receipt.total_auto_corrected,
        items=[
            schemas.LineItemOut(
                id=item.id,
                name=item.name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
            )
            for item in receipt.items
        ],
        raw_ocr_text=receipt.raw_ocr_text or "",
        image_url=f"/receipts/{receipt.id}/image" if receipt.image_path else None,
        thumbnail_url=f"/receipts/{receipt.id}/thumbnail" if receipt.thumbnail_path else None,
        created_at=receipt.created_at,
    )