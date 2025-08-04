import logging
import traceback
from functools import wraps
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app_errors.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ErrorHandler:
    def __init__(self):
        self.error_counts = {}
        
    def handle_errors(self, func):
        """Comprehensive error handling decorator"""
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise  # Re-raise HTTP exceptions
            except Exception as e:
                return self._handle_exception(func.__name__, e, args, kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except HTTPException:
                raise  # Re-raise HTTP exceptions
            except Exception as e:
                return self._handle_exception(func.__name__, e, args, kwargs)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    def _handle_exception(self, func_name, error, args, kwargs):
        """Handle and log exceptions"""
        error_id = f"{func_name}_{type(error).__name__}"
        self.error_counts[error_id] = self.error_counts.get(error_id, 0) + 1
        
        # Log error details
        logger.error(f"""
        Function: {func_name}
        Error: {str(error)}
        Type: {type(error).__name__}
        Count: {self.error_counts[error_id]}
        Args: {str(args)[:200]}
        Kwargs: {str(kwargs)[:200]}
        Traceback: {traceback.format_exc()}
        """)
        
        # Return appropriate error response
        if "database" in str(error).lower():
            return {"error": "Database connection issue", "code": "DB_ERROR"}
        elif "api" in str(error).lower() or "openai" in str(error).lower():
            return {"error": "External API error", "code": "API_ERROR"}
        elif "file" in str(error).lower():
            return {"error": "File processing error", "code": "FILE_ERROR"}
        else:
            return {"error": "Internal server error", "code": "INTERNAL_ERROR"}

# Global error handler instance
error_handler = ErrorHandler()

# FastAPI exception handlers
async def validation_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "details": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }
    )