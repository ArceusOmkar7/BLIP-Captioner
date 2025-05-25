#!/usr/bin/env python
"""
BLIP Image Captioning Microservice Runner
----------------------------------------
Script to start the BLIP Image Captioning Microservice
"""
import uvicorn
import os
import argparse
from app.core.config import settings, logger  # Import settings and logger


def main():
    """Run the BLIP Image Captioning Microservice using settings from config and CLI overrides."""
    parser = argparse.ArgumentParser(
        description="Run the BLIP Image Captioning Microservice")
    # Use settings from config.py as defaults, allowing CLI to override
    parser.add_argument("--host", default=settings.HOST,
                        help=f"Host to bind the server to (default: {settings.HOST})")
    parser.add_argument("--port", type=int, default=settings.PORT,
                        help=f"Port to bind the server to (default: {settings.PORT})")
    parser.add_argument("--reload", action=argparse.BooleanOptionalAction, default=settings.RELOAD,
                        help=f"Enable/disable auto-reload on code changes (default: {settings.RELOAD})")
    parser.add_argument("--workers", type=int, default=settings.WORKERS,
                        help=f"Number of worker processes (default: {settings.WORKERS})")
    parser.add_argument("--log-level", default=settings.LOG_LEVEL,
                        help=f"Logging level (default: {settings.LOG_LEVEL})")

    args = parser.parse_args()

    # Update settings with CLI arguments if they were provided
    # This ensures that if .env or defaults were used, CLI can still win
    # However, argparse already handles this by args.host etc. having the final value.
    # The logger in config.py is already configured. We can use it here.
    logger.info(
        f"Starting BLIP Image Captioning Microservice on {args.host}:{args.port}")
    logger.info(
        f"Reload: {args.reload}, Workers: {args.workers}, Log Level: {args.log_level}")

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
