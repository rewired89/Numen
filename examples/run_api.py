#!/usr/bin/env python3
"""
Launch Numen API server.

Usage:
    python examples/run_api.py
"""

if __name__ == "__main__":
    import uvicorn
    from numen.api.server import app

    print("Starting Numen API server...")
    print("API docs available at: http://localhost:8000/docs")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
