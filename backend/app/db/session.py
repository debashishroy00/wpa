"""
WealthPath AI - Database Session Management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Check if we're in production (Supabase)
is_production = "supabase" in settings.DATABASE_URL.lower()

if is_production:
    # Use NullPool for Supabase to avoid connection pooling issues
    # Each request gets its own connection which is immediately closed after use
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=NullPool,  # No connection pooling - critical for Supabase
        echo=settings.DEBUG,
        connect_args={
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        }
    )
    logger.info("Using NullPool for Supabase production database")
else:
    # Use normal pooling for local development
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=10,
        echo=settings.DEBUG
    )
    logger.info("Using standard connection pool for local database")

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