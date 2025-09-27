#!/usr/bin/env python3
"""
Test script for the /api/save-transactions endpoint
Demonstrates how to use the new endpoint with sample data.
"""

import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_save_transactions():
    """Test the save transactions endpoint with sample data"""
    
    # API endpoint URL
    url = "http://localhost:3000/api/save-transactions"
    
    # Sample transaction data matching the expected format
    sample_request = {
        "success": True,
        "data": [
        {
            "date": "2025-08-12",
            "merchant": "BARNES & NOBLE #2086 EXTON PAAPPLE PAY ENDING IN 4642",
            "amount": 25.44,
            "category": "Merchandise"
        },
        {
            "date": "2025-08-12",
            "merchant": "EARTHSPEAK CHESTER SPRINPA",
            "amount": 14.84,
            "category": "Merchandise"
        },
        {
            "date": "2025-08-12",
            "merchant": "WAWA 118 DOWNINGTOWN PAAPPLE PAY ENDING IN 4642",
            "amount": 11.88,
            "category": "Gasoline"
        },
        {
            "date": "2025-08-12",
            "merchant": "WAWA 118 DOWNINGTOWN PAAPPLE PAY ENDING IN 4642",
            "amount": 41.4,
            "category": "Gasoline"
        },
        {
            "date": "2025-08-12",
            "merchant": "WEGMANS #050 DOWNINGTOWN PAAPPLE PAY ENDING IN 4642",
            "amount": 50.43,
            "category": "Supermarkets"
        },
        {
            "date": "2025-08-11",
            "merchant": "DIRECTPAY FULL BALANCESEE DETAILS OF YOUR NEXT DIRECTPAY BELOW",
            "amount": -923.62,
            "category": "Payments and Credits"
        },
        {
            "date": "2025-08-11",
            "merchant": "KINDRED SOCIETY EXTON PAAPPLE PAY ENDING IN 4642",
            "amount": 43.05,
            "category": "Services"
        }
    ],
    "metadata": {
        "total_transactions": 7,
        "file_type": "csv",
        "column_mapping": {
            "date": "Trans. Date",
            "amount": "Amount",
            "merchant": "Description",
            "category": "Category"
        },
        "errors": [],
        "original_filename": "sample_transactions.csv",
        "file_size": 708,
        "upload_timestamp": "2025-09-27T15:26:18.353949",
        "processing_time": "2025-09-27T15:26:18.353949"
    }
    }
    
    try:
        print("🚀 Testing /api/save-transactions endpoint...")
        print(f"📡 URL: {url}")
        print(f"📊 Sending {len(sample_request['data'])} transactions")
        print("=" * 60)
        
        # Send POST request
        response = requests.post(
            url,
            json=sample_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📈 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        # Parse response
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"📄 Response Body:")
            print(json.dumps(response_data, indent=2))
        else:
            print(f"📄 Response Text: {response.text}")
        
        # Check if successful
        if response.status_code == 200:
            print("\n✅ SUCCESS: Transactions saved successfully!")
            if isinstance(response_data, dict):
                print(f"💾 Transactions inserted: {response_data.get('transactions_inserted', 'N/A')}")
        else:
            print(f"\n❌ ERROR: Request failed with status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to the server.")
        print("💡 Make sure the FastAPI server is running on http://localhost:3000")
        print("💡 Start the server with: python start_server.py")
        
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out. The server might be overloaded.")
        
    except Exception as e:
        print(f"❌ ERROR: Unexpected error occurred: {str(e)}")

def test_save_transactions_without_user_id():
    """Test the save transactions endpoint without user_id (anonymous)"""
    
    # API endpoint URL
    url = "http://localhost:3000/api/save-transactions"
    
    # Sample transaction data without user_id
    sample_request = {
        "success": True,
        "data": [
            {
                "date": "2025-01-15",
                "merchant": "TEST MERCHANT ANONYMOUS",
                "amount": 10.00,
                "category": "Test"
            },
            {
                "date": "2025-01-14",
                "merchant": "ANOTHER TEST MERCHANT",
                "amount": 5.50,
                "category": "Test"
            }
        ],
        "metadata": {
            "source": "anonymous_test",
            "parsed_at": datetime.now().isoformat()
        }
    }
    
    try:
        print("\n🚀 Testing /api/save-transactions endpoint WITHOUT user_id...")
        print(f"📡 URL: {url}")
        print(f"📊 Sending {len(sample_request['data'])} anonymous transactions")
        print("=" * 60)
        
        # Send POST request
        response = requests.post(
            url,
            json=sample_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📈 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        # Parse response
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"📄 Response Body:")
            print(json.dumps(response_data, indent=2))
        else:
            print(f"📄 Response Text: {response.text}")
        
        # Check if successful
        if response.status_code == 200:
            print("\n✅ SUCCESS: Anonymous transactions saved successfully!")
            if isinstance(response_data, dict):
                print(f"💾 Transactions inserted: {response_data.get('transactions_inserted', 'N/A')}")
                print(f"👤 User ID: {response_data.get('user_id', 'None (anonymous)')}")
        else:
            print(f"\n❌ ERROR: Request failed with status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to the server.")
        print("💡 Make sure the FastAPI server is running on http://localhost:3000")
        print("💡 Start the server with: python start_server.py")
        
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out. The server might be overloaded.")
        
    except Exception as e:
        print(f"❌ ERROR: Unexpected error occurred: {str(e)}")

def test_invalid_data():
    """Test the endpoint with invalid data to verify error handling"""
    
    url = "http://localhost:3000/api/save-transactions"
    
    # Test with empty data array
    invalid_request = {
        "success": True,
        "data": []
    }
    
    try:
        print("\n🧪 Testing with invalid data (empty data array)...")
        
        response = requests.post(
            url,
            json=invalid_request,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📈 Response Status: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"📄 Response Body:")
            print(json.dumps(response_data, indent=2))
        
        if response.status_code == 400:  # Bad request error
            print("✅ SUCCESS: Properly handled validation error for empty data")
        else:
            print(f"⚠️  WARNING: Expected 400 status, got {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    print("PersoniFi Save Transactions API Test")
    print("=" * 60)
    
    # Test with valid data (with user_id)
    test_save_transactions()
    
    # Test with valid data (without user_id - anonymous)
    test_save_transactions_without_user_id()
    
    # Test with invalid data
    test_invalid_data()
    
    print("\n" + "=" * 60)
    print("🏁 Test completed!")
    print("\n💡 Tips:")
    print("- Make sure your Supabase credentials are set in .env file")
    print("- Ensure the 'transactions' table exists in your Supabase database")
    print("- Check the server logs for detailed error information")
    print("- user_id is now optional - transactions can be saved anonymously")
