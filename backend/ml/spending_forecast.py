"""
Spending forecasting using Prophet and other time series models
"""

import pandas as pd
from prophet import Prophet
from typing import List, Dict
from datetime import datetime, timedelta


class SpendingForecaster:
    """Forecast future spending patterns using time series analysis"""
    
    def __init__(self):
        self.model = None
    
    def train(self, transactions: List[Dict]):
        """
        Train forecasting model on historical transaction data
        
        Args:
            transactions: List of transaction dictionaries with 'date' and 'amount'
        """
        # Convert to DataFrame
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])
        df = df.groupby('date')['amount'].sum().reset_index()
        df.columns = ['ds', 'y']
        
        # Check if we have enough data
        if len(df) < 14:
            raise ValueError("Not enough data to train forecast model — need at least 14 days of transactions")
        
        # Train Prophet model
        self.model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            seasonality_mode='multiplicative'
        )
        self.model.fit(df)
    
    def forecast(self, periods: int = 30) -> List[Dict]:
        """
        Forecast spending for the next N days
        
        Args:
            periods: Number of days to forecast
            
        Returns:
            List of dicts with forecasted spending data
        """
        if self.model is None:
            raise ValueError("Model must be trained before forecasting")
        
        future = self.model.make_future_dataframe(periods=periods)
        forecast = self.model.predict(future)
        
        # Get only the future periods (exclude historical data)
        forecast_data = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods)
        
        # Convert to list of dicts with proper formatting
        result = []
        for _, row in forecast_data.iterrows():
            result.append({
                "date": row['ds'].isoformat(),
                "predicted_amount": round(float(row['yhat']), 2),
                "lower": round(float(row['yhat_lower']), 2),
                "upper": round(float(row['yhat_upper']), 2)
            })
        
        return result
    
    def get_weekly_forecast(self, weeks: int) -> List[float]:
        """
        Get weekly forecast totals by aggregating daily predictions
        
        Args:
            weeks: Number of weeks to forecast
            
        Returns:
            List of weekly spending totals
        """
        daily_forecast = self.forecast(periods=weeks * 7)
        weekly_totals = []
        
        for week in range(weeks):
            week_start = week * 7
            week_end = week_start + 7
            week_total = sum(day['predicted_amount'] for day in daily_forecast[week_start:week_end])
            weekly_totals.append(round(week_total, 2))
        
        return weekly_totals
    
    def detect_seasonal_patterns(self, transactions: List[Dict]) -> Dict:
        """
        Detect seasonal spending patterns (holidays, month-end, etc.)
        """
        # TODO: Implement seasonal pattern detection
        return {
            "holiday_spending": {},
            "monthly_patterns": {},
            "weekly_patterns": {}
        }

