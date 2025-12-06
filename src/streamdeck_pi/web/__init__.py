"""
Web interface for Stream Deck Pi Manager.
"""
from streamdeck_pi.web.app import create_app

__all__ = ["create_app"]


def main():
    """Main entry point for web server."""
    import uvicorn
    import argparse
    import logging

    parser = argparse.ArgumentParser(description="Stream Deck Pi Manager Web Interface")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8888, help="Port to bind to")
    parser.add_argument("--dev", action="store_true", help="Development mode")
    parser.add_argument("--reload", action="store_true", help="Auto-reload on code changes")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.dev else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    app = create_app()

    uvicorn.run(
        "streamdeck_pi.web.app:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        reload=args.reload or args.dev,
        log_level="debug" if args.dev else "info",
    )


if __name__ == "__main__":
    main()
