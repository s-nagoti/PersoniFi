"""
Simplified FastAPI server for testing - without the complex parser import
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile
import json

# Initialize FastAPI app
app = FastAPI(
    title="PersoniFi Backend API (Simple)",
    description="Simplified version for testing",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "PersoniFi FastAPI is running!"}

@app.get("/api/health")
async def health_check():
    return {
        "success": True,
        "message": "PersoniFi Backend is running (simple version)",
        "timestamp": "2025-01-27T00:00:00Z"
    }

@app.post("/api/parse-transactions")
async def parse_transactions_simple(file: UploadFile = File(...)):
    """Simplified version that just returns file info"""
    
    # Basic validation
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ['.csv', '.xlsx', '.xls']:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Only CSV and Excel files allowed."
        )
    
    # Read file content
    content = await file.read()
    
    return {
        "success": True,
        "message": "File received successfully",
        "file_info": {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content),
            "extension": file_ext
        },
        "data": [
            {
                "date": "2025-01-27",
                "merchant": "TEST MERCHANT",
                "amount": 123.45,
                "category": "Test"
            }
        ],
        "metadata": {
            "total_transactions": 1,
            "file_type": file_ext[1:],
            "processing_note": "This is a test response - full parsing not implemented yet"
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Simple FastAPI Server...")
    print("🌐 Server: http://localhost:3000")
    print("📚 Docs: http://localhost:3000/docs")
    uvicorn.run("main_simple:app", host="0.0.0.0", port=3000, reload=True)
