"""Analytics endpoints: monthly summary and category breakdown."""

import calendar
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app import schemas
from app.dependencies import get_db
from app.models import Receipt

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/monthly", response_model=schemas.MonthlySummary)
def monthly_summary(
    month: int = Query(None, ge=1, le=12),
    year: int = Query(None, ge=2020, le=2100),
    db: Session = Depends(get_db),
):
    """
    Args:
        month: Target month number (1-12), defaults to current month.
        year: Target four-digit year, defaults to current year.
        db: SQLAlchemy database session.
    Return:
        MonthlySummary with total spend, receipt count, average, previous month total, and daily breakdown.
    Calculates monthly spending totals and day-by-day expenditure for charting.
    """
    today = date.today()
    month = month or today.month
    year = year or today.year

    month_filter = (
        extract("month", Receipt.created_at) == month,
        extract("year", Receipt.created_at) == year,
    )

    total_spent = db.query(
        func.coalesce(func.sum(Receipt.total), 0.0)
    ).filter(*month_filter).scalar()

    receipt_count = db.query(Receipt).filter(*month_filter).count()
    avg_per_receipt = round(total_spent / receipt_count, 2) if receipt_count > 0 else 0.0

    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year

    previous_month_total = db.query(
        func.coalesce(func.sum(Receipt.total), 0.0)
    ).filter(
        extract("month", Receipt.created_at) == prev_month,
        extract("year", Receipt.created_at) == prev_year,
    ).scalar()

    days_in_month = calendar.monthrange(year, month)[1]
    daily_rows = (
        db.query(
            func.date(Receipt.created_at).label("day"),
            func.sum(Receipt.total).label("total"),
        )
        .filter(*month_filter)
        .group_by(func.date(Receipt.created_at))
        .order_by(func.date(Receipt.created_at))
        .all()
    )

    daily_map = {str(row.day): float(row.total) for row in daily_rows}
    daily_breakdown = []
    for day_num in range(1, days_in_month + 1):
        d = date(year, month, day_num)
        if d > today:
            break
        daily_breakdown.append(
            schemas.DailySpend(
                date=str(d),
                total=daily_map.get(str(d), 0.0),
            )
        )

    return schemas.MonthlySummary(
        month=month,
        year=year,
        total_spent=round(float(total_spent), 2),
        receipt_count=receipt_count,
        avg_per_receipt=avg_per_receipt,
        previous_month_total=round(float(previous_month_total), 2),
        daily_breakdown=daily_breakdown,
    )


@router.get("/categories", response_model=list[schemas.CategoryBreakdownItem])
def category_breakdown(
    month: int = Query(None, ge=1, le=12),
    year: int = Query(None, ge=2020, le=2100),
    db: Session = Depends(get_db),
):
    """
    Args:
        month: Target month number (1-12), defaults to current month.
        year: Target four-digit year, defaults to current year.
        db: SQLAlchemy database session.
    Return:
        List of CategoryBreakdownItem objects ordered by highest spend.
    Groups monthly spending by category with totals, percentages, and receipt counts.
    """
    today = date.today()
    month = month or today.month
    year = year or today.year

    rows = (
        db.query(
            Receipt.category,
            func.sum(Receipt.total).label("total"),
            func.count(Receipt.id).label("count"),
        )
        .filter(
            extract("month", Receipt.created_at) == month,
            extract("year", Receipt.created_at) == year,
        )
        .group_by(Receipt.category)
        .order_by(func.sum(Receipt.total).desc())
        .all()
    )

    grand_total = sum(float(r.total) for r in rows) or 1.0

    return [
        schemas.CategoryBreakdownItem(
            category=row.category or "Other",
            total=round(float(row.total), 2),
            percentage=round(float(row.total) / grand_total * 100, 1),
            count=row.count,
        )
        for row in rows
    ]