import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class TrendAnalyzer:
    def __init__(self):
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
    
    def detect_trends(self, df):
        """Detect sales spikes, seasonal trends, and patterns"""
        trends = {}
        
        if 'Date' in df.columns and 'Amount' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date')
            
            # Monthly aggregation
            monthly = df.groupby(df['Date'].dt.to_period('M'))['Amount'].sum()
            
            # Growth rate calculation
            growth_rates = monthly.pct_change().dropna()
            
            trends['avg_growth_rate'] = growth_rates.mean()
            trends['volatility'] = growth_rates.std()
            trends['seasonal_pattern'] = self._detect_seasonality(monthly)
            trends['trend_direction'] = 'increasing' if growth_rates.mean() > 0.05 else 'decreasing' if growth_rates.mean() < -0.05 else 'stable'
            
        return trends
    
    def detect_anomalies(self, df):
        """Detect unusual patterns and outliers"""
        anomalies = []
        
        if 'Amount' in df.columns:
            amounts = df['Amount'].values.reshape(-1, 1)
            outliers = self.anomaly_detector.fit_predict(amounts)
            
            anomaly_indices = np.where(outliers == -1)[0]
            
            for idx in anomaly_indices:
                anomalies.append({
                    'index': idx,
                    'amount': df.iloc[idx]['Amount'],
                    'date': df.iloc[idx].get('Date', 'Unknown'),
                    'severity': 'high' if abs(df.iloc[idx]['Amount']) > df['Amount'].std() * 2 else 'medium'
                })
        
        return anomalies
    
    def _detect_seasonality(self, series):
        """Simple seasonality detection"""
        if len(series) < 12:
            return "insufficient_data"
        
        # Check for quarterly patterns
        quarterly_avg = []
        for i in range(0, len(series), 3):
            quarterly_avg.append(series.iloc[i:i+3].mean())
        
        if len(quarterly_avg) > 1:
            q_std = np.std(quarterly_avg)
            q_mean = np.mean(quarterly_avg)
            if q_std / q_mean > 0.2:
                return "seasonal"
        
        return "non_seasonal"

def analyze_financial_trends(df):
    """Main function to analyze trends and anomalies"""
    analyzer = TrendAnalyzer()
    
    trends = analyzer.detect_trends(df)
    anomalies = analyzer.detect_anomalies(df)
    
    # Generate actionable insights
    insights = []
    
    if trends.get('trend_direction') == 'increasing':
        insights.append("📈 Positive growth trend detected")
    elif trends.get('trend_direction') == 'decreasing':
        insights.append("📉 Declining trend - requires attention")
    
    if len(anomalies) > 0:
        insights.append(f"⚠️ {len(anomalies)} anomalies detected")
    
    if trends.get('seasonal_pattern') == 'seasonal':
        insights.append("🔄 Seasonal patterns identified")
    
    return {
        'trends': trends,
        'anomalies': anomalies,
        'insights': insights
    }
