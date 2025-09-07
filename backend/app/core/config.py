"""
WealthPath AI - Core Configuration Settings
"""
from functools import lru_cache
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings
import secrets


class Settings(BaseSettings):
    """
    Application settings with Pydantic validation
    """
    # Project Information
    PROJECT_NAME: str = "WealthPath AI"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Security
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12
    
    # Database
    DATABASE_URL: str = "postgresql://wealthpath_user:wealthpath_dev_password@localhost:5432/wealthpath_db"
    POSTGRES_DB: str = "wealthpath_db"
    POSTGRES_USER: str = "wealthpath_user"
    POSTGRES_PASSWORD: str = "wealthpath_dev_password"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # CORS
    CORS_ORIGINS: str = "https://smartfinanceadvisor.net,http://localhost:3004,http://127.0.0.1:3004"
    ENABLE_CORS: bool = True
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    RATE_LIMIT_BURST: int = 20
    
    # Email Configuration
    SMTP_SERVER: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@wealthpath.ai"
    SMTP_USE_TLS: bool = True
    
    # External APIs
    PLAID_CLIENT_ID: str = ""
    PLAID_SECRET: str = ""
    PLAID_ENVIRONMENT: str = "sandbox"
    
    # LLM API Keys
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    
    # LLM Configuration
    LLM_DEFAULT_PROVIDER: str = "openai"
    LLM_DEFAULT_TIER: str = "dev"
    LLM_CACHE_ENABLED: bool = True
    LLM_CACHE_TTL_HOURS: int = 24
    LLM_MAX_COST_PER_REQUEST: float = 1.00
    KNOWLEDGE_BASE_PATH: str = "./knowledge_base"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    ENABLE_REQUEST_LOGGING: bool = True
    
    # ML Configuration
    ML_MODEL_PATH: str = "./models"
    ML_CACHE_TTL_SECONDS: int = 3600
    ML_BATCH_SIZE: int = 100
    
    # Monitoring & Observability
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9091
    
    # Session Configuration
    SESSION_COOKIE_SECURE: bool = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "lax"
    
    # File Upload
    UPLOAD_FOLDER: str = "./uploads"
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    
    # Feature Flags
    ENABLE_DOCS: bool = True
    
    # Hybrid Embedding System Configuration
    USE_HYBRID_EMBEDDINGS: bool = False
    EMBEDDING_ENABLE_CACHING: bool = True
    EMBEDDING_ENABLE_ROUTING: bool = True
    EMBEDDING_ENABLE_MONITORING: bool = True
    EMBEDDING_SHADOW_MODE: bool = False
    EMBEDDING_ENABLE_OPENAI: bool = True
    EMBEDDING_ENABLE_LOCAL: bool = True
    EMBEDDING_QUALITY_COMPARISON: bool = False
    
    # Embedding Cache Configuration
    EMBEDDING_L1_CACHE_SIZE: int = 1000
    EMBEDDING_L2_CACHE_TTL_API: int = 7 * 24 * 3600  # 7 days
    EMBEDDING_L2_CACHE_TTL_LOCAL: int = 24 * 3600    # 24 hours
    
    # Embedding Routing Configuration
    EMBEDDING_DAILY_API_BUDGET_USD: float = 10.0
    EMBEDDING_COST_PER_REQUEST_THRESHOLD: float = 0.01
    EMBEDDING_REALTIME_LATENCY_THRESHOLD_MS: float = 1000
    EMBEDDING_BATCH_SIZE_THRESHOLD: int = 100
    EMBEDDING_API_ERROR_RATE_THRESHOLD: float = 0.1
    EMBEDDING_API_LATENCY_THRESHOLD_MS: float = 5000
    
    # OpenAI Embedding Configuration
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_EMBEDDING_MAX_RETRIES: int = 3
    OPENAI_EMBEDDING_BASE_DELAY: float = 1.0
    OPENAI_EMBEDDING_MAX_DELAY: float = 60.0
    OPENAI_EMBEDDING_JITTER: bool = True
    
    # Local Embedding Configuration  
    LOCAL_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    LOCAL_EMBEDDING_DEVICE: str = "auto"  # "auto", "cpu", or "cuda"
    LOCAL_EMBEDDING_BATCH_SIZE: int = 32
    
    # Circuit Breaker Configuration
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 3
    CIRCUIT_BREAKER_SUCCESS_THRESHOLD: int = 2
    CIRCUIT_BREAKER_TIMEOUT_SECONDS: int = 60
    CIRCUIT_BREAKER_RESET_TIMEOUT: int = 300
    RELOAD_ON_CHANGE: bool = True
    
    # Validation
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v):
        allowed_envs = ["development", "staging", "production"]
        if v not in allowed_envs:
            raise ValueError(f"ENVIRONMENT must be one of {allowed_envs}")
        return v
    
    @field_validator("JWT_ALGORITHM")
    @classmethod
    def validate_jwt_algorithm(cls, v):
        allowed_algs = ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]
        if v not in allowed_algs:
            raise ValueError(f"JWT_ALGORITHM must be one of {allowed_algs}")
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"LOG_LEVEL must be one of {allowed_levels}")
        return v.upper()
    
    @field_validator("ACCESS_TOKEN_EXPIRE_MINUTES")
    @classmethod
    def validate_access_token_expire(cls, v):
        if v <= 0 or v > 1440:  # Max 24 hours
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be between 1 and 1440")
        return v
    
    @field_validator("REFRESH_TOKEN_EXPIRE_DAYS")
    @classmethod
    def validate_refresh_token_expire(cls, v):
        if v <= 0 or v > 90:  # Max 90 days
            raise ValueError("REFRESH_TOKEN_EXPIRE_DAYS must be between 1 and 90")
        return v
    
    model_config = {
        "env_file": [".env", ".env.development", "../.env.development"],
        "case_sensitive": True,
        "env_parse_none_str": None  # Don't try to parse empty strings as JSON
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    """
    return Settings()


# Global settings instance
settings = get_settings()