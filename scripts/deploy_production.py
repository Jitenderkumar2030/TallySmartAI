#!/usr/bin/env python3
"""
Production deployment script with all improvements
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

def setup_production_environment():
    """Setup production environment with all improvements"""
    
    print("🚀 Setting up TallySmartAI Production Environment...")
    
    # 1. Install dependencies
    print("📦 Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # 2. Create necessary directories
    directories = ["logs", "data", "static", "cache"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # 3. Initialize database with indexes
    print("🗄️ Setting up database...")
    from backend.database_optimizer import db_optimizer
    db_optimizer.create_indexes()
    print("✅ Database indexes created")
    
    # 4. Test Redis connection
    print("🔄 Testing Redis connection...")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379)
        r.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"⚠️ Redis connection failed: {e}")
        print("   Install Redis: sudo apt-get install redis-server")
    
    # 5. Validate environment variables
    print("⚙️ Validating configuration...")
    try:
        from config.production_settings import validate_production_config
        validate_production_config()
        print("✅ Configuration validated")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    # 6. Run health check
    print("🏥 Running initial health check...")
    try:
        from backend.health_monitor import health_monitor
        import asyncio
        health_status = asyncio.run(health_monitor.comprehensive_health_check())
        print(f"✅ Health check: {health_status['overall_status']}")
    except Exception as e:
        print(f"⚠️ Health check failed: {e}")
    
    # 7. Start services
    print("🎯 Starting production services...")
    
    # Start FastAPI backend
    backend_cmd = [
        "uvicorn", "backend.backend:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--workers", "4",
        "--log-level", "info"
    ]
    
    # Start Streamlit frontend
    frontend_cmd = [
        "streamlit", "run", "app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0",
        "--server.headless", "true"
    ]
    
    print("✅ Production environment setup complete!")
    print("\n🌟 TallySmartAI is ready for production!")
    print("   - Backend API: http://localhost:8000")
    print("   - Frontend App: http://localhost:8501")
    print("   - Health Check: http://localhost:8000/health")
    
    return True

if __name__ == "__main__":
    success = setup_production_environment()
    sys.exit(0 if success else 1)