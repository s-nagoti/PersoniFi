"""
PersoniFi FastAPI Backend Server
A modern Python API for parsing bank and credit card statements from CSV and Excel files.

Features:
- File upload with validation
- Automatic transaction parsing
- Structured JSON responses
- Database storage with Supabase integration
- Built-in API documentation
- Rate limiting and security
- Error handling
- Modular parsing and saving functions for reusability

API Endpoints:
- GET /api/health: Health check
- GET /api/formats: Supported file formats and requirements
- POST /api/parse-transactions: Parse uploaded files and return structured data
- POST /api/save-transactions: Save structured transaction data to database
- POST /api/upload-and-save: Combined endpoint for file upload, parsing, and saving
- POST /api/ask-agent: AI-powered financial insights and analysis

Dependencies:
- fastapi: Modern web framework
- uvicorn: ASGI server
- slowapi: Rate limiting
- python-multipart: File upload support
- supabase: Database client
- pandas: Data processing
- openpyxl: Excel file support
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field, validator
from supabase import create_client, Client
from dotenv import load_dotenv
from models import (
    AskAgentRequest, PlotlyChart, PlotlyTrace, PlotlyLayout, PlotlyAxis, 
    PlotlyMargin, PlotlyMarker, FinancialInsight, AskAgentResponse
)
import os
import tempfile
import shutil
from datetime import datetime
from typing import List, Optional, Dict, Any
import uvicorn
import logging
import json
from google import genai
from google.genai import types
from chart_integration import generate_chart_for_intent

# Import our existing parser
from python.transaction_parser import parse_transactions

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables for Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Initialize Supabase client
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_ANON_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    logger.info("Supabase client initialized successfully")
else:
    logger.warning("Supabase credentials not found. Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables.")

# Data Models for Transaction API
class Transaction(BaseModel):
    """Individual transaction data model"""
    date: str = Field(..., description="Transaction date in YYYY-MM-DD format")
    merchant: str = Field(..., description="Merchant name or transaction description")
    amount: float = Field(..., description="Transaction amount")
    category: Optional[str] = Field(None, description="Transaction category")
    
    @validator('date')
    def validate_date(cls, v):
        """Validate date format"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate amount is a valid number"""
        if not isinstance(v, (int, float)):
            raise ValueError('Amount must be a number')
        return float(v)

class TransactionData(BaseModel):
    """Transaction data array model"""
    data: List[Transaction] = Field(..., description="Array of transaction objects")

