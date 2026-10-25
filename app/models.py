"""SQLAlchemy ORM models for receipts and receipt line items."""

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_name = Column(String(255), default="Unknown Vendor")
    date = Column(String(50), nullable=True)
    total = Column(Float, default=0.0)
    category = Column(String(100), default="Other")
    confidence = Column(String(20), default="high")
    total_auto_corrected = Column(Boolean, default=False)
    raw_ocr_text = Column(Text, nullable=True)
    image_path = Column(String(500), nullable=True)
    thumbnail_path = Column(String(500), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    items = relationship(
        "ReceiptItem", back_populates="receipt", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """
        Args:
            None.
        Return:
            Formatted string representation of the Receipt instance.
        Returns a debug representation showing vendor name and total.
        """
        return f"<Receipt {self.vendor_name} {self.total}>"


class ReceiptItem(Base):
    __tablename__ = "receipt_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_id = Column(
        UUID(as_uuid=True),
        ForeignKey("receipts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    quantity = Column(Float, default=1.0)
    unit_price = Column(Float, default=0.0)
    total_price = Column(Float, default=0.0)

    receipt = relationship("Receipt", back_populates="items")

    def __repr__(self) -> str:
        """
        Args:
            None.
        Return:
            Formatted string representation of the ReceiptItem instance.
        Returns a debug representation showing item name and total price.
        """
        return f"<ReceiptItem {self.name} {self.total_price}>"