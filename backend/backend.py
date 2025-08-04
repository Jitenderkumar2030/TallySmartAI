from fastapi import FastAPI, File, UploadFile, Header, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import json
import jwt
from utils import preprocess, predict_sales
from auth import verify_token
from models import SessionLocal, User
from config.production_settings import get_settings
from backend.rate_limiter import rate_limiter, limiter
from backend.cache_manager import cache_manager
from backend.error_handler import error_handler, validation_exception_handler, http_exception_handler, general_exception_handler
from backend.health_monitor import health_monitor
from backend.database_optimizer import db_optimizer
import asyncio
import logging

# Initialize settings
settings = get_settings()

app = FastAPI(
    title="TallySmartAI API",
    description="AI-Powered Financial Analytics Platform",
    version="2.0.0"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if hasattr(settings, 'cors_origins') else ["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add error handlers
app.add_exception_handler(422, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    try:
        # Create database indexes
        db_optimizer.create_indexes()
        
        # Start health monitoring
        if settings.enable_health_checks:
            asyncio.create_task(periodic_health_check())
        
        logging.info("TallySmartAI API started successfully")
    except Exception as e:
        logging.error(f"Startup error: {e}")

async def periodic_health_check():
    """Run periodic health checks"""
    while True:
        try:
            await health_monitor.comprehensive_health_check()
            await asyncio.sleep(settings.health_check_interval)
        except Exception as e:
            logging.error(f"Health check error: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute

# Health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    return await health_monitor.comprehensive_health_check()

@app.get("/health/trends")
async def health_trends(hours: int = 24):
    """Get health trends"""
    return health_monitor.get_health_trends(hours)

# Token verification endpoint
@app.post("/verify")
@limiter.limit("10/minute")
@error_handler.handle_errors
async def verify(request: Request, data: dict):
    """Verify JWT token"""
    rate_limiter.check_rate_limit(f"verify:{request.client.host}", "login")
    
    try:
        payload = jwt.decode(data["token"], settings.jwt_secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Prediction endpoint with caching
@app.post("/predict")
@limiter.limit("10/minute")
@cache_manager.cache_result(expiry=1800, key_prefix="predict:")
@error_handler.handle_errors
async def predict(request: Request, file: UploadFile = File(...), authorization: str = Header(None)):
    """AI prediction endpoint with rate limiting and caching"""
    rate_limiter.check_rate_limit(f"predict:{request.client.host}", "predict")
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
    except (IndexError, jwt.InvalidTokenError):
        raise HTTPException(status_code=401, detail="Invalid authorization token")

    if payload["role"] not in ["pro", "admin"]:
        raise HTTPException(status_code=403, detail="Upgrade to Pro to access forecasting")

    # Validate file
    if file.size > settings.max_upload_size:
        raise HTTPException(status_code=413, detail="File too large")
    
    # Process file
    df = pd.read_csv(file.file)
    df = preprocess(df)
    forecast = predict_sales(df)
    
    return forecast.tail(5).to_dict(orient="records")

# Cashfree webhook with enhanced error handling
@app.post("/cashfree-webhook")
@error_handler.handle_errors
async def cashfree_webhook(request: Request):
    """Enhanced Cashfree webhook handler"""
    body = await request.body()
    
    try:
        data = json.loads(body)
        logging.info(f"Cashfree Webhook: {data}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if data.get("event") == "SUBSCRIPTION_ACTIVATED":
        email = data["data"]["customer_details"]["customer_email"]
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email).first()
            if user:
                user.role = "pro"
                db.commit()
                
                # Invalidate user cache
                cache_manager.invalidate_pattern(f"user:{email}:*")
                
                logging.info(f"User {email} upgraded to Pro")
            else:
                logging.warning(f"User {email} not found for upgrade")
        finally:
            db.close()

    return {"status": "ok"}

# Cache management endpoints
@app.get("/admin/cache/stats")
@error_handler.handle_errors
async def cache_stats():
    """Get cache statistics"""
    return cache_manager.get_cache_stats()

@app.post("/admin/cache/clear")
@error_handler.handle_errors
async def clear_cache(pattern: str = "*"):
    """Clear cache by pattern"""
    cleared = cache_manager.invalidate_pattern(pattern)
    return {"cleared_keys": cleared}

# Database optimization endpoint
@app.post("/admin/database/optimize")
@error_handler.handle_errors
async def optimize_database():
    """Optimize database performance"""
    stats = db_optimizer.analyze_database()
    db_optimizer.vacuum_database()
    return {"status": "optimized", "table_stats": stats}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