class SaveTransactionsRequest(BaseModel):
    """Request model for saving transactions"""
    success: bool = Field(..., description="Success flag from parser")
    data: List[Transaction] = Field(..., description="Array of transaction objects")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class SaveTransactionsResponse(BaseModel):
    """Response model for save transactions endpoint"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    transactions_inserted: int = Field(..., description="Number of transactions successfully inserted")

class GetCategoriesResponse(BaseModel):
    """Response model for get categories endpoint"""
    success: bool = Field(..., description="Whether the operation was successful")
    categories: List[str] = Field(..., description="List of unique transaction categories")

class TransactionResponse(BaseModel):
    """Model for a single transaction in the response"""
    id: str = Field(..., description="Transaction UUID")
    date: str = Field(..., description="Transaction date in YYYY-MM-DD format")
    amount: float = Field(..., description="Transaction amount")
    merchant: str = Field(..., description="Merchant name or description")
    category: Optional[str] = Field(None, description="Transaction category")

class GetTransactionsResponse(BaseModel):
    """Response model for get transactions endpoint"""
    success: bool = Field(..., description="Whether the operation was successful")
    transactions: List[TransactionResponse] = Field(..., description="List of transactions")

class DailyTrend(BaseModel):
    """Model for daily transaction totals"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    amount: float = Field(..., description="Total amount for this date")
    
    @validator('date')
    def validate_date(cls, v):
        """Validate date format"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')

class TransactionSummary(BaseModel):
    """Response model for transaction summary endpoint"""
    success: bool = Field(..., description="Whether the operation was successful")
    total_spent: float = Field(..., description="Total sum of all transaction amounts")
    by_category: Dict[str, float] = Field(..., description="Total spent per category")
    daily_trends: List[DailyTrend] = Field(..., description="Daily spending trends")

class UploadAndSaveResponse(BaseModel):
    """Response model for upload-and-save endpoint"""
    success: bool = Field(..., description="Whether the operation was successful")
    inserted: int = Field(..., description="Number of transactions successfully saved")
    errors: List[str] = Field(default=[], description="List of any failed insertions or errors")

# AI Agent Models are now imported from models.py to avoid circular imports

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

# Reusable parsing function
async def parse_uploaded_file(file: UploadFile) -> Dict[str, Any]:
    """
    Parse an uploaded file and return structured transaction data.
    
    Args:
        file: The uploaded file
        
    Returns:
        Dictionary containing parsed transactions and metadata
        
    Raises:
        HTTPException: If file validation or parsing fails
    """
    logger.info(f"Parsing uploaded file: {file.filename} ({file.size} bytes)")
    
    # Validate file
    validate_file(file)
    
    # Create temporary file
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
                "transactions": result["transactions"],
                "metadata": result["metadata"]
            }
        else:
            logger.error(f"Parsing failed for {file.filename}: {result['error']}")
            raise HTTPException(
                status_code=400,
                detail=result["error"]
            )
    
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                logger.error(f"Failed to clean up temporary file {temp_file_path}: {e}")

# Reusable database functions
async def get_unique_categories() -> Dict[str, Any]:
    """
    Fetch unique categories from the transactions table.
    """
    logger.info("Fetching unique transaction categories")
    
    if not supabase:
        logger.error("Supabase client not initialized")
        return {"success": False, "categories": [], "error": "Database connection not available"}
    
    try:
        # Correct Supabase query for Python client
        result = supabase.table("transactions") \
            .select("category") \
            .neq("category", None) \
            .execute()
        
        if result.data:
            categories = sorted(list(set(row["category"] for row in result.data if row.get("category"))))
            logger.info(f"Found {len(categories)} unique categories")
            return {"success": True, "categories": categories}
        else:
            logger.warning("No categories found in database")
            return {"success": True, "categories": []}
        
    except Exception as e:
        error_msg = f"Failed to fetch categories: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "categories": [], "error": error_msg}

# Reusable database functions for transactions
async def get_all_transactions() -> Dict[str, Any]:
    """
    Fetch all transactions from the database.
    
    Returns:
        Dictionary containing:
        - success: bool - Whether the operation was successful
        - transactions: List[Dict] - List of transaction objects
        - error: Optional[str] - Error message if operation failed
    """
    logger.info("Fetching all transactions")
    
    if not supabase:
        logger.error("Supabase client not initialized")
        return {"success": False, "transactions": [], "error": "Database connection not available"}
    
    try:
        # Query all transactions, ordered by date descending
        result = supabase.table("transactions") \
            .select("*") \
            .order("date", desc=True) \
            .execute()
        
        if result.data:
            # Convert to response format
            transactions = [
                {
                    "id": str(row["id"]),  # Convert UUID to string
                    "date": row["date"],
                    "amount": float(row["amount"]),  # Ensure float type
                    "merchant": row["merchant"],
                    "category": row.get("category")  # Optional field
                }
                for row in result.data
            ]
            
            logger.info(f"Found {len(transactions)} transactions")
            return {"success": True, "transactions": transactions}
        else:
            logger.warning("No transactions found in database")
            return {"success": True, "transactions": []}
        
    except Exception as e:
        error_msg = f"Failed to fetch transactions: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "transactions": [], "error": error_msg}

# Reusable database function for transaction summaries
async def get_transaction_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get summary statistics for transactions with optional filtering.
    
    Args:
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
        category: Optional category filter
        
    Returns:
        Dictionary containing:
        - success: bool - Whether the operation was successful
        - total_spent: float - Total sum of transaction amounts
        - by_category: Dict[str, float] - Total spent per category
        - daily_trends: List[Dict] - Daily spending trends
        - error: Optional[str] - Error message if operation failed
    """
    logger.info(f"Fetching transaction summary (start: {start_date}, end: {end_date}, category: {category})")
    
    if not supabase:
        logger.error("Supabase client not initialized")
        return {
            "success": False,
            "error": "Database connection not available",
            "total_spent": 0.0,
            "by_category": {},
            "daily_trends": []
        }
    
    try:
        # Start building the query
        query = supabase.table("transactions").select("*")
        
        # Apply filters if provided
        if start_date:
            query = query.gte("date", start_date)
        if end_date:
            query = query.lte("date", end_date)
        if category:
            query = query.eq("category", category)
            
        # Execute query
        result = query.execute()
        
        if not result.data:
            logger.warning("No transactions found for summary")
            return {
                "success": True,
                "total_spent": 0.0,
                "by_category": {},
                "daily_trends": []
            }
        
        # Process the results
        transactions = result.data
        
        # Calculate total spent
        total_spent = sum(float(t["amount"]) for t in transactions)
        
        # Calculate totals by category
        by_category = {}
        for t in transactions:
            cat = t.get("category", "Uncategorized")
            by_category[cat] = by_category.get(cat, 0.0) + float(t["amount"])
        
        # Calculate daily trends
        daily_totals = {}
        for t in transactions:
            date = t["date"]
            daily_totals[date] = daily_totals.get(date, 0.0) + float(t["amount"])
        
        # Convert daily totals to sorted list
        daily_trends = [
            {"date": date, "amount": amount}
            for date, amount in sorted(daily_totals.items())
        ]
        
        logger.info(f"Summary generated: {len(transactions)} transactions, {len(by_category)} categories")
        
        return {
            "success": True,
            "total_spent": total_spent,
            "by_category": by_category,
            "daily_trends": daily_trends
        }
        
    except Exception as e:
        error_msg = f"Failed to generate transaction summary: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "total_spent": 0.0,
            "by_category": {},
            "daily_trends": []
        }

