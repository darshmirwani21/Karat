"""
Savings optimization API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from database.models import Transaction, TransactionCategory
from optimization.savings_optimizer import SavingsOptimizer
from ml.spending_forecast import SpendingForecaster

router = APIRouter()


class OptimizationRequest(BaseModel):
    """Request model for savings optimization"""
    goal_amount: float
    target_date: datetime
    current_savings: float = 0.0
    monthly_income: float
    essential_expenses: Optional[float] = None


class OptimizationResponse(BaseModel):
    """Response model for savings optimization"""
    weekly_plan: List[float]
    weeks: int
    optimal_savings_ratio: float
    feasible: bool
    summary: str


@router.post("/calculate")
async def calculate_optimal_savings(
    request: OptimizationRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate optimal savings ratio and weekly savings plan
    """
    try:
        # Query the DB for the last 90 days of expense transactions for user_id=1
        ninety_days_ago = datetime.now() - timedelta(days=90)
        transactions = db.query(Transaction).filter(
            Transaction.account_id.in_(
                db.query(Transaction.account_id).filter(
                    Transaction.date >= ninety_days_ago,
                    Transaction.amount > 0  # Expenses only
                )
            ),
            Transaction.date >= ninety_days_ago,
            Transaction.amount > 0
        ).all()
        
        # Calculate weeks until target
        weeks_until_target = (request.target_date - datetime.now()).days / 7
        weeks_until_target = max(1, int(weeks_until_target))
        
        # If transactions exist, train a SpendingForecaster
        if len(transactions) >= 14:
            forecaster = SpendingForecaster()
            transaction_data = [
                {"date": t.date.isoformat(), "amount": t.amount}
                for t in transactions
            ]
            forecaster.train(transaction_data)
            weekly_expenses = forecaster.get_weekly_forecast(weeks_until_target)
        else:
            # Cold start: use essential_expenses from request or default
            if request.essential_expenses:
                weekly_expenses = [request.essential_expenses] * weeks_until_target
            else:
                weekly_expenses = [(request.monthly_income * 0.6) / 4.33] * weeks_until_target
        
        # Compute weekly income
        weekly_income = request.monthly_income / 4.33
        
        # Call SavingsOptimizer
        optimizer = SavingsOptimizer()
        result = optimizer.optimize_weekly_savings(
            goal_amount=request.goal_amount,
            target_date=request.target_date,
            current_savings=request.current_savings,
            weekly_income=weekly_income,
            weekly_expenses_forecast=weekly_expenses
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Create summary string
        weekly_avg = sum(result["weekly_plan"]) / len(result["weekly_plan"]) if result["weekly_plan"] else 0
        summary = f"Save ${weekly_avg:.2f}/week for {result['weeks']} weeks to reach your goal by {request.target_date.strftime('%B %d, %Y')}"
        
        return {
            "weekly_plan": result["weekly_plan"],
            "weeks": result["weeks"],
            "optimal_savings_ratio": result["optimal_savings_ratio"],
            "feasible": result["feasible"],
            "summary": summary
        }
        
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.get("/ratio")
async def get_current_savings_ratio(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get current savings ratio for a user
    """
    # TODO: Calculate from actual transaction data
    return {"savings_ratio": 0.0, "income": 0.0, "expenses": 0.0, "savings": 0.0}

