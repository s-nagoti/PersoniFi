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
import os
import tempfile
import shutil
from datetime import datetime
from typing import List, Optional, Dict, Any
import uvicorn
import logging

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
