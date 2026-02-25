"""
Savings optimization using mathematical optimization
"""

from pulp import LpMaximize, LpProblem, LpVariable, lpSum, value
from typing import List, Dict
from datetime import datetime, timedelta, timezone
import math


class SavingsOptimizer:
    """Optimize savings plan using constraint-based optimization"""
    
    def optimize_weekly_savings(
        self,
        goal_amount: float,
        target_date: datetime,
        current_savings: float,
        weekly_income: float,
        weekly_expenses_forecast: List[float],
        min_emergency_buffer: float = 0.0
    ) -> Dict:
        """
        Calculate optimal weekly savings amounts
        
        Args:
            goal_amount: Target savings amount
            target_date: When the goal should be reached
            current_savings: Current amount saved
            weekly_income: Expected weekly income
            weekly_expenses_forecast: Forecasted expenses for each week
            min_emergency_buffer: Minimum buffer to maintain
            
        Returns:
            Dictionary with weekly savings plan
        """
        # Calculate number of weeks using timezone-aware datetimes
        now = datetime.now(timezone.utc)
        if target_date.tzinfo is None:
            target_utc = target_date.replace(tzinfo=timezone.utc)
        else:
            target_utc = target_date.astimezone(timezone.utc)
        weeks = math.ceil((target_utc - now).days / 7)
        
        if weeks <= 0:
            return {"error": "Target date is in the past"}
        
        # Amount needed
        amount_needed = goal_amount - current_savings
        
        if amount_needed <= 0:
            return {"error": "Goal already achieved"}
        
        # Create optimization problem
        prob = LpProblem("SavingsOptimization", LpMaximize)
        
        # Decision variables: savings amount for each week
        savings_vars = [LpVariable(f"week_{i}", lowBound=0) for i in range(weeks)]
        
        # Objective: Maximize total savings (or minimize variance)
        # For now, we'll maximize total savings while ensuring goal is met
        prob += lpSum(savings_vars)
        
        # Constraints
        # 1. Total savings must meet goal
        prob += lpSum(savings_vars) >= amount_needed
        
        # 2. Weekly savings cannot exceed available income after expenses
        for i, (savings_var, expenses) in enumerate(zip(savings_vars, weekly_expenses_forecast)):
            available = weekly_income - expenses - min_emergency_buffer
            prob += savings_var <= max(0, available)
        
        # 3. Minimum weekly savings (to ensure progress)
        min_weekly = amount_needed / (weeks * 1.5)  # Allow some flexibility
        for savings_var in savings_vars:
            prob += savings_var >= min_weekly
        
        # Solve
        prob.solve()
        
        # Extract solution
        weekly_plan = [value(var) for var in savings_vars]
        total_savings = sum(weekly_plan)
        
        return {
            "weekly_plan": weekly_plan,
            "total_savings": total_savings,
            "weeks": weeks,
            "optimal_savings_ratio": total_savings / (weeks * weekly_income) if weekly_income > 0 else 0,
            "feasible": prob.status == 1
        }
    
    def recalculate_after_expense(
        self,
        original_plan: Dict,
        unexpected_expense: float,
        week_occurred: int
    ) -> Dict:
        """
        Recalculate savings plan after an unexpected expense
        
        Arguments:
            original_plan: Original weekly savings plan
            unexpected_expense: Amount of unexpected expense
            week_occurred: Which week the expense occurred
            
        Returns:
            Adjusted weekly savings plan
        """
        # TODO: Implement recalculation logic
        # This would adjust remaining weeks to compensate for the expense
        return original_plan

