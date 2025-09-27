# PersoniFi Backend

A modern FastAPI backend service for parsing bank and credit card statements from CSV and Excel files. The service extracts transaction data and returns it in a structured JSON format for visualization and AI analysis.

## Features

- 📁 **File Upload**: Accepts CSV and Excel (.xlsx, .xls) files via HTTP POST
- 🔍 **Smart Parsing**: Automatically detects column mappings for common bank statement formats
- 📊 **Structured Output**: Returns transactions in standardized JSON format
- 🛡️ **Error Handling**: Comprehensive validation and error handling
- 🔒 **Security**: Rate limiting, file type validation, and CORS protection
- 🐍 **Pure Python**: FastAPI + Pandas for robust file parsing
- 📚 **Auto Documentation**: Built-in Swagger UI and ReDoc

## Tech Stack

- **Backend**: FastAPI (Python)
- **File Parsing**: Pandas + Python
- **Security**: SlowAPI Rate Limiting, CORS
- **File Upload**: FastAPI native multipart support
- **Server**: Uvicorn ASGI server

## Quick Start

### Prerequisites

- Python (v3.8 or higher)
- pip package manager

### Installation

1. **Clone and setup the project:**
   ```bash
   git clone <your-repo>
   cd PersoniFi
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r python/requirements.txt
   ```

3. **Start the server:**
   ```bash
   python start_server.py
   # or directly:
   python main.py
   # or with uvicorn:
   uvicorn main:app --reload --host 0.0.0.0 --port 3000
   ```

The server will start on `http://localhost:3000`

### API Documentation

Once the server is running, you can access:
- **Swagger UI**: http://localhost:3000/docs
- **ReDoc**: http://localhost:3000/redoc
- **OpenAPI JSON**: http://localhost:3000/openapi.json

## API Endpoints

### POST `/api/parse-transactions`

Upload and parse a bank/credit card statement file.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: File upload with field name `file`

**Supported Files:**
- CSV files (.csv)
- Excel files (.xlsx, .xls)
- Maximum file size: 10MB

**Response Format:**
```json
{
  "success": true,
  "data": [
    {
      "date": "2023-12-25",
      "merchant": "AMAZON.COM",
      "amount": -45.99,
      "category": "Shopping" // optional
    }
  ],
  "metadata": {
    "total_transactions": 150,
    "file_type": "csv",
    "column_mapping": {
      "date": "Transaction Date",
      "amount": "Amount",
      "merchant": "Description"
    },
    "original_filename": "bank_statement.csv",
    "file_size": 2048576
  }
}
```

### GET `/api/formats`

Get information about supported file formats and required columns.

**Response:**
```json
{
  "success": true,
  "supported_formats": {
    "csv": {
      "extensions": [".csv"],
      "mime_types": ["text/csv", "application/csv"],
      "max_size": "10MB"
    },
    "excel": {
      "extensions": [".xlsx", ".xls"],
      "mime_types": ["application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
      "max_size": "10MB"
    }
  },
  "required_columns": ["date", "amount", "merchant/description"],
  "optional_columns": ["category"]
}
```

### GET `/api/health`

Health check endpoint.

## File Format Requirements

### Required Columns

The parser automatically detects columns with these keywords:

- **Date**: `date`, `transaction date`, `posted date`, `trans date`, `payment date`
- **Amount**: `amount`, `transaction amount`, `debit`, `credit`, `posted amount`
- **Merchant**: `description`, `merchant`, `transaction description`, `payee`, `memo`

### Optional Columns

- **Category**: `category`, `transaction category`, `type`, `transaction type`

### Supported Date Formats

- YYYY-MM-DD (2023-12-25)
- MM/DD/YYYY (12/25/2023)
- DD/MM/YYYY (25/12/2023)
- MM-DD-YYYY (12-25-2023)
- And many more common formats

### Amount Formats

- Positive amounts: 123.45, $123.45
- Negative amounts: -123.45, (123.45)
- Currency symbols are automatically stripped

## Error Handling

The service handles various error scenarios:

- **File Type Validation**: Only CSV and Excel files accepted
- **File Size Limits**: Maximum 10MB per file
- **Missing Columns**: Clear error messages for missing required columns
- **Invalid Data**: Skips invalid rows and reports errors
- **Encoding Issues**: Tries multiple encodings for CSV files
- **Rate Limiting**: Prevents abuse with request rate limiting

## Example Usage

