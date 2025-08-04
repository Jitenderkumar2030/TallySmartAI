import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
from datetime import datetime, timedelta

class PredictiveAnalytics:
    def __init__(self):
        self.cash_flow_model = RandomForestRegressor(n_estimators=100)
        self.risk_model = GradientBoostingClassifier(n_estimators=100)
        self.scaler = StandardScaler()
    
    def predict_cash_flow_crisis(self, df):
        """Predict potential cash flow issues"""
        if len(df) < 30:
            return {"warning": "Insufficient data for prediction"}
        
        # Feature engineering
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        
        # Create features
        df['rolling_avg_7'] = df['Amount'].rolling(7).mean()
        df['rolling_avg_30'] = df['Amount'].rolling(30).mean()
        df['volatility'] = df['Amount'].rolling(7).std()
        df['trend'] = df['Amount'].pct_change()
        
        # Predict next 30 days cash flow
        features = ['rolling_avg_7', 'rolling_avg_30', 'volatility', 'trend']
        X = df[features].dropna()
        
        if len(X) < 10:
            return {"warning": "Insufficient clean data"}
        
        # Simple prediction (in production, use trained model)
        future_cash_flow = X['rolling_avg_30'].iloc[-1] * 30
        current_trend = X['trend'].iloc[-5:].mean()
        
        risk_level = "LOW"
        if current_trend < -0.1:
            risk_level = "HIGH"
        elif current_trend < -0.05:
            risk_level = "MEDIUM"
        
        return {
            "predicted_30_day_flow": future_cash_flow,
            "risk_level": risk_level,
            "trend": current_trend,
            "recommendations": self._get_cash_flow_recommendations(risk_level)
        }
    
    def predict_seasonal_patterns(self, df):
        """Identify and predict seasonal business patterns"""
        df['Date'] = pd.to_datetime(df['Date'])
        df['Month'] = df['Date'].dt.month
        df['Quarter'] = df['Date'].dt.quarter
        df['DayOfWeek'] = df['Date'].dt.dayofweek
        
        monthly_avg = df.groupby('Month')['Amount'].mean()
        quarterly_avg = df.groupby('Quarter')['Amount'].mean()
        
        # Find peak and low seasons
        peak_month = monthly_avg.idxmax()
        low_month = monthly_avg.idxmin()
        
        return {
            "peak_season": f"Month {peak_month}",
            "low_season": f"Month {low_month}",
            "seasonal_variance": monthly_avg.std() / monthly_avg.mean(),
            "monthly_patterns": monthly_avg.to_dict(),
            "recommendations": self._get_seasonal_recommendations(peak_month, low_month)
        }
    
    def _get_cash_flow_recommendations(self, risk_level):
        recommendations = {
            "HIGH": [
                "🚨 Immediate action required - Review all pending receivables",
                "💰 Consider emergency credit line activation",
                "📉 Reduce non-essential expenses immediately",
                "📞 Contact customers for faster payment collection"
            ],
            "MEDIUM": [
                "⚠️ Monitor cash flow closely",
                "📋 Review payment terms with customers",
                "💳 Prepare contingency funding options",
                "📊 Optimize inventory levels"
            ],
            "LOW": [
                "✅ Cash flow appears stable",
                "💡 Consider investment opportunities",
                "📈 Plan for business expansion",
                "🏦 Build emergency reserves"
            ]
        }
        return recommendations.get(risk_level, [])
    
    def _get_seasonal_recommendations(self, peak_month, low_month):
        return [
            f"📈 Prepare for peak season in month {peak_month}",
            f"📉 Plan cost optimization for low season in month {low_month}",
            "📦 Adjust inventory based on seasonal patterns",
            "👥 Plan staffing according to seasonal demand"
        ]

predictive_analytics = PredictiveAnalytics()