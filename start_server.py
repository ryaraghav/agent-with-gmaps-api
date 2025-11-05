#!/usr/bin/env python3
"""
Start the FastAPI server for the restaurant agent
"""
import uvicorn
from app import app

if __name__ == "__main__":
    print("🍽️  Starting Restaurant Agent Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("🔗 Endpoint: POST /run")
    print("💬 Using conversational agent from agent.py")
    print("📖 API Docs: http://localhost:8000/docs")
    print("-" * 50)
    
    uvicorn.run(
        "app:app", 
        host="0.0.0.0", 
        port=8000,
        reload=True  # Auto-reload on code changes
    )
