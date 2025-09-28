#!/usr/bin/env python3
"""
PersoniFi FastAPI Server Startup Script
Simple script to start the FastAPI development server with proper configuration.
"""

import uvicorn
import sys
import os
from dotenv import load_dotenv

def main():
    """Start the FastAPI development server"""
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    print("🚀 Starting PersoniFi FastAPI Backend Server...")
    print("📁 Working directory:", current_dir)
    print("🌐 Server will be available at: http://localhost:3000")
    print("📚 API Documentation: http://localhost:3000/docs")
    print("📖 ReDoc Documentation: http://localhost:3000/redoc")
    print("=" * 60)
    
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True,
            reload_dirs=[current_dir]
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
