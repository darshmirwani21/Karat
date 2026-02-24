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
        
        # Train Prophet model
        self.model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            seasonality_mode='multiplicative'
        )
        self.model.fit(df)
    
    def forecast(self, periods: int = 30) -> pd.DataFrame:
        """
        Forecast spending for the next N days
        
        Args:
            periods: Number of days to forecast
            
        Returns:
            DataFrame with forecasted spending
        """
        if self.model is None:
            raise ValueError("Model must be trained before forecasting")
        
        future = self.model.make_future_dataframe(periods=periods)
        forecast = self.model.predict(future)
        
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
    
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

