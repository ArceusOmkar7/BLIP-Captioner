#!/usr/bin/env python
"""
BLIP Image Captioning Microservice Runner
----------------------------------------
Script to start the BLIP Image Captioning Microservice
"""
import uvicorn
import os
import argparse


def main():
    """Run the BLIP Image Captioning Microservice."""
    parser = argparse.ArgumentParser(
        description="Run the BLIP Image Captioning Microservice")
    parser.add_argument("--host", default="0.0.0.0",
                        help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000,
                        help="Port to bind the server to")
    parser.add_argument("--reload", action="store_true",
                        help="Enable auto-reload on code changes")
    parser.add_argument("--workers", type=int, default=1,
                        help="Number of worker processes")
    parser.add_argument("--log-level", default="info", help="Logging level")

    args = parser.parse_args()

    print(
        f"Starting BLIP Image Captioning Microservice on {args.host}:{args.port}")

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level=args.log_level
    )


if __name__ == "__main__":
    # Ensure we're running from the correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
