"""
Test script to check if we can import the transaction parser
"""

print("Testing imports...")

try:
    print("1. Testing basic imports...")
    import pandas as pd
    print("✅ Pandas imported successfully")
    
    import openpyxl
    print("✅ Openpyxl imported successfully")
    
    import json
    print("✅ JSON imported successfully")
    
    print("\n2. Testing transaction parser import...")
    from python.transaction_parser import parse_transactions
    print("✅ Transaction parser imported successfully")
    
    print("\n3. Testing parser with sample file...")
    if os.path.exists("sample_transactions.csv"):
        result = parse_transactions("sample_transactions.csv")
        print(f"✅ Parser test successful: {result['success']}")
        if result['success']:
            print(f"   Found {len(result['transactions'])} transactions")
    else:
        print("⚠️ Sample file not found, skipping parser test")
    
    print("\n🎉 All imports successful!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Try: pip install pandas openpyxl")
    
except Exception as e:
    print(f"❌ Error: {e}")

import os
