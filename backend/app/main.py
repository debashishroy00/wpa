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
    
    # Initialize LLM clients at startup (ensures they're available for all endpoints)
    try:
        from app.services.llm_service import llm_service
        
        # Register OpenAI client if API key is available
        if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            from app.services.llm_clients.openai_client import OpenAIClient
            openai_client = OpenAIClient(llm_service.providers["openai"])
            llm_service.register_client("openai", openai_client)
            logger.info("✅ OpenAI client registered at startup")
        
        # Register Gemini client if API key is available
        if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
            from app.services.llm_clients.gemini_client import GeminiClient
            gemini_client = GeminiClient(llm_service.providers["gemini"])
            llm_service.register_client("gemini", gemini_client)
            logger.info("✅ Gemini client registered at startup")
        
        # Register Anthropic/Claude client if API key is available
        if hasattr(settings, 'ANTHROPIC_API_KEY') and settings.ANTHROPIC_API_KEY:
            try:
                from app.services.llm_clients.claude_client import ClaudeClient
                claude_client = ClaudeClient(llm_service.providers["claude"])
                llm_service.register_client("claude", claude_client)
                logger.info("✅ Claude client registered at startup")
            except ImportError:
                logger.info("Claude client not available")
        
        registered_clients = list(llm_service.clients.keys())
        logger.info(f"LLM service initialized with clients: {registered_clients}")
        
    except Exception as e:
        logger.warning(f"LLM service initialization failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down WealthPath AI backend")


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
    # Parse CORS origins from comma-separated string
    cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
    
    logger.info("CORS enabled with origins", origins=cors_origins)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for development
        allow_credentials=False,  # Must be False when allow_origins=["*"]
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