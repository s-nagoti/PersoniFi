#!/usr/bin/env python3
"""
Test script for PersoniFi FastAPI endpoints
Tests all API endpoints to ensure they're working correctly.
"""

import requests
import json
import os
from pathlib import Path

BASE_URL = "http://localhost:3000"

def test_health():
    """Test health check endpoint"""
    print("🧪 Testing health check endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['message']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_formats():
    """Test supported formats endpoint"""
    print("\n🧪 Testing supported formats endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/formats")
        if response.status_code == 200:
            data = response.json()
            print("✅ Supported formats endpoint working")
            print(f"   Supported formats: {list(data['supported_formats'].keys())}")
            return True
        else:
            print(f"❌ Formats endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Formats endpoint error: {e}")
        return False

def test_file_upload():
    """Test file upload endpoint"""
    print("\n🧪 Testing file upload endpoint...")
    
    # Check if sample file exists
    sample_file = "sample_transactions.csv"
    if not os.path.exists(sample_file):
        print(f"❌ Sample file not found: {sample_file}")
        return False
    
    try:
        with open(sample_file, 'rb') as f:
            files = {'file': (sample_file, f, 'text/csv')}
            response = requests.post(f"{BASE_URL}/api/parse-transactions", files=files)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                transactions = data.get('data', [])
                metadata = data.get('metadata', {})
                print(f"✅ File upload successful!")
                print(f"   Parsed {len(transactions)} transactions")
                print(f"   File type: {metadata.get('file_type')}")
                print(f"   Column mapping: {metadata.get('column_mapping')}")
                
                # Show first few transactions
                if transactions:
                    print("   Sample transactions:")
                    for i, tx in enumerate(transactions[:3]):
                        print(f"     {i+1}. {tx['date']} | {tx['merchant'][:30]}... | ${tx['amount']}")
                
                return True
            else:
                print(f"❌ Parsing failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Upload failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error')}")
            except:
                print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

def test_invalid_file():
    """Test with invalid file type"""
    print("\n🧪 Testing invalid file type rejection...")
    
    # Create a temporary text file
    with open("test_invalid.txt", "w") as f:
        f.write("This is not a valid CSV file")
    
    try:
        with open("test_invalid.txt", 'rb') as f:
            files = {'file': ('test_invalid.txt', f, 'text/plain')}
            response = requests.post(f"{BASE_URL}/api/parse-transactions", files=files)
        
        if response.status_code == 400:
            data = response.json()
            print("✅ Invalid file type correctly rejected")
            print(f"   Error: {data.get('error')}")
            return True
        else:
            print(f"❌ Expected 400 error, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Invalid file test error: {e}")
        return False
    finally:
        # Clean up test file
        if os.path.exists("test_invalid.txt"):
            os.remove("test_invalid.txt")

def main():
    """Run all tests"""
    print("🚀 PersoniFi FastAPI Backend Tests")
    print("=" * 50)
    
    tests = [
        test_health,
        test_formats,
        test_file_upload,
        test_invalid_file
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! FastAPI server is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the server logs for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