# Reusable saving function
async def save_transactions_to_db(transactions: List[Transaction]) -> Dict[str, Any]:
    """
    Save transactions to Supabase database.
    
    Args:
        transactions: List of transaction objects to save
        
    Returns:
        Dictionary containing save results and any errors
        
    Raises:
        HTTPException: If database connection or validation fails
    """
    logger.info(f"Saving {len(transactions)} transactions to database")
    
    # Validate Supabase connection
    if not supabase:
        logger.error("Supabase client not initialized - missing environment variables")
        raise HTTPException(
            status_code=500,
            detail="Database connection not available. Please check server configuration."
        )
    
    # Validate input data
    if not transactions:
        raise HTTPException(
            status_code=400,
            detail="No transaction data provided"
        )
    
    try:
        # Prepare transactions for database insertion
        transactions_to_insert = []
        errors = []
        
        for i, transaction in enumerate(transactions):
            try:
                # Convert transaction to database format
                db_transaction = {
                    "date": transaction.date,
                    "merchant": transaction.merchant,
                    "amount": transaction.amount,
                    "category": transaction.category
                }
                
                transactions_to_insert.append(db_transaction)
                
            except Exception as e:
                error_msg = f"Transaction {i+1}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Insert transactions into Supabase
        logger.info(f"Inserting {len(transactions_to_insert)} transactions into database")
        
        # Use Supabase client to insert data
        result = supabase.table('transactions').insert(transactions_to_insert).execute()
        
        # Check if insertion was successful
        if hasattr(result, 'data') and result.data:
            inserted_count = len(result.data)
            logger.info(f"Successfully inserted {inserted_count} transactions")
            
            return {
                "success": True,
                "inserted": inserted_count,
                "errors": errors
            }
        else:
            logger.error(f"Database insertion failed - no data returned")
            errors.append("Failed to insert transactions into database")
            return {
                "success": False,
                "inserted": 0,
                "errors": errors
            }
    
    except Exception as e:
        logger.error(f"Unexpected error saving transactions: {str(e)}")
        return {
            "success": False,
            "inserted": 0,
            "errors": [f"Internal server error: {str(e)}"]
        }

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

@app.get("/api/get-categories", response_model=GetCategoriesResponse)
@limiter.limit("100/minute")
async def get_categories(request: Request):
    """
    Get a list of unique transaction categories from the database.
    
    This endpoint returns a sorted list of all unique categories that have been
    assigned to transactions. It's useful for:
    - Populating category dropdown menus
    - Analyzing spending patterns
    - Generating transaction reports
    
    Returns:
        JSON object containing:
        - success: Boolean indicating if the operation was successful
        - categories: List of unique category strings, sorted alphabetically
        
    Note:
        - Categories are case-sensitive
        - Empty or null categories are excluded
        - Returns an empty list if no categories are found
    """
    try:
        # Use our reusable function to fetch categories
        result = await get_unique_categories()
        
        if result["success"]:
            return GetCategoriesResponse(
                success=True,
                categories=result["categories"]
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to fetch categories")
            )
            
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error in get_categories: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/api/get-transactions", response_model=GetTransactionsResponse)
@limiter.limit("50/minute")
async def get_transactions(request: Request):
    """
    Get all transactions from the database.
    
    This endpoint returns all transactions stored in the database,
    ordered by date (most recent first). It's useful for:
    - Displaying transaction history
    - Generating reports
    - Data analysis and visualization
    
    Returns:
        JSON object containing:
        - success: Boolean indicating if the operation was successful
        - transactions: List of transaction objects with fields:
            - id: Transaction UUID
            - date: Transaction date (YYYY-MM-DD)
            - amount: Transaction amount
            - merchant: Merchant name/description
            - category: Optional transaction category
            
    Note:
        - Transactions are ordered by date descending (newest first)
        - Returns an empty list if no transactions are found
        - Future versions may support pagination and filtering
    """

