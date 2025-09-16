"""
Database connection cleanup middleware for Supabase compatibility
"""
from fastapi import Request
import structlog
from sqlalchemy.pool import NullPool
from app.db.session import engine

logger = structlog.get_logger()

async def db_cleanup_middleware(request: Request, call_next):
    """
    Middleware to ensure database connections are properly closed
    This is critical for Supabase Session Pooler mode
    """
    try:
        # Process the request
        response = await call_next(request)
        return response
    finally:
        # Always dispose of connections after each request
        # This ensures connections are returned to Supabase pooler
        try:
            # Close all checked-out connections
            engine.dispose()
        except Exception as e:
            logger.warning("Failed to dispose engine connections", error=str(e))