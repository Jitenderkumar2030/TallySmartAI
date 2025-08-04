import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

class BusinessIntelligence:
    def __init__(self):
        self.kpi_thresholds = {
            'revenue_growth': {'good': 0.1, 'warning': 0.05},
            'profit_margin': {'good': 0.15, 'warning': 0.08},
            'cash_conversion': {'good': 30, 'warning': 60}
        }
    
    def generate_executive_dashboard(self, df):
        """Generate executive-level business intelligence dashboard"""
        # Calculate KPIs
        kpis = self._calculate_kpis(df)
        
        # Create comprehensive dashboard
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=('Revenue Trend', 'Profit Analysis', 
                          'Cash Flow', 'Expense Breakdown',
                          'Growth Metrics', 'Risk Assessment'),
            specs=[[{"secondary_y": True}, {"type": "pie"}],
                   [{"colspan": 2}, None],
                   [{"type": "indicator"}, {"type": "bar"}]]
        )
        
        # Revenue trend with moving average
        df['Date'] = pd.to_datetime(df['Date'])
        monthly_revenue = df.groupby(df['Date'].dt.to_period('M'))['Amount'].sum()
        
        fig.add_trace(
            go.Scatter(x=monthly_revenue.index.astype(str), y=monthly_revenue.values,
                      name="Monthly Revenue", line=dict(color='blue')),
            row=1, col=1
        )
        
        # Add more visualizations...
        
        return fig, kpis
    
    def _calculate_kpis(self, df):
        """Calculate key performance indicators"""
        if len(df) < 2:
            return {}
        
        total_revenue = df['Amount'].sum()
        avg_transaction = df['Amount'].mean()
        transaction_count = len(df)
        
        # Calculate growth rate (simplified)
        df['Date'] = pd.to_datetime(df['Date'])
        df_sorted = df.sort_values('Date')
        recent_period = df_sorted.tail(30)['Amount'].sum()
        previous_period = df_sorted.iloc[-60:-30]['Amount'].sum() if len(df_sorted) >= 60 else recent_period
        
        growth_rate = (recent_period - previous_period) / previous_period if previous_period > 0 else 0
        
        return {
            'total_revenue': total_revenue,
            'avg_transaction_value': avg_transaction,
            'transaction_count': transaction_count,
            'growth_rate': growth_rate,
            'revenue_per_day': total_revenue / max(1, (df['Date'].max() - df['Date'].min()).days),
            'volatility': df['Amount'].std() / df['Amount'].mean() if df['Amount'].mean() > 0 else 0
        }
    
    def generate_competitor_analysis(self, user_data, industry_benchmarks):
        """Compare user performance against industry benchmarks"""
        user_kpis = self._calculate_kpis(user_data)
        
        comparison = {}
        for metric, user_value in user_kpis.items():
            if metric in industry_benchmarks:
                benchmark = industry_benchmarks[metric]
                comparison[metric] = {
                    'user_value': user_value,
                    'industry_avg': benchmark,
                    'performance': 'above' if user_value > benchmark else 'below',
                    'gap_percentage': ((user_value - benchmark) / benchmark * 100) if benchmark > 0 else 0
                }
        
        return comparison

business_intelligence = BusinessIntelligence()