import sqlite3
import pandas as pd
from datetime import datetime
import os

class ClientManager:
    def __init__(self, db_path="clients.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize client management database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                client_name TEXT NOT NULL,
                client_code TEXT UNIQUE NOT NULL,
                industry TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_code TEXT NOT NULL,
                data_type TEXT NOT NULL,
                file_name TEXT NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_summary TEXT,
                FOREIGN KEY (client_code) REFERENCES clients (client_code)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_client(self, user_email, client_name, industry="General"):
        """Add new client"""
        client_code = f"CLT_{client_name.replace(' ', '_').upper()}_{datetime.now().strftime('%Y%m')}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO clients (user_email, client_name, client_code, industry)
                VALUES (?, ?, ?, ?)
            ''', (user_email, client_name, client_code, industry))
            conn.commit()
            return client_code
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()
    
    def get_user_clients(self, user_email):
        """Get all clients for a user"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('''
            SELECT client_name, client_code, industry, created_at, is_active
            FROM clients 
            WHERE user_email = ? AND is_active = 1
            ORDER BY created_at DESC
        ''', conn, params=(user_email,))
        conn.close()
        return df
    
    def log_client_data(self, client_code, data_type, file_name, summary=""):
        """Log uploaded data for client"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO client_data (client_code, data_type, file_name, data_summary)
            VALUES (?, ?, ?, ?)
        ''', (client_code, data_type, file_name, summary))
        
        conn.commit()
        conn.close()

# Global instance
client_manager = ClientManager()
