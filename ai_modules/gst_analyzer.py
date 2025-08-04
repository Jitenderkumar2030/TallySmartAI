import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re

class GSTAnomalyDetector:
    def __init__(self):
        self.gst_rates = [0, 5, 12, 18, 28]  # Standard GST rates in India
        self.hsn_patterns = {
            'services': range(99, 100),
            'goods': range(1, 99)
        }
    
    def detect_gst_anomalies(self, df):
        """Detect GST-related anomalies in financial data"""
        anomalies = []
        
        # Check for GST rate anomalies
        if 'GST_Rate' in df.columns:
            invalid_rates = df[~df['GST_Rate'].isin(self.gst_rates + [np.nan])]
            for idx, row in invalid_rates.iterrows():
                anomalies.append({
                    'type': 'invalid_gst_rate',
                    'severity': 'high',
                    'message': f"Invalid GST rate {row['GST_Rate']}% found",
                    'row_index': idx,
                    'suggestion': 'Verify GST rate against current tax slab'
                })
        
        # Check for missing GST on taxable items
        if 'Amount' in df.columns and 'GST_Amount' in df.columns:
            taxable_threshold = 20  # Minimum amount for GST applicability
            missing_gst = df[(df['Amount'] > taxable_threshold) & 
                           (df['GST_Amount'].fillna(0) == 0)]
            
            for idx, row in missing_gst.head(10).iterrows():
                anomalies.append({
                    'type': 'missing_gst',
                    'severity': 'medium',
                    'message': f"No GST on ₹{row['Amount']:,.2f} transaction",
                    'row_index': idx,
                    'suggestion': 'Check if GST exemption applies or add GST'
                })
        
        # Check for GST calculation errors
        if all(col in df.columns for col in ['Amount', 'GST_Rate', 'GST_Amount']):
            df_calc = df.dropna(subset=['Amount', 'GST_Rate', 'GST_Amount'])
            expected_gst = df_calc['Amount'] * df_calc['GST_Rate'] / 100
            gst_diff = abs(df_calc['GST_Amount'] - expected_gst)
            
            incorrect_gst = df_calc[gst_diff > 1]  # Allow ₹1 tolerance
            for idx, row in incorrect_gst.head(10).iterrows():
                expected = row['Amount'] * row['GST_Rate'] / 100
                anomalies.append({
                    'type': 'gst_calculation_error',
                    'severity': 'high',
                    'message': f"GST mismatch: Expected ₹{expected:.2f}, Found ₹{row['GST_Amount']:.2f}",
                    'row_index': idx,
                    'suggestion': 'Recalculate GST amount'
                })
        
        # Check for duplicate GSTIN entries
        if 'GSTIN' in df.columns:
            gstin_pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
            invalid_gstin = df[df['GSTIN'].notna() & 
                             ~df['GSTIN'].str.match(gstin_pattern)]
            
            for idx, row in invalid_gstin.head(5).iterrows():
                anomalies.append({
                    'type': 'invalid_gstin',
                    'severity': 'high',
                    'message': f"Invalid GSTIN format: {row['GSTIN']}",
                    'row_index': idx,
                    'suggestion': 'Verify GSTIN format (15 characters)'
                })
        
        return anomalies
    
    def generate_gst_compliance_report(self, df):
        report = {
            'total_transactions': len(df),
            'gst_applicable': 0,
            'total_gst_collected': 0,
            'compliance_score': 0
        }
        
        if 'GST_Amount' in df.columns:
            report['gst_applicable'] = len(df[df['GST_Amount'].fillna(0) > 0])
            report['total_gst_collected'] = df['GST_Amount'].fillna(0).sum()
        
        anomalies = self.detect_gst_anomalies(df)
        critical_issues = len([a for a in anomalies if a['severity'] == 'high'])
        
        # Calculate compliance score (0-100)
        if report['total_transactions'] > 0:
            error_rate = critical_issues / report['total_transactions']
            report['compliance_score'] = max(0, 100 - (error_rate * 100))
        
        report['anomalies'] = anomalies
        return report

# Global instance
gst_detector = GSTAnomalyDetector()
