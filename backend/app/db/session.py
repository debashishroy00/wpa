"""
WealthPath AI - Database Session Management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Create database engine with optimized pool settings for Supabase
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,  # Reduced from default 10 to prevent exhaustion
    max_overflow=10,  # Allow some overflow connections
    pool_timeout=30,  # Wait up to 30 seconds for a connection
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()


def get_db():
    """
    Database dependency for FastAPI with proper cleanup
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error("Database session error", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


async def create_tables():
    """
    Create all database tables
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise


async def drop_tables():
    """
    Drop all database tables (use with caution)
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
    except Exception as e:
        logger.error("Failed to drop database tables", error=str(e))
        raise