/**
 * PersoniFi Backend Server
 * Express.js server for handling bank/credit card statement uploads and parsing
 * 
 * Dependencies:
 * - express: Web framework
 * - multer: File upload middleware
 * - cors: Cross-origin resource sharing
 * - helmet: Security headers
 * - express-rate-limit: Rate limiting
 * - python-shell: Execute Python scripts from Node.js
 */

const express = require('express');
const multer = require('multer');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const { PythonShell } = require('python-shell');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

// Security middleware
app.use(helmet());

// CORS configuration
app.use(cors({
    origin: process.env.FRONTEND_URL || 'http://localhost:3001',
    credentials: true
}));

// Rate limiting
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // Limit each IP to 100 requests per windowMs
    message: 'Too many requests from this IP, please try again later.'
});
app.use('/api/', limiter);

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Configure multer for file uploads
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        // Create uploads directory if it doesn't exist
        const uploadDir = 'uploads';
        if (!fs.existsSync(uploadDir)) {
            fs.mkdirSync(uploadDir, { recursive: true });
        }
        cb(null, uploadDir);
    },
    filename: function (req, file, cb) {
        // Generate unique filename with timestamp
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
    }
});

// File filter for multer
const fileFilter = (req, file, cb) => {
    // Only allow CSV and Excel files
    const allowedTypes = [
        'text/csv',
        'application/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ];
    
    const allowedExtensions = ['.csv', '.xlsx', '.xls'];
    const fileExtension = path.extname(file.originalname).toLowerCase();
    
    if (allowedTypes.includes(file.mimeType) || allowedExtensions.includes(fileExtension)) {
        cb(null, true);
    } else {
        cb(new Error('Invalid file type. Only CSV and Excel files are allowed.'), false);
    }
};

const upload = multer({
    storage: storage,
    fileFilter: fileFilter,
    limits: {
        fileSize: 10 * 1024 * 1024, // 10MB limit
        files: 1 // Only allow one file at a time
    }
});

// Error handling middleware
app.use((error, req, res, next) => {
    if (error instanceof multer.MulterError) {
        if (error.code === 'LIMIT_FILE_SIZE') {
            return res.status(400).json({
                success: false,
                error: 'File too large. Maximum size is 10MB.'
            });
        }
        if (error.code === 'LIMIT_FILE_COUNT') {
            return res.status(400).json({
                success: false,
                error: 'Too many files. Only one file allowed per request.'
            });
        }
    }
    
    if (error.message) {
        return res.status(400).json({
            success: false,
            error: error.message
        });
    }
    
    res.status(500).json({
        success: false,
        error: 'Internal server error'
    });
});

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({
        success: true,
        message: 'PersoniFi Backend is running',
        timestamp: new Date().toISOString()
    });
});

// Main transaction parsing endpoint
app.post('/api/parse-transactions', upload.single('file'), async (req, res) => {
    try {
        // Validate file upload
        if (!req.file) {
            return res.status(400).json({
                success: false,
                error: 'No file uploaded. Please upload a CSV or Excel file.'
            });
        }

        const filePath = req.file.path;
        const originalName = req.file.originalname;
        const fileSize = req.file.size;

        console.log(`Processing file: ${originalName} (${fileSize} bytes)`);

        // Execute Python script to parse the file
        const options = {
            mode: 'text',
            pythonPath: 'python', // Adjust if Python is not in PATH
            pythonOptions: ['-u'], // Unbuffered output
            scriptPath: path.join(__dirname, 'python'),
            args: [filePath]
        };

        PythonShell.run('transaction_parser.py', options, (err, results) => {
            // Clean up uploaded file
            fs.unlink(filePath, (unlinkErr) => {
                if (unlinkErr) {
                    console.error('Error deleting uploaded file:', unlinkErr);
                }
            });

            if (err) {
                console.error('Python script error:', err);
                return res.status(500).json({
                    success: false,
                    error: 'Failed to parse file. Please check the file format and try again.',
                    details: err.message
                });
            }

            try {
                // Parse JSON output from Python script
                const result = JSON.parse(results.join(''));
                
                if (result.success) {
                    // Return successful response with transactions
                    res.json({
                        success: true,
                        data: result.transactions,
                        metadata: {
                            ...result.metadata,
                            original_filename: originalName,
                            file_size: fileSize
                        }
                    });
                } else {
                    // Return error from Python script
                    res.status(400).json({
                        success: false,
                        error: result.error || 'Failed to parse transactions',
                        metadata: result.metadata || {}
                    });
                }
            } catch (parseError) {
                console.error('JSON parse error:', parseError);
                res.status(500).json({
                    success: false,
                    error: 'Invalid response from parser. Please try again.'
                });
            }
        });

    } catch (error) {
        console.error('Server error:', error);
        
        // Clean up file if it exists
        if (req.file && req.file.path) {
            fs.unlink(req.file.path, (unlinkErr) => {
                if (unlinkErr) {
                    console.error('Error deleting uploaded file:', unlinkErr);
                }
            });
        }

        res.status(500).json({
            success: false,
            error: 'Internal server error. Please try again later.'
        });
    }
});

// Get supported file formats endpoint
app.get('/api/formats', (req, res) => {
    res.json({
        success: true,
        supported_formats: {
            csv: {
                extensions: ['.csv'],
                mime_types: ['text/csv', 'application/csv'],
                max_size: '10MB'
            },
            excel: {
                extensions: ['.xlsx', '.xls'],
                mime_types: [
                    'application/vnd.ms-excel',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                ],
                max_size: '10MB'
            }
        },
        required_columns: ['date', 'amount', 'merchant/description'],
        optional_columns: ['category'],
        example_structure: {
            date: 'YYYY-MM-DD',
            merchant: 'string',
            amount: 'float',
            category: 'string (optional)'
        }
    });
});

// 404 handler
app.use('*', (req, res) => {
    res.status(404).json({
        success: false,
        error: 'Endpoint not found'
    });
});

// Start server
app.listen(PORT, () => {
    console.log(`🚀 PersoniFi Backend server running on port ${PORT}`);
    console.log(`📁 Upload directory: ${path.join(__dirname, 'uploads')}`);
    console.log(`🐍 Python parser: ${path.join(__dirname, 'python', 'transaction_parser.py')}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('SIGTERM received. Shutting down gracefully...');
    process.exit(0);
});

process.on('SIGINT', () => {
    console.log('SIGINT received. Shutting down gracefully...');
    process.exit(0);
});

module.exports = app;
