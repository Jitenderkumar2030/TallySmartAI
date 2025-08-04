import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from datetime import datetime
import io

class ReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
    
    def generate_comparative_report(self, df1, df2, period1_name, period2_name):
        """Generate comparative analysis report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Title
        title = Paragraph(f"Comparative Financial Analysis: {period1_name} vs {period2_name}", 
                         self.styles['Title'])
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Summary comparison
        summary1 = self._calculate_summary(df1)
        summary2 = self._calculate_summary(df2)
        
        comparison_data = [
            ['Metric', period1_name, period2_name, 'Change %'],
            ['Total Revenue', f"₹{summary1['total']:,.2f}", f"₹{summary2['total']:,.2f}", 
             f"{((summary2['total'] - summary1['total']) / summary1['total'] * 100):+.1f}%"],
            ['Average Transaction', f"₹{summary1['avg']:,.2f}", f"₹{summary2['avg']:,.2f}",
             f"{((summary2['avg'] - summary1['avg']) / summary1['avg'] * 100):+.1f}%"],
            ['Transaction Count', f"{summary1['count']:,}", f"{summary2['count']:,}",
             f"{((summary2['count'] - summary1['count']) / summary1['count'] * 100):+.1f}%"]
        ]
        
        table = Table(comparison_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
        
        # Key insights
        insights = self._generate_insights(summary1, summary2)
        story.append(Paragraph("Key Insights:", self.styles['Heading2']))
        for insight in insights:
            story.append(Paragraph(f"• {insight}", self.styles['Normal']))
            story.append(Spacer(1, 6))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _calculate_summary(self, df):
        """Calculate summary statistics"""
        if 'Amount' in df.columns:
            return {
                'total': df['Amount'].sum(),
                'avg': df['Amount'].mean(),
                'count': len(df),
                'max': df['Amount'].max(),
                'min': df['Amount'].min()
            }
        return {'total': 0, 'avg': 0, 'count': 0, 'max': 0, 'min': 0}
    
    def _generate_insights(self, summary1, summary2):
        """Generate business insights from comparison"""
        insights = []
        
        revenue_change = ((summary2['total'] - summary1['total']) / summary1['total'] * 100)
        if revenue_change > 10:
            insights.append(f"Strong revenue growth of {revenue_change:.1f}% indicates business expansion")
        elif revenue_change < -10:
            insights.append(f"Revenue decline of {abs(revenue_change):.1f}% requires immediate attention")
        
        count_change = ((summary2['count'] - summary1['count']) / summary1['count'] * 100)
        if count_change > revenue_change:
            insights.append("Increased transaction volume with stable pricing strategy")
        elif count_change < revenue_change:
            insights.append("Revenue growth driven by higher transaction values")
        
        return insights

# Global instance
report_generator = ReportGenerator()