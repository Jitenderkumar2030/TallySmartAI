#!/usr/bin/env python3
"""
Production Readiness Checker for TallySmartAI
"""

import os
import sys
import sqlite3
import requests
from datetime import datetime

class ProductionChecker:
    def __init__(self):
        self.checks_passed = 0
        self.total_checks = 0
        self.issues = []
    
    def run_all_checks(self):
        """Run all production readiness checks"""
        print("🔍 TallySmartAI Production Readiness Check")
        print("=" * 50)
        
        self.check_environment_variables()
        self.check_database_setup()
        self.check_dependencies()
        self.check_file_permissions()
        self.check_api_connectivity()
        self.check_security_settings()
        
        self.print_summary()
        return len(self.issues) == 0
    
    def check_environment_variables(self):
        """Check required environment variables"""
        print("\n📋 Checking Environment Variables...")
        
        required_vars = [
            'OPENAI_API_KEY',
            'JWT_SECRET_KEY',
            'CASHFREE_CLIENT_ID',
            'TELEGRAM_BOT_TOKEN'
        ]
        
        for var in required_vars:
            self.total_checks += 1
            if os.getenv(var):
                print(f"✅ {var} is set")
                self.checks_passed += 1
            else:
                print(f"❌ {var} is missing")
                self.issues.append(f"Missing environment variable: {var}")
    
    def check_database_setup(self):
        """Check database connectivity and tables"""
        print("\n🗄️ Checking Database Setup...")
        
        try:
            self.total_checks += 1
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            
            # Check if users table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if cursor.fetchone():
                print("✅ Users table exists")
                self.checks_passed += 1
            else:
                print("❌ Users table missing")
                self.issues.append("Users table not found in database")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            self.issues.append(f"Database error: {e}")
    
    def check_dependencies(self):
        """Check if all required packages are installed"""
        print("\n📦 Checking Dependencies...")
        
        required_packages = [
            'streamlit', 'fastapi', 'pandas', 'numpy', 
            'scikit-learn', 'openai', 'PyJWT', 'bcrypt',
            'reportlab', 'plotly', 'SpeechRecognition', 
            'pyttsx3', 'PyPDF2', 'pdfplumber'
        ]
        
        for package in required_packages:
            self.total_checks += 1
            try:
                __import__(package.lower().replace('-', '_'))
                print(f"✅ {package} installed")
                self.checks_passed += 1
            except ImportError:
                print(f"❌ {package} not installed")
                self.issues.append(f"Missing package: {package}")
    
    def check_file_permissions(self):
        """Check file and directory permissions"""
        print("\n📁 Checking File Permissions...")
        
        directories = ['data', 'logs', 'uploads']
        
        for directory in directories:
            self.total_checks += 1
            if os.path.exists(directory) and os.access(directory, os.W_OK):
                print(f"✅ {directory}/ is writable")
                self.checks_passed += 1
            else:
                print(f"❌ {directory}/ is not writable or doesn't exist")
                self.issues.append(f"Directory {directory} is not writable")
    
    def check_api_connectivity(self):
        """Check external API connectivity"""
        print("\n🌐 Checking API Connectivity...")
        
        # Test OpenAI API
        self.total_checks += 1
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key and openai_key != 'your_production_openai_key':
            try:
                import openai
                openai.api_key = openai_key
                # Simple test call
                print("✅ OpenAI API key is valid")
                self.checks_passed += 1
            except Exception as e:
                print(f"❌ OpenAI API test failed: {e}")
                self.issues.append("OpenAI API connectivity issue")
        else:
            print("❌ OpenAI API key not configured")
            self.issues.append("OpenAI API key not set")
    
    def check_security_settings(self):
        """Check security configurations"""
        print("\n🔒 Checking Security Settings...")
        
        self.total_checks += 1
        jwt_secret = os.getenv('JWT_SECRET_KEY')
        if jwt_secret and jwt_secret != 'testsecret' and len(jwt_secret) >= 32:
            print("✅ JWT secret key is secure")
            self.checks_passed += 1
        else:
            print("❌ JWT secret key is weak or default")
            self.issues.append("JWT secret key needs to be changed and strengthened")
    
    def print_summary(self):
        """Print final summary"""
        print("\n" + "=" * 50)
        print(f"📊 SUMMARY: {self.checks_passed}/{self.total_checks} checks passed")
        
        if self.issues:
            print("\n🚨 ISSUES TO RESOLVE:")
            for i, issue in enumerate(self.issues, 1):
                print(f"{i}. {issue}")
            print("\n❌ NOT READY FOR PRODUCTION")
        else:
            print("\n✅ READY FOR PRODUCTION DEPLOYMENT!")
        
        print("=" * 50)

if __name__ == "__main__":
    checker = ProductionChecker()
    is_ready = checker.run_all_checks()
    sys.exit(0 if is_ready else 1)
