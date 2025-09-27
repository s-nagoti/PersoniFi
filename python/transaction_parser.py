#!/usr/bin/env python3
"""
Transaction Parser for PersoniFi
Parses CSV and Excel files containing bank/credit card transactions
and returns structured JSON data.

Dependencies:
- pandas
- openpyxl (for Excel support)
- python-dateutil

Install with: pip install pandas openpyxl python-dateutil
"""

import sys
import json
import pandas as pd
from datetime import datetime
import re
from typing import List, Dict, Any, Optional


def clean_amount(amount_str: Any) -> Optional[float]:
    """
    Clean and convert amount string to float.
    Handles various formats: $123.45, (123.45), -123.45, etc.
    """
    if pd.isna(amount_str) or amount_str == '':
        return None
    
    # Convert to string and strip whitespace
    amount_str = str(amount_str).strip()
    
    # Remove currency symbols and parentheses (for negative amounts)
    amount_str = re.sub(r'[$€£¥,\s]', '', amount_str)
    amount_str = amount_str.replace('(', '-').replace(')', '')
    
    try:
        return float(amount_str)
    except (ValueError, TypeError):
        return None


def parse_date(date_str: Any) -> Optional[str]:
    """
    Parse various date formats and return YYYY-MM-DD string.
    """
    if pd.isna(date_str) or date_str == '':
        return None
    
    # Common date formats to try
    date_formats = [
        '%Y-%m-%d',      # 2023-12-25
        '%m/%d/%Y',      # 12/25/2023
        '%d/%m/%Y',      # 25/12/2023
        '%Y/%m/%d',      # 2023/12/25
        '%m-%d-%Y',      # 12-25-2023
        '%d-%m-%Y',      # 25-12-2023
        '%b %d, %Y',     # Dec 25, 2023
        '%B %d, %Y',     # December 25, 2023
    ]
    
    date_str = str(date_str).strip()
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # Try pandas date parsing as fallback
    try:
        parsed_date = pd.to_datetime(date_str)
        return parsed_date.strftime('%Y-%m-%d')
    except:
        return None


def find_column_mapping(df: pd.DataFrame) -> Dict[str, str]:
    """
    Automatically detect column mappings for common transaction file formats.
    Returns a mapping of standard fields to actual column names.
    """
    mapping = {}
    columns = [col.lower().strip() for col in df.columns]
    
    # Date column mapping
    date_keywords = ['date', 'transaction date', 'posted date', 'trans date', 'payment date']
    for keyword in date_keywords:
        for i, col in enumerate(columns):
            if keyword in col:
                mapping['date'] = df.columns[i]
                break
        if 'date' in mapping:
            break
    
    # Amount column mapping
    amount_keywords = ['amount', 'transaction amount', 'debit', 'credit', 'posted amount']
    for keyword in amount_keywords:
        for i, col in enumerate(columns):
            if keyword in col:
                mapping['amount'] = df.columns[i]
                break
        if 'amount' in mapping:
            break
    
    # Merchant/Description column mapping
    merchant_keywords = ['description', 'merchant', 'transaction description', 'payee', 'memo']
    for keyword in merchant_keywords:
        for i, col in enumerate(columns):
            if keyword in col:
                mapping['merchant'] = df.columns[i]
                break
        if 'merchant' in mapping:
            break
    
    # Category column mapping (optional)
    category_keywords = ['category', 'transaction category', 'type', 'transaction type']
    for keyword in category_keywords:
        for i, col in enumerate(columns):
            if keyword in col:
                mapping['category'] = df.columns[i]
                break
    
    return mapping


def parse_transactions(file_path: str) -> Dict[str, Any]:
    """
    Main function to parse transaction files and return structured JSON.
    
    Args:
        file_path: Path to the CSV or Excel file
        
    Returns:
        Dictionary containing parsed transactions and metadata
    """
    try:
        # Determine file type and read accordingly
        if file_path.endswith('.csv'):
            # Try different encodings for CSV files
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise ValueError("Could not read CSV file with any supported encoding")
                
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file format. Only CSV and Excel files are supported.")
        
        # Basic validation
        if df.empty:
            raise ValueError("File is empty or contains no data")
        
        # Find column mappings
        column_mapping = find_column_mapping(df)
        
        # Validate required columns
        missing_columns = []
        if 'date' not in column_mapping:
            missing_columns.append('date')
        if 'amount' not in column_mapping:
            missing_columns.append('amount')
        if 'merchant' not in column_mapping:
            missing_columns.append('merchant/description')
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Parse transactions
        transactions = []
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Extract and clean data
                date_str = parse_date(row[column_mapping['date']])
                amount = clean_amount(row[column_mapping['amount']])
                merchant = str(row[column_mapping['merchant']]).strip() if not pd.isna(row[column_mapping['merchant']]) else ""
                
                # Skip empty rows
                if not date_str or amount is None or not merchant:
                    continue
                
                # Build transaction object
                transaction = {
                    "date": date_str,
                    "merchant": merchant,
                    "amount": amount
                }
                
                # Add category if available
                if 'category' in column_mapping and not pd.isna(row[column_mapping['category']]):
                    transaction["category"] = str(row[column_mapping['category']]).strip()
                
                transactions.append(transaction)
                
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")
        
        # Validate results
        if not transactions:
            raise ValueError("No valid transactions found in the file")
        
        # Return structured response
        return {
            "success": True,
            "transactions": transactions,
            "metadata": {
                "total_transactions": len(transactions),
                "file_type": "csv" if file_path.endswith('.csv') else "excel",
                "column_mapping": column_mapping,
                "errors": errors[:10]  # Limit errors to first 10
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "transactions": [],
            "metadata": {}
        }


def main():
    """
    Command line interface for the parser.
    Usage: python transaction_parser.py <file_path>
    """
    if len(sys.argv) != 2:
        print(json.dumps({
            "success": False,
            "error": "Usage: python transaction_parser.py <file_path>"
        }))
        sys.exit(1)
    
    file_path = sys.argv[1]
    result = parse_transactions(file_path)
    
    # Output JSON to stdout for Node.js to capture
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
