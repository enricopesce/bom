#!/usr/bin/env python3
"""
VM Assessment BOM Generator - Development Server Starter
Simple entry point for development mode
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

if __name__ == "__main__":
    from app import app
    import uvicorn
    
    # Development configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    print("🚀 VM Assessment BOM Generator - Development Server")
    print("=" * 50)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Log Level: {log_level}")
    print(f"Access: http://localhost:{port}")
    print("=" * 50)
    
    uvicorn.run(
        app, 
        host=host, 
        port=port, 
        log_level=log_level,
        reload=True
    )