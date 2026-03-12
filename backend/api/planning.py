"""
AI-powered financial planning API endpoints - real goals and recommendations from DB
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from pydantic import BaseModel

from database.connection import get_db
from database import models

router = APIRouter()


class GoalRequest(BaseModel):
    """Request model for creating a savings goal"""
    name: str = "New Goal"
    target_amount: float
    target_date: datetime


@router.post("/goals")
async def create_savings_goal(
    goal: GoalRequest,
    user_id: int = Query(1),
    db: Session = Depends(get_db),
):
    """
    Create a new savings goal for the user.
    """
    name = goal.name
    target_amount = goal.target_amount
    target_date = goal.target_date
    # Ensure user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        user = models.User(
            id=user_id,
            email=f"user{user_id}@karat.demo",
            hashed_password="",
            full_name=f"User {user_id}",
        )
        db.add(user)
        db.flush()

    g = models.SavingsGoal(
        user_id=user_id,
        name=name,
        target_amount=target_amount,
        target_date=target_date,
        current_amount=0.0,
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    return {"goal_id": g.id, "status": "created"}


@router.get("/goals")
async def get_savings_goals(
    user_id: int = Query(1),
    db: Session = Depends(get_db),
):
    """
    Get all savings goals for a user.
    """
    goals = (
        db.query(models.SavingsGoal)
        .filter(models.SavingsGoal.user_id == user_id, models.SavingsGoal.is_active == True)
        .order_by(models.SavingsGoal.target_date.asc())
        .all()
    )
    return {
        "goals": [
            {
                "id": g.id,
                "name": g.name,
                "target_amount": g.target_amount,
                "current_amount": g.current_amount,
                "target_date": g.target_date.isoformat() if g.target_date else None,
            }
            for g in goals
        ]
    }


@router.post("/recommendations/generate")
async def generate_recommendations(
    goal_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """
    Generate AI-powered savings recommendations for a goal
    """
    try:
        # Look up the goal by goal_id
        goal = db.query(models.SavingsGoal).filter(models.SavingsGoal.id == goal_id).first()
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        # Look up the user's recent transactions (last 90 days) from DB
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
        
        # Calculate weeks until target
        weeks_until_target = (goal.target_date - datetime.now()).days / 7
        weeks_until_target = max(1, int(weeks_until_target))
        
        # Prepare expense forecast
        if len(transactions) >= 14:
            from ml.spending_forecast import SpendingForecaster
            forecaster = SpendingForecaster()
            transaction_data = [
                {"date": t.date.isoformat(), "amount": t.amount}
                for t in transactions
            ]
            forecaster.train(transaction_data)
            weekly_expenses = forecaster.get_weekly_forecast(weeks_until_target)
        else:
            # Default estimate: assume 60% of monthly income goes to expenses
            # We need to estimate monthly income from income transactions
            income_transactions = db.query(models.Transaction).filter(
                models.Transaction.date >= ninety_days_ago,
                models.Transaction.amount < 0  # Income transactions
            ).all()
            
            if income_transactions:
                monthly_income = abs(sum(t.amount for t in income_transactions)) * (30/90)  # Scale to monthly
            else:
                monthly_income = 4000  # Default assumption
            
            weekly_expenses = [(monthly_income * 0.6) / 4.33] * weeks_until_target
        
        # Estimate weekly income (if we have income data)
        income_transactions = db.query(models.Transaction).filter(
            models.Transaction.date >= ninety_days_ago,
            models.Transaction.amount < 0  # Income transactions
        ).all()
        
        if income_transactions:
            monthly_income = abs(sum(t.amount for t in income_transactions)) * (30/90)
        else:
            monthly_income = 4000  # Default assumption
        
        weekly_income = monthly_income / 4.33
        
        # Call SavingsOptimizer
        from optimization.savings_optimizer import SavingsOptimizer
        optimizer = SavingsOptimizer()
        result = optimizer.optimize_weekly_savings(
            goal_amount=goal.target_amount,
            target_date=goal.target_date,
            current_savings=goal.current_amount,
            weekly_income=weekly_income,
            weekly_expenses_forecast=weekly_expenses
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Delete any existing recommendations for that goal
        db.query(models.SavingsRecommendation).filter(
            models.SavingsRecommendation.goal_id == goal_id
        ).delete()
        
        # Create one SavingsRecommendation row per week in the plan
        recommendations = []
        for i, weekly_amount in enumerate(result["weekly_plan"]):
            week_start = datetime.now() + timedelta(weeks=i)
            rec = models.SavingsRecommendation(
                goal_id=goal_id,
                week_start=week_start,
                recommended_amount=weekly_amount,
                reasoning=f"Week {i+1} of {result['weeks']}: based on your spending forecast"
            )
            recommendations.append(rec)
        
        db.add_all(recommendations)
        db.commit()
        
        # Return all recommendations
        return {
            "recommendations": [
                {
                    "id": rec.id,
                    "week_start": rec.week_start.isoformat() if rec.week_start else None,
                    "recommended_amount": rec.recommended_amount,
                    "reasoning": rec.reasoning or "",
                    "user_approved": rec.user_approved,
                }
                for rec in recommendations
            ]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")


@router.post("/recommendations/{recommendation_id}/approve")
async def approve_recommendation(
    recommendation_id: int,
    approved: bool = Query(...),
    db: Session = Depends(get_db),
):
    """
    Approve or reject an AI recommendation (for learning).
    """
    rec = db.query(models.SavingsRecommendation).filter(models.SavingsRecommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    rec.user_approved = approved
    db.commit()
    return {"status": "updated", "learning": True}


@router.get("/recommendations")
async def get_recommendations(
    goal_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """
    Get recommendations for a specific goal.
    """
    recs = (
        db.query(models.SavingsRecommendation)
        .filter(models.SavingsRecommendation.goal_id == goal_id)
        .order_by(models.SavingsRecommendation.week_start.asc())
        .all()
    )
    return {
        "recommendations": [
            {
                "id": r.id,
                "week_start": r.week_start.isoformat() if r.week_start else None,
                "recommended_amount": r.recommended_amount,
                "reasoning": r.reasoning or "",
                "user_approved": r.user_approved,
            }
            for r in recs
        ]
    }