### Using curl:
```bash
curl -X POST \
  http://localhost:3000/api/parse-transactions \
  -F "file=@/path/to/your/statement.csv"
```

### Using JavaScript (fetch):
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:3000/api/parse-transactions', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log('Parsed transactions:', data.data);
  } else {
    console.error('Error:', data.error);
  }
});
```

## Development

### Project Structure
```
PersoniFi/
├── main.py                # FastAPI server
├── start_server.py        # Server startup script
├── python/
│   ├── transaction_parser.py  # Python parsing script
│   └── requirements.txt       # Python dependencies
├── test_save_transactions.py  # Test script for save endpoint
├── env.example            # Environment variables template
├── .env                   # Your environment variables (create this)
├── uploads/               # Temporary file storage (auto-created)
└── README.md
```

### Environment Variables

- `PORT`: Server port (default: 3000)
- `FRONTEND_URL`: CORS origin for frontend (default: http://localhost:3001)

### Database Setup (Supabase)

1. **Create a Supabase project** at [supabase.com](https://supabase.com)

2. **Create the transactions table** in your Supabase SQL editor:
```sql
CREATE TABLE transactions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT,
    date DATE NOT NULL,
    merchant TEXT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    category TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create an index for better query performance
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_date ON transactions(date);
```

**Note:** 
- `user_id` is nullable since we support anonymous transactions
- `created_at` is auto-generated by Supabase (don't insert manually)
- `id` is auto-generated UUID primary key

3. **Set environment variables**:
```bash
# Copy the example environment file
cp env.example .env

# Edit the .env file with your actual Supabase credentials
# SUPABASE_URL=https://your-project-id.supabase.co
# SUPABASE_ANON_KEY=your_supabase_anon_key_here
```

**Get your Supabase credentials:**
1. Go to your Supabase project dashboard
2. Navigate to Settings → API
3. Copy the "Project URL" and "anon/public" key
4. Paste them into your `.env` file

### API Endpoints

#### 1. Parse Transactions
Upload and parse bank/credit card statements:

```bash
curl -X POST \
  http://localhost:3000/api/parse-transactions \
  -F "file=@your_statement.csv"
```

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "date": "2025-01-15",
            "merchant": "AMAZON.COM",
            "amount": 45.99,
            "category": "Shopping"
        }
    ],
    "metadata": {
        "total_transactions": 1,
        "file_type": "csv"
    }
}
```

#### 2. Save Transactions (NEW)
Save parsed transactions to Supabase database. User ID is optional for anonymous transactions:

**With User ID:**
```bash
curl -X POST \
  http://localhost:3000/api/save-transactions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "success": true,
    "data": [
        {
            "date": "2025-01-15",
            "merchant": "AMAZON.COM",
            "amount": 45.99,
            "category": "Shopping"
        }
    ]
  }'
```

**Without User ID (Anonymous):**
```bash
curl -X POST \
  http://localhost:3000/api/save-transactions \
  -H "Content-Type: application/json" \
  -d '{
    "success": true,
    "data": [
        {
            "date": "2025-01-15",
            "merchant": "AMAZON.COM",
            "amount": 45.99,
            "category": "Shopping"
        }
    ]
  }'
```

**Response:**
```json
{
    "success": true,
    "message": "Successfully saved 1 transactions",
    "transactions_inserted": 1,
    "user_id": "user-123"
}
```

**Anonymous Response:**
```json
{
    "success": true,
    "message": "Successfully saved 1 transactions",
    "transactions_inserted": 1,
    "user_id": null
}
```

### Testing

#### Test with Sample Data
```bash
# Make sure you have a .env file with your Supabase credentials
cp env.example .env
# Edit .env with your actual credentials

# Run the included test script
python test_save_transactions.py
```

#### Test with CSV File
```bash
# Create a test CSV file
echo "Date,Description,Amount
2023-12-25,AMAZON.COM,-45.99
2023-12-24,GROCERY STORE,-23.45" > test.csv

# Parse the file
curl -X POST \
  http://localhost:3000/api/parse-transactions \
  -F "file=@test.csv"

# Save the parsed data with user ID
curl -X POST \
  http://localhost:3000/api/save-transactions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "success": true,
    "data": [/* parsed transactions */]
  }'

# Or save anonymously (without user_id)
curl -X POST \
  http://localhost:3000/api/save-transactions \
  -H "Content-Type: application/json" \
  -d '{
    "success": true,
    "data": [/* parsed transactions */]
  }'
```

## License

MIT License - see LICENSE file for details.