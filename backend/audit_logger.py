import sqlite3
import json
from datetime import datetime
import os

class AuditLogger:
    def __init__(self, db_path="audit_trail.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize audit trail database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                action TEXT NOT NULL,
                resource TEXT,
                details TEXT,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_action(self, user_email, action, resource=None, details=None, ip_address=None, session_id=None):
        """Log user action"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        details_json = json.dumps(details) if details else None
        
        cursor.execute('''
            INSERT INTO audit_logs (user_email, action, resource, details, ip_address, session_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_email, action, resource, details_json, ip_address, session_id))
        
        conn.commit()
        conn.close()
    
    def get_user_logs(self, user_email, limit=50):
        """Get recent logs for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT action, resource, timestamp, details
            FROM audit_logs 
            WHERE user_email = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (user_email, limit))
        
        logs = cursor.fetchall()
        conn.close()
        return logs

# Global instance
audit_logger = AuditLogger()