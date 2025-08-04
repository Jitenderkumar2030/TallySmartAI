from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import time
import hashlib
from collections import defaultdict
import jwt
import os

class SecurityMiddleware:
    def __init__(self):
        self.rate_limits = defaultdict(list)
        self.failed_attempts = defaultdict(int)
        self.blocked_ips = set()
        self.jwt_secret = os.getenv('JWT_SECRET_KEY', 'fallback_secret')
    
    async def rate_limit_middleware(self, request: Request, call_next):
        """Rate limiting middleware"""
        client_ip = request.client.host
        current_time = time.time()
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            raise HTTPException(status_code=429, detail="IP temporarily blocked")
        
        # Rate limiting logic
        self.rate_limits[client_ip] = [
            timestamp for timestamp in self.rate_limits[client_ip]
            if current_time - timestamp < 60  # 1 minute window
        ]
        
        if len(self.rate_limits[client_ip]) >= 100:  # 100 requests per minute
            self.blocked_ips.add(client_ip)
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        self.rate_limits[client_ip].append(current_time)
        
        response = await call_next(request)
        return response
    
    def validate_file_upload(self, file):
        """Validate uploaded files for security"""
        # Check file size (max 50MB)
        if file.size > 50 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large")
        
        # Check file type
        allowed_types = ['.csv', '.pdf', '.xlsx', '.xls']
        if not any(file.filename.lower().endswith(ext) for ext in allowed_types):
            raise HTTPException(status_code=400, detail="File type not allowed")
        
        # Scan for malicious content (basic check)
        content = file.file.read(1024)  # Read first 1KB
        file.file.seek(0)  # Reset file pointer
        
        malicious_patterns = [b'<script', b'javascript:', b'<?php']
        if any(pattern in content.lower() for pattern in malicious_patterns):
            raise HTTPException(status_code=400, detail="Potentially malicious file")
        
        return True
    
    def encrypt_sensitive_data(self, data):
        """Encrypt sensitive data before storage"""
        from cryptography.fernet import Fernet
        
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            key = Fernet.generate_key()
        
        f = Fernet(key)
        return f.encrypt(data.encode()).decode()
    
    def audit_log_access(self, user_email, resource, action):
        """Enhanced audit logging with security focus"""
        from backend.audit_logger import audit_logger
        
        audit_logger.log_action(
            user_email=user_email,
            action=action,
            resource=resource,
            details={
                'timestamp': time.time(),
                'security_level': 'high' if action in ['login', 'data_export'] else 'normal'
            }
        )

security_middleware = SecurityMiddleware()