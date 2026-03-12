"""
Dashboard data API endpoints - real aggregates from DB
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.connection import get_db
from database import models
from ml.anomaly_detection import SpendingAnomalyDetector

router = APIRouter()


def _income_expense_from_transactions(
    db: Session,
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """Sum income (negative amounts) and expenses (positive amounts) from transactions."""
    q = (
        db.query(models.Transaction.amount, func.count(models.Transaction.id))
        .join(models.Account)
        .filter(models.Account.user_id == user_id)
    )
    if start_date is not None:
        q = q.filter(models.Transaction.date >= start_date)
    if end_date is not None:
        q = q.filter(models.Transaction.date <= end_date)
    rows = q.all()
    total_income = 0.0
    total_expenses = 0.0
    for (amount, _) in rows:
        if amount is None:
            continue
        if amount < 0:
            total_income += abs(amount)
        else:
            total_expenses += amount
    return total_income, total_expenses


@router.get("/summary")
async def get_financial_summary(
    user_id: int = Query(1),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Get overall financial summary from accounts and transactions.
    """
    total_income, total_expenses = _income_expense_from_transactions(
        db, user_id, start_date, end_date
    )
    total_savings = total_income - total_expenses
    savings_ratio = (total_savings / total_income) if total_income else 0.0

    # Account balances for user
    balances = (
        db.query(func.coalesce(func.sum(models.Account.balance), 0))
        .filter(models.Account.user_id == user_id, models.Account.is_active == True)
        .scalar()
    )
    account_balances = [float(balances)] if balances is not None else [0.0]

    return {
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "total_savings": round(total_savings, 2),
        "savings_ratio": round(savings_ratio, 4),
        "account_balances": account_balances,
    }


@router.get("/spending/category")
async def get_spending_by_category(
    user_id: int = Query(1),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Get spending breakdown by category (expenses only, positive amounts).
    """
    q = (
        db.query(
            models.Transaction.category,
            func.sum(models.Transaction.amount).label("amount"),
            func.count(models.Transaction.id).label("count"),
        )
        .join(models.Account)
        .filter(models.Account.user_id == user_id)
        .filter(models.Transaction.amount > 0)
    )
    if start_date is not None:
        q = q.filter(models.Transaction.date >= start_date)
    if end_date is not None:
        q = q.filter(models.Transaction.date <= end_date)
    rows = q.group_by(models.Transaction.category).all()

    total = sum(r.amount or 0 for r in rows)
    categories = [
        {
            "category": r.category.value if r.category else "other",
            "amount": round(float(r.amount or 0), 2),
            "percentage": round(100 * (r.amount or 0) / total, 2) if total else 0,
            "transaction_count": r.count or 0,
        }
        for r in rows
    ]
    return {"categories": categories}


@router.get("/trends/monthly")
async def get_monthly_trends(
    user_id: int = Query(1),
    months: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db),
):
    """
    Get monthly income/expense/savings trends.
    """
    end = datetime.utcnow()
    start = end - timedelta(days=months * 31)
    q = (
        db.query(
            func.date_trunc("month", models.Transaction.date).label("month"),
            models.Transaction.amount,
        )
        .join(models.Account)
        .filter(models.Account.user_id == user_id)
        .filter(models.Transaction.date >= start)
        .filter(models.Transaction.date <= end)
    )
    rows = q.all()
    by_month = defaultdict(lambda: {"income": 0.0, "expenses": 0.0})
    for r in rows:
        if r.month is None or r.amount is None:
            continue
        key = r.month.strftime("%Y-%m") if hasattr(r.month, "strftime") else str(r.month)
        if r.amount < 0:
            by_month[key]["income"] += abs(r.amount)
        else:
            by_month[key]["expenses"] += r.amount

    trends = []
    for month in sorted(by_month.keys(), reverse=True)[:months]:
        inc = by_month[month]["income"]
        exp = by_month[month]["expenses"]
        savings = inc - exp
        trends.append({
            "month": month,
            "income": round(inc, 2),
            "expenses": round(exp, 2),
            "savings": round(savings, 2),
            "savings_ratio": round(savings / inc, 4) if inc else 0,
        })
    return {"trends": trends}


@router.get("/anomalies")
async def get_spending_anomalies(
    user_id: int = Query(1),
    db: Session = Depends(get_db),
):
    """
    Detect and return unusual spending patterns using ML.
    """
    q = (
        db.query(
            models.Transaction.id,
            models.Transaction.amount,
            models.Transaction.date,
            models.Transaction.merchant_name,
            models.Transaction.category,
        )
        .join(models.Account)
        .filter(models.Account.user_id == user_id)
        .filter(models.Transaction.amount > 0)
        .order_by(models.Transaction.date.desc())
        .limit(500)
    )
    rows = q.all()
    if not rows:
        return {"anomalies": []}
    transactions = [
        {"id": r.id, "amount": r.amount, "date": r.date, "merchant_name": r.merchant_name, "category": r.category.value if r.category else "other"}
        for r in rows
    ]
    detector = SpendingAnomalyDetector(contamination=0.05)
    anomalies = detector.detect_anomalies(transactions)
    return {"anomalies": anomalies}


@router.get("/forecast")
async def get_spending_forecast(
    user_id: int = Query(1),
    weeks: int = Query(8, ge=1, le=52),
    db: Session = Depends(get_db),
):
    """
    Get spending forecast for the next N weeks
    """
    # Query last 90 days of expense transactions for the user
    ninety_days_ago = datetime.now() - timedelta(days=90)
    transactions = db.query(models.Transaction).filter(
        models.Transaction.account_id.in_(
            db.query(models.Transaction.account_id).filter(
                models.Transaction.date >= ninety_days_ago,
                models.Transaction.amount > 0  # Expenses only
            )
        ),
        models.Transaction.date >= ninety_days_ago,
        models.Transaction.amount > 0
    ).all()
    
    # If fewer than 14 transactions, return insufficient data message
    if len(transactions) < 14:
        return {"forecast": [], "message": "Not enough data for forecast"}
    
    # Train SpendingForecaster and get weekly forecast
    from ml.spending_forecast import SpendingForecaster
    forecaster = SpendingForecaster()
    transaction_data = [
        {"date": t.date.isoformat(), "amount": t.amount}
        for t in transactions
    ]
    
    try:
        forecaster.train(transaction_data)
        weekly_forecast = forecaster.get_weekly_forecast(weeks)
        
        forecast_data = [
            {"week": i + 1, "predicted_spending": amount}
            for i, amount in enumerate(weekly_forecast)
        ]
        
        return {"forecast": forecast_data, "message": "ok"}
        
    except ValueError as e:
        return {"forecast": [], "message": f"Forecast failed: {str(e)}"}
