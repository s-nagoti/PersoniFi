"""
PersoniFi FastAPI Backend Server
A modern Python API for parsing bank and credit card statements from CSV and Excel files.

Features:
- File upload with validation
- Automatic transaction parsing
- Structured JSON responses
- Built-in API documentation
- Rate limiting and security
- Error handling

Dependencies:
- fastapi: Modern web framework
- uvicorn: ASGI server
- slowapi: Rate limiting
- python-multipart: File upload support
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import tempfile
import shutil
from datetime import datetime
from typing import List, Optional, Dict, Any
import uvicorn
import logging

# Import our existing parser
from python.transaction_parser import parse_transactions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PersoniFi Backend API",
    description="Backend service for parsing bank and credit card statements from CSV and Excel files",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    openapi_url="/openapi.json"
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",
        "http://localhost:3000", 
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*"]
)

# File validation constants
ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls'}
ALLOWED_MIME_TYPES = {
    'text/csv',
    'application/csv', 
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_file(file: UploadFile) -> None:
    """
    Validate uploaded file for type and size.
    
    Args:
        file: The uploaded file
        
    Raises:
        HTTPException: If file validation fails
    """
    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file_ext}'. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check MIME type
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        logger.warning(f"Unexpected MIME type: {file.content_type} for file: {file.filename}")
    
    # File size is handled by FastAPI automatically, but we can add custom logic here if needed

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "PersoniFi Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/health"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "success": True,
        "message": "PersoniFi Backend is running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/formats")
async def get_supported_formats():
    """Get information about supported file formats and requirements"""
    return {
        "success": True,
        "supported_formats": {
            "csv": {
                "extensions": [".csv"],
                "mime_types": ["text/csv", "application/csv"],
                "max_size": "10MB"
            },
            "excel": {
                "extensions": [".xlsx", ".xls"],
                "mime_types": [
                    "application/vnd.ms-excel",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ],
                "max_size": "10MB"
            }
        },
        "required_columns": ["date", "amount", "merchant/description"],
        "optional_columns": ["category"],
        "example_structure": {
            "date": "YYYY-MM-DD",
            "merchant": "string",
            "amount": "float",
            "category": "string (optional)"
        },
        "column_keywords": {
            "date": ["date", "transaction date", "posted date", "trans date", "payment date"],
            "amount": ["amount", "transaction amount", "debit", "credit", "posted amount"],
            "merchant": ["description", "merchant", "transaction description", "payee", "memo"],
            "category": ["category", "transaction category", "type", "transaction type"]
        }
    }

@app.post("/api/parse-transactions")
@limiter.limit("100/minute")
async def parse_transactions_endpoint(
    request: Request,
    file: UploadFile = File(..., description="CSV or Excel file containing bank/credit card transactions")
):
    """
    Upload and parse a bank/credit card statement file.
    
    This endpoint accepts CSV or Excel files and returns structured transaction data.
    
    **Supported file types:**
    - CSV files (.csv)
    - Excel files (.xlsx, .xls)
    
    **Maximum file size:** 10MB
    
    **Response format:**
    - `success`: Boolean indicating if parsing was successful
    - `data`: Array of transaction objects
    - `metadata`: Information about the parsing process
    
    **Transaction object structure:**
    - `date`: Date in YYYY-MM-DD format
    - `merchant`: Merchant name or description
    - `amount`: Transaction amount as float
    - `category`: Transaction category (optional)
    """
    
    logger.info(f"Received file upload: {file.filename} ({file.size} bytes)")
    
    # Validate file
    try:
        validate_file(file)
    except HTTPException as e:
        logger.error(f"File validation failed: {e.detail}")
        raise e
    
    # Create temporary file
    temp_file = None
    temp_file_path = None
    
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            # Read file content in chunks to handle large files
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        logger.info(f"Saved file to temporary location: {temp_file_path}")
        
        # Parse the file using our existing parser
        result = parse_transactions(temp_file_path)
        
        if result["success"]:
            # Add metadata about the upload
            result["metadata"]["original_filename"] = file.filename
            result["metadata"]["file_size"] = file.size
            result["metadata"]["upload_timestamp"] = datetime.now().isoformat()
            result["metadata"]["processing_time"] = datetime.now().isoformat()
            
            logger.info(f"Successfully parsed {len(result['transactions'])} transactions from {file.filename}")
            
            return {
                "success": True,
                "data": result["transactions"],
                "metadata": result["metadata"]
            }
        else:
            logger.error(f"Parsing failed for {file.filename}: {result['error']}")
            raise HTTPException(
                status_code=400,
                detail=result["error"]
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
    
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                logger.error(f"Failed to clean up temporary file {temp_file_path}: {e}")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler for unexpected errors"""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "status_code": 500
        }
    )

if __name__ == "__main__":
    # Development server configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3000,
        reload=True,  # Auto-reload for development
        log_level="info",
        access_log=True
    )
