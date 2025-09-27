# PersoniFi Backend

A Node.js + Express backend service for parsing bank and credit card statements from CSV and Excel files. The service extracts transaction data and returns it in a structured JSON format for visualization and AI analysis.

## Features

- 📁 **File Upload**: Accepts CSV and Excel (.xlsx, .xls) files via HTTP POST
- 🔍 **Smart Parsing**: Automatically detects column mappings for common bank statement formats
- 📊 **Structured Output**: Returns transactions in standardized JSON format
- 🛡️ **Error Handling**: Comprehensive validation and error handling
- 🔒 **Security**: Rate limiting, file type validation, and security headers
- 🐍 **Python Integration**: Uses Python (Pandas) for robust file parsing

## Tech Stack

- **Backend**: Node.js + Express.js
- **File Parsing**: Python + Pandas
- **Security**: Helmet, CORS, Rate Limiting
- **File Upload**: Multer

## Quick Start

### Prerequisites

- Node.js (v16 or higher)
- Python (v3.8 or higher)
- npm or yarn

### Installation

1. **Clone and setup the project:**
   ```bash
   git clone <your-repo>
   cd PersoniFi
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Install Python dependencies:**
   ```bash
   cd python
   pip install -r requirements.txt
   cd ..
   ```

4. **Start the server:**
   ```bash
   npm start
   # or for development with auto-reload:
   npm run dev
   ```

The server will start on `http://localhost:3000`

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
├── server.js              # Express server
├── package.json           # Node.js dependencies
├── python/
│   ├── transaction_parser.py  # Python parsing script
│   └── requirements.txt       # Python dependencies
├── uploads/               # Temporary file storage (auto-created)
└── README.md
```

### Environment Variables

- `PORT`: Server port (default: 3000)
- `FRONTEND_URL`: CORS origin for frontend (default: http://localhost:3001)

### Testing

Test the endpoint with a sample CSV file:

```bash
# Create a test CSV file
echo "Date,Description,Amount
2023-12-25,AMAZON.COM,-45.99
2023-12-24,GROCERY STORE,-23.45" > test.csv

# Test the API
curl -X POST \
  http://localhost:3000/api/parse-transactions \
  -F "file=@test.csv"
```

## License

MIT License - see LICENSE file for details.