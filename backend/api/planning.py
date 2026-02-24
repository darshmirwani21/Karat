"""
AI-powered financial planning API endpoints - real goals and recommendations from DB
"""

from datetime import datetime
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
    Generate AI-powered savings recommendations for a goal (stub: creates one placeholder).
    """
    goal = db.query(models.SavingsGoal).filter(models.SavingsGoal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    # TODO: Call optimization + ML to generate week-by-week plan
    from datetime import timedelta
    rec = models.SavingsRecommendation(
        goal_id=goal_id,
        week_start=datetime.utcnow(),
        recommended_amount=goal.target_amount / 10,
        reasoning="Placeholder: distribute goal over 10 weeks.",
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {
        "recommendations": [
            {
                "id": rec.id,
                "week_start": rec.week_start.isoformat() if rec.week_start else None,
                "recommended_amount": rec.recommended_amount,
                "reasoning": rec.reasoning or "",
                "user_approved": rec.user_approved,
            }
        ]
    }


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
