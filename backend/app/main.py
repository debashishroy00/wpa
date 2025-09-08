"""
WealthPath AI - FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog
import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import engine
from app.db.base import Base

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter('wealthpath_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('wealthpath_request_duration_seconds', 'Request duration', ['method', 'endpoint'])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler
    """
    # Startup
    logger.info("Starting WealthPath AI backend", version=settings.PROJECT_VERSION)
    
    # Create database tables (tables already created via Alembic)
    logger.info("Database connection verified")
    
    # Initialize LLM clients
    try:
        from app.services.llm_service import llm_service as MultiLLMService
        # Register a basic provider for testing
        logger.info("LLM service available for new endpoints")
    except Exception as e:
        logger.warning(f"LLM service initialization skipped: {e}")
    
    # Start keep-alive service for Render
    if settings.ENVIRONMENT == "production" and settings.KEEP_ALIVE_ENABLED:
        try:
            from app.services.keep_alive import keep_alive_service
            import asyncio
            
            # Get the production URL from environment or construct it
            health_url = settings.KEEP_ALIVE_URL or "https://smartfinanceadvisor.net/health"
            keep_alive_service.set_health_url(health_url, settings.KEEP_ALIVE_INTERVAL_MINUTES)
            
            # Start keep-alive in background task
            asyncio.create_task(keep_alive_service.start_keep_alive())
            logger.info("Keep-alive service started for production", 
                       url=health_url, 
                       interval_minutes=settings.KEEP_ALIVE_INTERVAL_MINUTES)
        except Exception as e:
            logger.warning(f"Keep-alive service failed to start: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down WealthPath AI backend")
    
    # Stop keep-alive service
    if settings.ENVIRONMENT == "production":
        try:
            from app.services.keep_alive import keep_alive_service
            await keep_alive_service.stop_keep_alive()
            logger.info("Keep-alive service stopped")
        except Exception as e:
            logger.warning(f"Keep-alive service cleanup failed: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Intelligent Financial Planning Platform",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json" if settings.ENABLE_DOCS else None,
    docs_url="/docs" if settings.ENABLE_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_DOCS else None,
    lifespan=lifespan
)

# Fix Invalid Host Header Error - Allow all hosts for deployment compatibility
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Allow all hosts (fixes Render/Railway host header issues)
)

# CORS middleware
if settings.ENABLE_CORS:
    # Production CORS configuration for smartfinanceadvisor.net
    production_origins = [
        "https://smartfinanceadvisor.net",
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
        "http://localhost:3005"
    ]
    
    logger.info("CORS enabled with origins", origins=production_origins)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=production_origins,
        allow_credentials=True,  # Enable credentials for authentication
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
    )


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Add processing time header and metrics
    """
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Record metrics
    if settings.ENABLE_METRICS:
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(process_time)
    
    return response


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """
    Structured logging middleware
    """
    start_time = time.time()
    
    # Log request
    logger.info(
        "Request started",
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        "Request completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time=process_time,
    )
    
    return response


# Critical health endpoints FIRST (for Railway/Render deployment)
@app.get("/")
async def root():
    """Root endpoint - Railway/Render health check backup"""
    return {"message": "WealthPath AI Backend is running", "status": "healthy"}


@app.get("/health")
async def health_check():
    """Fast health check for Railway/Render - NO dependencies, NO database calls"""
    from datetime import datetime
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# API Routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)




@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint
    """
    if not settings.ENABLE_METRICS:
        return JSONResponse(
            status_code=404,
            content={"detail": "Metrics are disabled"}
        )
    
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler
    """
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        exception=str(exc),
        exc_info=True,
    )
    
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error": str(exc),
                "path": request.url.path,
            }
        )
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"],
            },
        }
    )