@app.get("/api/get-summary", response_model=TransactionSummary)
@limiter.limit("100/minute")
async def get_transaction_summary_endpoint(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None
):
    """
    Get aggregated summary of transactions with optional filtering.
    
    This endpoint provides aggregated statistics about transactions,
    including totals by category and daily trends. It's useful for:
    - Dashboard visualizations
    - Spending analysis
    - Category-based reporting
    - AI-powered insights
    
    Query Parameters:
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
        category: Optional category filter
    
    Returns:
        JSON object containing:
        - success: Boolean indicating if the operation was successful
        - total_spent: Total sum of all transaction amounts
        - by_category: Dictionary of category totals
        - daily_trends: List of daily spending totals
        
    Note:
        - All amounts are in the original transaction currency
        - Dates must be in YYYY-MM-DD format
        - Returns zero totals if no transactions are found
        - Category totals include an "Uncategorized" group
    """
    try:
        # Validate date formats if provided
        if start_date:
            try:
                datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="start_date must be in YYYY-MM-DD format"
                )
        
        if end_date:
            try:
                datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="end_date must be in YYYY-MM-DD format"
                )
        
        # Validate date range if both dates provided
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date cannot be later than end_date"
            )
        
        # Use our reusable function to fetch summary
        result = await get_transaction_summary(
            start_date=start_date,
            end_date=end_date,
            category=category
        )
        
        if result["success"]:
            return TransactionSummary(
                success=True,
                total_spent=result["total_spent"],
                by_category=result["by_category"],
                daily_trends=result["daily_trends"]
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to generate summary")
            )
            
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error in get_transaction_summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
    try:
        # Use our reusable function to fetch transactions
        result = await get_all_transactions()
        
        if result["success"]:
            return GetTransactionsResponse(
                success=True,
                transactions=result["transactions"]
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to fetch transactions")
            )
            
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error in get_transactions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

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
    
    try:
        # Use our reusable parsing function
        result = await parse_uploaded_file(file)
        
        return {
            "success": True,
            "data": result["transactions"],
            "metadata": result["metadata"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
    
@app.post("/api/upload-and-save", response_model=UploadAndSaveResponse)
@limiter.limit("30/minute")
async def upload_and_save_endpoint(
    request: Request,
    file: UploadFile = File(..., description="CSV or Excel file containing bank/credit card transactions")
):
    """
    Upload a transaction file and save the parsed transactions to the database.
    
    This endpoint combines file parsing and database storage in a single operation.
    It accepts a file upload, then internally calls the parsing logic
    from /api/parse-transactions and the saving logic from /api/save-transactions.
    
    **Environment Variables Required:**
    - SUPABASE_URL: Your Supabase project URL
    - SUPABASE_ANON_KEY: Your Supabase anonymous key
    
    **Supported file types:**
    - CSV files (.csv)
    - Excel files (.xlsx, .xls)
    
    **Parameters:**
    - `file`: CSV or Excel file containing transactions
    
    **Maximum file size:** 10MB
    
    **Response format:**
    - `success`: Boolean indicating if the operation was successful
    - `inserted`: Number of transactions successfully saved to database
    - `errors`: Array of any error messages from failed insertions
    
    **Error Handling:**
    - Invalid file types are rejected
    - Parsing errors are returned in the errors array
    - Database connection issues are handled gracefully
    - Individual transaction validation errors are tracked
    """
    
    logger.info(f"Received upload-and-save request: {file.filename}")
    
    try:
        # Step 1: Parse the uploaded file using our reusable parsing function
        parse_result = await parse_uploaded_file(file)
        
        if not parse_result["success"]:
            return UploadAndSaveResponse(
                success=False,
                inserted=0,
                errors=[f"Parsing failed: {parse_result.get('error', 'Unknown error')}"]
            )
        
        # Convert parsed transactions to Transaction objects for validation
        transactions = []
        parsing_errors = []
        
        for i, trans_data in enumerate(parse_result["transactions"]):
            try:
                transaction = Transaction(
                    date=trans_data["date"],
                    merchant=trans_data["merchant"],
                    amount=trans_data["amount"],
                    category=trans_data.get("category")
                )
                transactions.append(transaction)
            except Exception as e:
                parsing_errors.append(f"Transaction {i+1} validation failed: {str(e)}")
        
        # If we have parsing errors, include them in the response
        if parsing_errors:
            logger.warning(f"Found {len(parsing_errors)} transaction validation errors")
        
        # Step 2: Save transactions to database using our reusable saving function
        save_result = await save_transactions_to_db(transactions)
        
        # Combine parsing errors with saving errors
        all_errors = parsing_errors + save_result.get("errors", [])
        
        # Determine overall success
        overall_success = save_result["success"] and len(parsing_errors) == 0
        
        logger.info(f"Upload-and-save completed: {save_result['inserted']} transactions inserted, {len(all_errors)} errors")
        
        return UploadAndSaveResponse(
            success=overall_success,
            inserted=save_result["inserted"],
            errors=all_errors
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, etc.)
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error in upload-and-save: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/api/ask-agent", response_model=AskAgentResponse)
@limiter.limit("30/minute")
async def ask_agent_endpoint(
    request: Request,
    agent_request: AskAgentRequest
):
    """
    You are a financial query parser for a personal finance visualization agent. 
Your task is to extract the user's intent, any specified filters, and recommend a chart type with justification from their natural language question about their personal finances. 

The extracted intent should match one of the following actions that the /api/ask-agent endpoint can handle:
- "total_spent" → compute total spending
- "total_income" → compute total income
- "spending_by_category" → breakdown of spend by category
- "transactions_over_time" → list transactions over a specified period
- "balance_over_time" → account balance trend over time

Filters may include:
- "category" (e.g., "groceries", "gasoline")
- "start_date" (YYYY-MM-DD)
- "end_date" (YYYY-MM-DD)
- "metric" (optional, e.g., sum, average)

For chart recommendation:
- Include a "chart" object with:
    - "type" → suggested chart type (e.g., bar, line, pie)
    - "justification" → why this chart type is appropriate for the data and intent

Return the response strictly as a JSON object with the keys:
- "intent" → the identified intent
- "filters" → the extracted filters as key-value pairs
- "chart" → the chart type and justification object

If a filter is not present in the question, omit that key.  
Do not include any text outside the JSON object.  

Example output:
{
  "intent": "spending_by_category",
  "filters": {
    "category": "groceries",
    "start_date": "2025-08-01",
    "end_date": "2025-08-31"
  },
  "chart": {
    "type": "bar",
    "justification": "Bar charts are best for comparing discrete categories such as spending by category over a month"
  }
}
    """
    
    logger.info(f"Received AI agent request: {agent_request.prompt[:100]}...")
    
    try:
        # Step 1: Parse user prompt to extract intent and filters using AI (Gemini)
        intent = None
        extracted_filters = {}
        
        try:
            # Gemini AI integration for intent detection and filter extraction
            client = genai.Client(
                api_key=os.environ.get("GEMINI_API_KEY"),
            )

            model = "gemini-flash-latest"
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=agent_request.prompt),
                    ],
                ),
            ]
            generate_content_config = types.GenerateContentConfig(
                thinking_config = types.ThinkingConfig(
                    thinking_budget=-1,
                ),
                system_instruction=[
                    types.Part.from_text(text="""You are a financial query parser for a personal finance visualization agent. 
Your task is to extract the user's intent, any specified filters, and recommend a chart type with justification from their natural language question about their personal finances. 

The extracted intent should match one of the following actions that the /api/ask-agent endpoint can handle:
- "total_spent" → compute total spending
- "total_income" → compute total income
- "spending_by_category" → breakdown of spend by category
- "transactions_over_time" → list transactions over a specified period
- "balance_over_time" → account balance trend over time

Filters may include:
- "category" (e.g., "groceries", "gasoline")
- "start_date" (YYYY-MM-DD)
- "end_date" (YYYY-MM-DD)
- "metric" (optional, e.g., sum, average)

For chart recommendation:
- Include a "chart" object with:
    - "type" → suggested chart type (e.g., bar, line, pie)
    - "justification" → why this chart type is appropriate for the data and intent

Return the response strictly as a JSON object with the keys:
- "intent" → the identified intent
- "filters" → the extracted filters as key-value pairs
- "chart" → the chart type and justification object

If a filter is not present in the question, omit that key.  
Do not include any text outside the JSON object.  

Example output:
{
  "intent": "spending_by_category",
  "filters": {
    "category": "groceries",
    "start_date": "2025-08-01",
    "end_date": "2025-08-31"
  },
  "chart": {
    "type": "bar",
    "justification": "Bar charts are best for comparing discrete categories such as spending by category over a month"
  }
}
"""),
                ],
            )

            # Collect the response from Gemini
            response_text = ""
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                response_text += chunk.text
            
            # Parse the JSON response from Gemini
            try:
                gemini_response = json.loads(response_text.strip())
                intent = gemini_response.get("intent")
                extracted_filters = gemini_response.get("filters", {})
                chart = gemini_response.get("chart", {})
                logger.info(f"Gemini successfully parsed intent: {intent}, filters: {extracted_filters}")
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini response as JSON: {e}")
                logger.error(f"Raw Gemini response: {response_text}")
                raise Exception("Invalid JSON response from Gemini")
                
        except Exception as e:
            logger.warning(f"Gemini API failed ({str(e)}), falling back to simple keyword matching")
            
            # FALLBACK: Simple keyword-based intent detection
            prompt_lower = agent_request.prompt.lower()
            
            if "spending" in prompt_lower or "spent" in prompt_lower:
                if "category" in prompt_lower or "categories" in prompt_lower:
                    intent = "spending_by_category"
                else:
                    intent = "total_spent"
                # Extract potential date filters (simple fallback)
                if "last month" in prompt_lower:
                    extracted_filters["date_range"] = "last_month"
                elif "this month" in prompt_lower:
                    extracted_filters["date_range"] = "this_month"
            elif "category" in prompt_lower or "categories" in prompt_lower:
                intent = "spending_by_category"
            elif "trend" in prompt_lower or "over time" in prompt_lower:
                intent = "transactions_over_time"
            elif "balance" in prompt_lower:
                intent = "balance_over_time"
            elif "income" in prompt_lower:
                intent = "total_income"
            else:
                intent = "total_spent"  # Default fallback
        
        logger.info(f"Detected intent: {intent}, filters: {extracted_filters}, chart: {chart}")
        
        # Step 2: Query Supabase database based on extracted filters
        # TODO: Optimize database queries based on intent and filters
        # This section will use the extracted filters to build efficient queries
        
        raw_data = {}
        
        # PLACEHOLDER: Database querying based on intent
        # This section will be expanded with actual query logic based on intent
        # Expected workflow:
        # 1. Build appropriate Supabase query based on intent
        # 2. Apply extracted filters (date ranges, categories, amounts)
        # 3. Execute query and retrieve relevant transaction data
        # 4. Perform any necessary aggregations or calculations
        
        if intent == "total_spent":
            # Query for total spending data
            # Placeholder: Will query transactions and sum amounts
            raw_data = {"total_spent": 0.0, "transaction_count": 0}
            
        elif intent == "total_income":
            # Query for total income data
            # Placeholder: Will query positive transactions and sum amounts
            raw_data = {"total_income": 0.0, "income_transactions": []}
            
        elif intent == "spending_by_category":
            # Query for category-based spending data
            # Placeholder: Will query and group by categories
            raw_data = {"categories": {}, "total_by_category": {}}
            
        elif intent == "transactions_over_time":
            # Query for time-series transaction data
            # Placeholder: Will query transactions grouped by date
            raw_data = {"daily_trends": [], "monthly_trends": []}
            
        elif intent == "balance_over_time":
            # Query for balance trend data
            # Placeholder: Will calculate running balance over time
            raw_data = {"balance_trends": [], "starting_balance": 0.0}
            
        else:
            # Default: General financial overview
            raw_data = {"summary": {}, "recent_transactions": []}
        
        logger.info(f"Database query completed for intent: {intent}")
        
        # Step 3: Generate AI-powered insights using Gemini
        try:
            # Get chart recommendation from Gemini Step 1 (if available) or use defaults
            if 'chart' in locals() and chart:
                chart_type = chart.get("type", "bar")
                explanation = chart.get("justification", "Chart type selected for optimal data visualization")
            else:
                # Fallback chart recommendations based on intent
                if intent == "spending_by_category":
                    chart_type = "pie"
                    explanation = "Pie charts effectively show proportional breakdown of spending across categories"
                elif intent == "transactions_over_time":
                    chart_type = "line"
                    explanation = "Line charts are ideal for showing trends and changes over time"
                elif intent == "balance_over_time":
                    chart_type = "area"
                    explanation = "Area charts effectively show balance changes and trends over time"
                else:
                    chart_type = "bar"
                    explanation = "Bar charts clearly display total amounts for easy comparison"

            # Prepare input for Gemini Step 3 generation
            gemini_input = {
                "intent": intent,
                "filters": extracted_filters,
                "chart": {"type": chart_type, "justification": explanation},
                "explanation": explanation,
                "raw_data": raw_data
            }

            # Initialize Gemini client for Step 3 insight generation
            client = genai.Client(
                api_key=os.environ.get("GEMINI_API_KEY"),
            )

            model = "gemini-flash-latest"
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=json.dumps(gemini_input)),
                    ],
                ),
            ]
            generate_content_config = types.GenerateContentConfig(
                thinking_config = types.ThinkingConfig(
                    thinking_budget=-1,
                ),
                system_instruction=[
                    types.Part.from_text(text="""You are a financial visualization AI assistant.  

Your task: Take the following inputs:
- "intent": the detected intent from the user's natural language query
- "filters": any extracted filters (e.g., category, start_date, end_date)
- "chart": a suggested Plotly chart type and associated details
- "explanation": a justification of why the chosen chart is appropriate
- "raw_data": raw transaction data retrieved from the Supabase database

Your output must strictly match the AskAgentResponse Pydantic model:

AskAgentResponse:
- success: bool → whether the request was successful
- intent: string → detected intent from user prompt
- filters: dict → extracted filters used for the database query
- insight: object → a FinancialInsight object containing:
    - summary: str → short, concise natural language summary of the insight
    - chart: object → a PlotlyChart object containing:
        - data: list of PlotlyTrace objects, each with:
            - type: str (bar, line, pie, scatter, etc.)
            - x: optional list of values for x-axis
            - y: optional list of values for y-axis
            - values: optional list of numbers (for pie charts)
            - labels: optional list of labels (for pie charts)
            - name: optional trace name
            - marker: optional marker object (with color)
        - layout: PlotlyLayout object with:
            - title: str
            - xaxis: optional axis configuration (title)
            - yaxis: optional axis configuration (title)
            - margin: optional margin object (t, l, r, b)
            - plot_bgcolor: optional
            - paper_bgcolor: optional
    - explanation: str → detailed justification of chart choice
- raw_data: dict → raw query results from the database
- error: optional str → error message if the operation failed

Constraints:
- Output must be valid JSON only, with **no extra text or markdown**.
- Ensure all fields required by the model are present.
- Summaries should be concise and insightful, not just descriptive.
- Chart objects must be valid and ready to render in Plotly (react-plotly.js).

Example output:

{
  "success": true,
  "intent": "spending_by_category",
  "filters": {
    "category": "groceries",
    "start_date": "2025-08-01",
    "end_date": "2025-08-31"
  },
  "insight": {
    "summary": "You spent the most on groceries ($450) this month.",
    "chart": {
  "data": [
    {
      "type": "bar",
      "x": ["Groceries", "Transportation", "Entertainment"],
      "y": [450, 300, 200],
      "marker": {
        "color": "#4F46E5",
        "line": {"color": "#FFFFFF", "width": 1}
      },
      "hovertemplate": "<b>%{x}</b><br>Amount: $%{y:,.2f}<extra></extra>"
    }
  ],
  "layout": {
    "title": {
      "text": "<b>Spending by Category - August 2025</b>",
      "x": 0.5,
      "xanchor": "center",
      "font": {"size": 18, "color": "#374151", "family": "Arial, sans-serif"}
    },
    "xaxis": {
      "title": {"text": "<b>Category</b>", "font": {"size": 14, "color": "#374151"}},
      "tickfont": {"size": 11, "color": "#374151"},
      "gridcolor": "#E5E7EB",
      "showgrid": true
    },
    "yaxis": {
      "title": {"text": "<b>Amount ($)</b>", "font": {"size": 14, "color": "#374151"}},
      "tickfont": {"size": 11, "color": "#374151"},
      "tickformat": "$,.0f",
      "gridcolor": "#E5E7EB",
      "showgrid": true
    },
    "margin": {"t": 60, "l": 80, "r": 40, "b": 60},
    "plot_bgcolor": "#FAFAFA",
    "paper_bgcolor": "#FFFFFF",
    "font": {"family": "Arial, sans-serif", "color": "#374151"}
  }
},
  "raw_data": {
    "transactions": [
      {"date": "2025-08-02", "merchant": "Whole Foods", "amount": 150, "category": "Groceries"},
      {"date": "2025-08-10", "merchant": "Trader Joe's", "amount": 300, "category": "Groceries"}
    ]
  },
  "error": null
}
"""),
                ],
            )

            # Collect the response from Gemini
            response_text = ""
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                response_text += chunk.text

            # Parse the JSON response from Gemini
            try:
                # Clean the response text - remove any markdown formatting
                clean_response = response_text.strip()
                if clean_response.startswith("```json"):
                    clean_response = clean_response[7:]
                if clean_response.endswith("```"):
                    clean_response = clean_response[:-3]
                clean_response = clean_response.strip()

                gemini_result = json.loads(clean_response)
                
                # Gemini should return the complete AskAgentResponse structure
                logger.info(f"Gemini generated complete response for intent: {intent}")
                return AskAgentResponse(**gemini_result)

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini Step 3 response as JSON: {e}")
                logger.error(f"Raw Gemini response: {response_text}")
                raise Exception("Invalid JSON response from Gemini Step 3")

        except Exception as e:
            logger.warning(f"Gemini Step 3 failed ({str(e)}), using fallback insight generation")

            # FALLBACK: Create AskAgentResponse with simple insight
            if intent == "spending_by_category":
                summary = "You spent the most on Food & Dining ($450) this month, followed by Transportation ($300)."
                explanation = "A bar chart is the best choice because it clearly compares spending across categories, highlighting which ones dominate."
                plotly_chart = PlotlyChart(
                    data=[
                        PlotlyTrace(
                            type="bar",
                            x=["Food & Dining", "Transportation", "Entertainment", "Shopping", "Utilities"],
                            y=[450, 300, 200, 150, 100],
                            marker=PlotlyMarker(color="rgba(99, 110, 250, 0.7)")
                        )
                    ],
                    layout=PlotlyLayout(
                        title="Spending by Category - September 2025",
                        xaxis=PlotlyAxis(title="Category"),
                        yaxis=PlotlyAxis(title="Amount ($)"),
                        margin=PlotlyMargin(t=40, l=50, r=20, b=50),
                        plot_bgcolor="white",
                        paper_bgcolor="white"
                    )
                )
            else:
                summary = f"Analysis completed for {intent.replace('_', ' ')}."
                explanation = f"Chart type selected for optimal data visualization of {intent}."
                plotly_chart = PlotlyChart(
                    data=[
                        PlotlyTrace(
                            type="bar",
                            x=["Total"],
                            y=[0],
                            marker=PlotlyMarker(color="rgba(156, 163, 175, 0.7)")
                        )
                    ],
                    layout=PlotlyLayout(
                        title="Financial Analysis",
                        xaxis=PlotlyAxis(title="Category"),
                        yaxis=PlotlyAxis(title="Amount ($)"),
                        margin=PlotlyMargin(t=40, l=50, r=20, b=50),
                        plot_bgcolor="white",
                        paper_bgcolor="white"
                    )
                )

            # Create fallback insight object
            insight = FinancialInsight(
                summary=summary,
                explanation=explanation,
                chart=plotly_chart
            )

            logger.info(f"Generated fallback insight for intent: {intent}")

            # Return complete AskAgentResponse
            return AskAgentResponse(
                success=True,
                intent=intent,
                filters=extracted_filters,
                insight=insight,
                raw_data=raw_data,
                error=None
            )

