"""
Anomaly detection for unusual spending patterns
"""

import pandas as pd
from sklearn.ensemble import IsolationForest
from typing import List, Dict
import numpy as np


class SpendingAnomalyDetector:
    """Detect unusual spending patterns in transaction data"""
    
    def __init__(self, contamination=0.1):
        """
        Args:
            contamination: Expected proportion of anomalies (0.0 to 0.5)
        """
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.is_trained = False
    
    def detect_anomalies(self, transactions: List[Dict]) -> List[Dict]:
        """
        Detect anomalous transactions
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            List of transactions flagged as anomalies with anomaly scores
        """
        if not transactions:
            return []
        
        df = pd.DataFrame(transactions)
        
        # Feature engineering
        features = self._extract_features(df)
        
        # Train and predict
        self.model.fit(features)
        predictions = self.model.predict(features)
        scores = self.model.score_samples(features)
        
        # Mark anomalies
        df['is_anomaly'] = predictions == -1
        df['anomaly_score'] = scores
        
        # Return anomalous transactions
        anomalies = df[df['is_anomaly']].to_dict('records')
        
        return anomalies
    
    def _extract_features(self, df: pd.DataFrame) -> np.ndarray:
        """
        Extract features for anomaly detection.
        Handles missing 'date' column for amount-only analysis.
        """
        if 'amount' not in df.columns:
            raise ValueError("transactions must include 'amount'")
        features = [np.asarray(df['amount'], dtype=float).reshape(-1, 1)]
        if 'date' in df.columns:
            dates = pd.to_datetime(df['date'])
            features.append(dates.dt.dayofweek.values.reshape(-1, 1).astype(float))
            features.append(dates.dt.day.values.reshape(-1, 1).astype(float))
        return np.hstack(features)

