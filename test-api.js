/**
 * Test script for the PersoniFi API endpoint
 * Tests file upload and parsing functionality
 */

const fs = require('fs');
const path = require('path');

// Create a simple test using Node.js built-in modules
const testFileUpload = async () => {
    const filePath = path.join(__dirname, 'sample_transactions.csv');
    
    if (!fs.existsSync(filePath)) {
        console.error('❌ Test file not found:', filePath);
        return;
    }
    
    console.log('🧪 Testing PersoniFi API endpoint...');
    console.log('📁 File:', filePath);
    
    // Read the file
    const fileContent = fs.readFileSync(filePath);
    const fileName = path.basename(filePath);
    
    // Create multipart form data manually
    const boundary = '----formdata-test-' + Date.now();
    const CRLF = '\r\n';
    
    let body = '';
    body += '--' + boundary + CRLF;
    body += 'Content-Disposition: form-data; name="file"; filename="' + fileName + '"' + CRLF;
    body += 'Content-Type: text/csv' + CRLF;
    body += CRLF;
    body += fileContent.toString();
    body += CRLF;
    body += '--' + boundary + '--' + CRLF;
    
    try {
        const response = await fetch('http://localhost:3000/api/parse-transactions', {
            method: 'POST',
            headers: {
                'Content-Type': 'multipart/form-data; boundary=' + boundary,
                'Content-Length': Buffer.byteLength(body)
            },
            body: body
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('✅ API Test Successful!');
            console.log(`📊 Total transactions parsed: ${result.metadata.total_transactions}`);
            console.log(`📅 Date range: ${result.data[result.data.length - 1].date} to ${result.data[0].date}`);
            console.log(`💰 Sample transactions:`);
            
            // Show first 3 transactions
            result.data.slice(0, 3).forEach((tx, i) => {
                console.log(`   ${i + 1}. ${tx.date} | ${tx.merchant.substring(0, 30)}... | $${tx.amount} | ${tx.category}`);
            });
            
            console.log(`\n📋 Column mapping used:`);
            console.log(`   Date: ${result.metadata.column_mapping.date}`);
            console.log(`   Amount: ${result.metadata.column_mapping.amount}`);
            console.log(`   Merchant: ${result.metadata.column_mapping.merchant}`);
            console.log(`   Category: ${result.metadata.column_mapping.category}`);
            
        } else {
            console.log('❌ API Test Failed!');
            console.log('Error:', result.error);
        }
        
    } catch (error) {
        console.error('❌ Request failed:', error.message);
    }
};

// Run the test
testFileUpload();
