import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class ProductionSettings(BaseSettings):
    # App Configuration
    app_name: str = "TallySmartAI"
    environment: str = "production"
    debug: bool = False
    
    # Security
    jwt_secret_key: str
    encryption_key: str
    allowed_hosts: list = ["*"]
    
    # Database
    database_url: str = "sqlite:///data/production.db"
    database_pool_size: int = 20
    database_max_overflow: int = 30
    
    # Redis Cache
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    cache_timeout: int = 3600
    
    # API Keys
    openai_api_key: str
    cashfree_client_id: str
    cashfree_client_secret: str
    telegram_bot_token: str
    
    # Rate Limiting
    rate_limit_per_minute: int = 100
    max_upload_size: int = 50 * 1024 * 1024  # 50MB
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/tallysmartai.log"
    
    # Performance
    enable_caching: bool = True
    enable_compression: bool = True
    
    # Features
    enable_voice_commands: bool = True
    enable_pdf_parser: bool = True
    enable_gst_analyzer: bool = True
    
    # Email Configuration
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    notification_email: str = ""
    notification_password: str = ""
    
    # Monitoring
    enable_health_checks: bool = True
    health_check_interval: int = 300  # 5 minutes
    
    class Config:
        env_file = ".env.production"
        case_sensitive = False

@lru_cache()
def get_settings():
    return ProductionSettings()

# Validation function
def validate_production_config():
    """Validate all required production settings"""
    settings = get_settings()
    required_fields = [
        'jwt_secret_key', 'encryption_key', 'openai_api_key',
        'cashfree_client_id', 'cashfree_client_secret', 'telegram_bot_token'
    ]
    
    missing_fields = []
    for field in required_fields:
        value = getattr(settings, field, None)
        if not value or value.startswith('your_'):
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"Missing required production settings: {missing_fields}")
    
    return settings