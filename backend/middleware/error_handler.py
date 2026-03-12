"""
Error handling middleware for Karat API
Provides consistent error responses and logging
"""

import logging
import time
from typing import Dict, Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import traceback


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ErrorHandler(BaseHTTPMiddleware):
    """Global error handling middleware"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Add processing time header
            process_time = (time.time() - start_time) * 1000
            response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
            
            return response
            
        except HTTPException as e:
            return self._handle_http_exception(e, request)
        except Exception as e:
            return self._handle_unexpected_error(e, request)
    
    def _handle_http_exception(self, exc: HTTPException, request: Request) -> JSONResponse:
        """Handle HTTP exceptions with proper formatting"""
        error_response = {
            "error": {
                "type": "http_error",
                "code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url.path)
            },
            "timestamp": time.time(),
            "request_id": self._get_request_id(request)
        }
        
        logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response
        )
    
    def _handle_unexpected_error(self, exc: Exception, request: Request) -> JSONResponse:
        """Handle unexpected errors with proper formatting"""
        error_response = {
            "error": {
                "type": "internal_error",
                "code": 500,
                "message": "An unexpected error occurred",
                "path": str(request.url.path)
            },
            "timestamp": time.time(),
            "request_id": self._get_request_id(request)
        }
        
        # Log full error details for debugging
        logger.error(f"Unexpected error: {str(exc)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return JSONResponse(
            status_code=500,
            content=error_response
        )
    
    def _get_request_id(self, request: Request) -> str:
        """Extract or generate request ID for tracing"""
        # Try to get from headers first
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            # Generate a simple request ID
            request_id = f"req_{int(time.time() * 1000)}"
        return request_id


class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)


class DatabaseError(Exception):
    """Custom database error"""
    def __init__(self, message: str, operation: str = None):
        self.message = message
        self.operation = operation
        super().__init__(message)


class ExternalServiceError(Exception):
    """Custom external service error (e.g., Plaid)"""
    def __init__(self, message: str, service: str = None):
        self.message = message
        self.service = service
        super().__init__(message)


def create_error_response(
    error_type: str,
    message: str,
    status_code: int = 400,
    details: Dict[str, Any] = None
) -> JSONResponse:
    """Create standardized error response"""
    error_content = {
        "error": {
            "type": error_type,
            "code": status_code,
            "message": message
        },
        "timestamp": time.time()
    }
    
    if details:
        error_content["error"]["details"] = details
    
    return JSONResponse(
        status_code=status_code,
        content=error_content
    )


def handle_validation_error(error: ValidationError) -> HTTPException:
    """Convert validation error to HTTP exception"""
    message = f"Validation error: {error.message}"
    if error.field:
        message += f" (field: {error.field})"
    
    return HTTPException(
        status_code=422,
        detail=message
    )


def handle_database_error(error: DatabaseError) -> HTTPException:
    """Convert database error to HTTP exception"""
    message = f"Database error: {error.message}"
    if error.operation:
        message += f" (operation: {error.operation})"
    
    return HTTPException(
        status_code=500,
        detail=message
    )


def handle_external_service_error(error: ExternalServiceError) -> HTTPException:
    """Convert external service error to HTTP exception"""
    message = f"External service error: {error.message}"
    if error.service:
        message += f" (service: {error.service})"
    
    return HTTPException(
        status_code=502,
        detail=message
    )
