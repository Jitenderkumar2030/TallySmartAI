import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import json
from datetime import datetime
import os

class NotificationSystem:
    def __init__(self):
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', 587)),
            'email': os.getenv('NOTIFICATION_EMAIL'),
            'password': os.getenv('NOTIFICATION_PASSWORD')
        }
        self.webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    
    def send_critical_alert(self, user_email, alert_type, message, data=None):
        """Send critical business alerts"""
        alert_config = {
            'cash_flow_crisis': {
                'subject': '🚨 URGENT: Cash Flow Crisis Detected',
                'priority': 'HIGH',
                'channels': ['email', 'sms', 'slack']
            },
            'gst_compliance_issue': {
                'subject': '⚠️ GST Compliance Issue Detected',
                'priority': 'MEDIUM',
                'channels': ['email', 'slack']
            },
            'anomaly_detected': {
                'subject': '🔍 Financial Anomaly Detected',
                'priority': 'MEDIUM',
                'channels': ['email']
            },
            'forecast_ready': {
                'subject': '📊 Your Financial Forecast is Ready',
                'priority': 'LOW',
                'channels': ['email']
            }
        }
        
        config = alert_config.get(alert_type, alert_config['forecast_ready'])
        
        # Send via configured channels
        for channel in config['channels']:
            try:
                if channel == 'email':
                    self._send_email(user_email, config['subject'], message, data)
                elif channel == 'slack':
                    self._send_slack_notification(config['subject'], message)
                elif channel == 'sms':
                    self._send_sms_notification(user_email, message)
            except Exception as e:
                print(f"Failed to send {channel} notification: {e}")
    
    def _send_email(self, to_email, subject, message, data=None):
        """Send email notification"""
        if not self.email_config['email']:
            return
        
        msg = MIMEMultipart()
        msg['From'] = self.email_config['email']
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Create HTML email body
        html_body = f"""
        <html>
        <body>
            <h2>{subject}</h2>
            <p>{message}</p>
            {self._format_data_for_email(data) if data else ''}
            <hr>
            <p><small>Sent by TallySmartAI at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
            server.starttls()
            server.login(self.email_config['email'], self.email_config['password'])
            server.send_message(msg)
    
    def _send_slack_notification(self, title, message):
        """Send Slack notification"""
        if not self.webhook_url:
            return
        
        payload = {
            "text": f"{title}\n{message}",
            "username": "TallySmartAI",
            "icon_emoji": ":chart_with_upwards_trend:"
        }
        
        requests.post(self.webhook_url, json=payload)
    
    def _format_data_for_email(self, data):
        """Format data for email display"""
        if isinstance(data, dict):
            formatted = "<ul>"
            for key, value in data.items():
                formatted += f"<li><strong>{key}:</strong> {value}</li>"
            formatted += "</ul>"
            return formatted
        return str(data)

notification_system = NotificationSystem()