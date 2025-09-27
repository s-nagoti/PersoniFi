#!/usr/bin/env python3
"""
Test script for the new /api/upload-and-save endpoint

This script demonstrates how to use the new endpoint that combines
file parsing and database saving in a single operation.

Usage:
    python test_upload_and_save.py

Requirements:
    - FastAPI server running on localhost:3000
    - Valid .env file with SUPABASE_URL and SUPABASE_ANON_KEY
    - Sample transaction file (CSV or Excel)
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_upload_and_save():
    """Test the new upload-and-save endpoint"""
    
    # Configuration
    base_url = "http://localhost:3000"
    endpoint = f"{base_url}/api/upload-and-save"
    
    # Sample file path - replace with your actual file
    sample_file = "sample_transactions.csv"  # Update this path
    
    # Check if sample file exists
    if not os.path.exists(sample_file):
        print(f"❌ Sample file '{sample_file}' not found.")
        print("Please create a sample CSV file with transaction data or update the file path.")
        return
    
    # Check environment variables
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_ANON_KEY"):
        print("❌ Missing environment variables SUPABASE_URL and SUPABASE_ANON_KEY")
        print("Please check your .env file.")
        return
    
    try:
        # Prepare the request
        with open(sample_file, 'rb') as file:
            files = {'file': (sample_file, file, 'text/csv')}
            
            print(f"🚀 Testing upload-and-save endpoint...")
            print(f"📁 File: {sample_file}")
            print(f"🔗 Endpoint: {endpoint}")
            print()
            
            # Make the request
            response = requests.post(endpoint, files=files)
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                print("✅ Request successful!")
                print(f"📊 Response: {result}")
                
                if result.get("success"):
                    print(f"🎉 Successfully saved {result.get('inserted', 0)} transactions!")
                    if result.get("errors"):
                        print(f"⚠️  Errors encountered: {result['errors']}")
                else:
                    print("❌ Operation failed")
                    if result.get("errors"):
                        print(f"🚨 Errors: {result['errors']}")
                        
            else:
                print(f"❌ Request failed with status code: {response.status_code}")
                print(f"📝 Response: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server.")
        print("Make sure the FastAPI server is running on localhost:3000")
        
    except FileNotFoundError:
        print(f"❌ File '{sample_file}' not found.")
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

def test_health_check():
    """Test if the server is running"""
    try:
        response = requests.get("http://localhost:3000/api/health")
        if response.status_code == 200:
            print("✅ Server is running and healthy!")
            return True
        else:
            print(f"⚠️  Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running or not accessible")
        return False

if __name__ == "__main__":
    print("🧪 Testing PersoniFi Upload-and-Save Endpoint")
    print("=" * 50)
    
    # First check if server is running
    if test_health_check():
        print()
        test_upload_and_save()
    else:
        print("\n💡 To start the server, run:")
        print("   python main.py")
        print("   or")
        print("   uvicorn main:app --host 0.0.0.0 --port 3000 --reload")