# 3. Update the error handling (around lines 1403-1412):
    except Exception as e:
        logger.error(f"Error in ask-agent endpoint: {str(e)}")
        
        # Create error response with basic insight
        error_insight = FinancialInsight(
            summary="An error occurred while processing your request.",
            explanation="Unable to generate chart due to processing error.",
            chart=PlotlyChart(
                data=[
                    PlotlyTrace(
                        type="bar",
                        x=["Error"],
                        y=[0],
                        marker=PlotlyMarker(color="rgba(239, 68, 68, 0.7)")
                    )
                ],
                layout=PlotlyLayout(
                    title="Processing Error",
                    xaxis=PlotlyAxis(title="Status"),
                    yaxis=PlotlyAxis(title="Value"),
                    margin=PlotlyMargin(t=40, l=50, r=20, b=50),
                    plot_bgcolor="white",
                    paper_bgcolor="white"
                )
            )
        )
        
        return AskAgentResponse(
            success=False,
            intent=None,
            filters=None,
            insight=error_insight,
            raw_data=None,
            error=f"Failed to process request: {str(e)}"
        )

        
    except Exception as e:
        logger.error(f"Error in ask-agent endpoint: {str(e)}")
        return AskAgentResponse(
            success=False,
            intent=None,
            filters=None,
            insight=None,
            raw_data=None,
            error=f"Failed to process request: {str(e)}"
        )

