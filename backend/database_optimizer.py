import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime

class DatabaseOptimizer:
    def __init__(self, db_path="users.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for better concurrency
            conn.execute("PRAGMA synchronous=NORMAL")  # Balance between safety and speed
            conn.execute("PRAGMA cache_size=10000")  # Increase cache size
            conn.execute("PRAGMA temp_store=MEMORY")  # Store temp tables in memory
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def create_indexes(self):
        """Create performance indexes"""
        indexes = [
            # User table indexes
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
            "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
            
            # Audit log indexes
            "CREATE INDEX IF NOT EXISTS idx_audit_user_email ON audit_logs(user_email)",
            "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action)",
            
            # Client management indexes
            "CREATE INDEX IF NOT EXISTS idx_clients_email ON clients(email)",
            "CREATE INDEX IF NOT EXISTS idx_clients_business_type ON clients(business_type)",
            
            # Session indexes
            "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at)",
        ]
        
        with self.get_connection() as conn:
            for index_sql in indexes:
                try:
                    conn.execute(index_sql)
                    self.logger.info(f"Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
                except Exception as e:
                    self.logger.error(f"Failed to create index: {e}")
            conn.commit()
    
    def analyze_database(self):
        """Analyze database for optimization"""
        with self.get_connection() as conn:
            # Update table statistics
            conn.execute("ANALYZE")
            
            # Get table sizes
            cursor = conn.execute("""
                SELECT name, COUNT(*) as row_count 
                FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            
            stats = {}
            for table_name, _ in cursor.fetchall():
                count_cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = count_cursor.fetchone()[0]
                stats[table_name] = row_count
            
            return stats
    
    def vacuum_database(self):
        """Optimize database storage"""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
            self.logger.info("Database vacuum completed")
        except Exception as e:
            self.logger.error(f"Database vacuum failed: {e}")

# Initialize database optimizer
db_optimizer = DatabaseOptimizer()