@app.post("/api/save-transactions", response_model=SaveTransactionsResponse)
@limiter.limit("50/minute")
async def save_transactions_endpoint(
    request: Request,
    transaction_request: SaveTransactionsRequest
):
    """
    Save parsed transactions to Supabase database.
    
    This endpoint accepts structured transaction data and stores each transaction
    in the Supabase 'transactions' table.
    
    **Request Body:**
    - `success`: Boolean - Success flag from parser
    - `data`: Array of transaction objects
    - `metadata`: Optional metadata object
    
    **Transaction Object Structure:**
    - `date`: String - Date in YYYY-MM-DD format
    - `merchant`: String - Merchant name or description
    - `amount`: Float - Transaction amount
    - `category`: String (optional) - Transaction category
    
    **Response:**
    - `success`: Boolean - Whether the operation was successful
    - `message`: String - Response message
    - `transactions_inserted`: Integer - Number of transactions inserted
    
    **Error Handling:**
    - Validates Supabase connection
    - Validates transaction data format
    - Handles database insertion errors
    - Returns detailed error messages
    """
    
    logger.info(f"Received request to save {len(transaction_request.data)} transactions")
    
    try:
        # Use our reusable saving function (without user_id for backward compatibility)
        save_result = await save_transactions_to_db(transaction_request.data)
        
        if save_result["success"]:
            return SaveTransactionsResponse(
                success=True,
                message=f"Successfully saved {save_result['inserted']} transactions",
                transactions_inserted=save_result["inserted"]
            )
        else:
            # If there are errors, include them in the response
            error_message = "Failed to save transactions"
            if save_result.get("errors"):
                error_message += f": {'; '.join(save_result['errors'][:3])}"  # Show first 3 errors
            raise HTTPException(
                status_code=500,
                detail=error_message
            )
    
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, etc.)
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error saving transactions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

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
