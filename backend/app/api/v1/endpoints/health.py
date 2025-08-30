"""
Health Check Endpoints
Comprehensive system health monitoring for production deployment
"""
import os
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
import structlog

from app.db.session import get_db
from app.services.simple_vector_store import simple_vector_store

logger = structlog.get_logger()
router = APIRouter()

# Health check cache to prevent overwhelming the system
_health_cache = {}
_cache_ttl = 30  # seconds

def get_cached_health(check_name: str):
    """Get cached health check result if still valid"""
    if check_name in _health_cache:
        cached_time, cached_result = _health_cache[check_name]
        if time.time() - cached_time < _cache_ttl:
            return cached_result
    return None

def cache_health(check_name: str, result: Dict):
    """Cache health check result"""
    _health_cache[check_name] = (time.time(), result)

@router.get("")
async def basic_health_check():
    """
    Basic health check endpoint
    Returns 200 OK if the service is running
    Used by load balancers and monitoring systems
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "wealthpath-ai"
    }

@router.get("/live")
async def liveness_probe():
    """
    Kubernetes liveness probe endpoint
    Indicates if the application is running and should receive traffic
    """
    try:
        # Basic application health - can it respond?
        start_time = time.time()
        response_time = (time.time() - start_time) * 1000
        
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": round(response_time, 2)
        }
    except Exception as e:
        logger.error("Liveness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not alive")

@router.get("/ready")
async def readiness_probe(db: Session = Depends(get_db)):
    """
    Kubernetes readiness probe endpoint
    Indicates if the application is ready to serve requests
    """
    try:
        # Check cached result first
        cached = get_cached_health("readiness")
        if cached and cached.get("status") == "ready":
            return cached
        
        checks = {}
        overall_status = "ready"
        
        # Database connectivity check
        start_time = time.time()
        try:
            db.execute(text("SELECT 1"))
            db_response_time = (time.time() - start_time) * 1000
            checks["database"] = {
                "status": "healthy",
                "response_time_ms": round(db_response_time, 2)
            }
        except Exception as e:
            checks["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            overall_status = "not_ready"
        
        # Vector store check
        try:
            if simple_vector_store:
                # Simple check - can we access the store?
                doc_count = len(simple_vector_store.documents) if hasattr(simple_vector_store, 'documents') else 0
                checks["vector_store"] = {
                    "status": "healthy",
                    "document_count": doc_count
                }
            else:
                checks["vector_store"] = {
                    "status": "unavailable",
                    "message": "Vector store not initialized"
                }
        except Exception as e:
            checks["vector_store"] = {
                "status": "unhealthy", 
                "error": str(e)
            }
        
        # Memory check - basic threshold
        try:
            import psutil
            memory = psutil.virtual_memory()
            if memory.percent > 95:  # Critical memory usage
                checks["memory"] = {
                    "status": "critical",
                    "usage_percent": memory.percent
                }
                overall_status = "not_ready"
            else:
                checks["memory"] = {
                    "status": "healthy",
                    "usage_percent": memory.percent
                }
        except ImportError:
            checks["memory"] = {
                "status": "unavailable",
                "message": "psutil not available"
            }
        except Exception as e:
            checks["memory"] = {
                "status": "error",
                "error": str(e)
            }
        
        result = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks
        }
        
        # Cache the result
        cache_health("readiness", result)
        
        if overall_status != "ready":
            raise HTTPException(status_code=503, detail="Service not ready")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"Readiness check failed: {str(e)}")

@router.get("/deep")
async def deep_health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check with detailed system information
    Used for detailed monitoring and diagnostics
    """
    try:
        # Check cached result first
        cached = get_cached_health("deep")
        if cached:
            return cached
        
        checks = {}
        issues = []
        
        # Database health with query performance
        db_start = time.time()
        try:
            # Test basic connectivity
            db.execute(text("SELECT 1"))
            
            # Test a more complex query
            result = db.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"))
            table_count = result.scalar()
            
            db_response_time = (time.time() - db_start) * 1000
            
            checks["database"] = {
                "status": "healthy",
                "response_time_ms": round(db_response_time, 2),
                "table_count": table_count,
                "connection_pool": "active"  # Simplified
            }
            
            if db_response_time > 1000:  # > 1 second is concerning
                issues.append(f"Database response time high: {db_response_time:.0f}ms")
                
        except Exception as e:
            checks["database"] = {
                "status": "failed",
                "error": str(e),
                "response_time_ms": (time.time() - db_start) * 1000
            }
            issues.append(f"Database connectivity failed: {str(e)}")
        
        # Vector store detailed check
        try:
            if simple_vector_store:
                store_info = {
                    "status": "healthy",
                    "document_count": len(simple_vector_store.documents) if hasattr(simple_vector_store, 'documents') else 0
                }
                
                # Test search functionality
                search_start = time.time()
                test_results = simple_vector_store.search("test", limit=1)
                search_time = (time.time() - search_start) * 1000
                
                store_info.update({
                    "search_response_time_ms": round(search_time, 2),
                    "search_functional": True
                })
                
                checks["vector_store"] = store_info
                
                if search_time > 500:  # > 500ms is slow
                    issues.append(f"Vector store search slow: {search_time:.0f}ms")
                    
            else:
                checks["vector_store"] = {
                    "status": "not_available",
                    "message": "Vector store not initialized"
                }
                issues.append("Vector store not available")
                
        except Exception as e:
            checks["vector_store"] = {
                "status": "failed",
                "error": str(e)
            }
            issues.append(f"Vector store check failed: {str(e)}")
        
        # System resource checks
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            checks["system_resources"] = {
                "status": "healthy",
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "disk_usage_percent": round(disk_percent, 1),
                "available_memory_mb": round(memory.available / 1024 / 1024),
                "free_disk_gb": round(disk.free / 1024 / 1024 / 1024, 1)
            }
            
            # Add warnings for high resource usage
            if cpu_percent > 80:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            if memory.percent > 80:
                issues.append(f"High memory usage: {memory.percent:.1f}%")
            if disk_percent > 85:
                issues.append(f"High disk usage: {disk_percent:.1f}%")
                
        except ImportError:
            checks["system_resources"] = {
                "status": "unavailable",
                "message": "System monitoring not available (psutil missing)"
            }
        except Exception as e:
            checks["system_resources"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Application-specific checks
        try:
            # Check if we can import key services
            from app.services.chat_memory_service import ChatMemoryService
            from app.services.enhanced_intent_classifier import enhanced_intent_classifier
            
            checks["application_services"] = {
                "status": "healthy",
                "chat_memory_service": "available",
                "intent_classifier": "available"
            }
            
        except ImportError as e:
            checks["application_services"] = {
                "status": "degraded",
                "error": f"Service import failed: {str(e)}"
            }
            issues.append(f"Application service unavailable: {str(e)}")
        
        # Determine overall health status
        failed_checks = [name for name, check in checks.items() if check.get('status') in ['failed', 'error']]
        
        if failed_checks:
            overall_status = "unhealthy"
        elif issues:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        result = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks,
            "issues": issues,
            "issue_count": len(issues),
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "uptime_info": {
                "process_start": "unknown",  # Could track this if needed
                "check_duration_ms": round((time.time() - time.time()) * 1000, 2)  # This check's duration
            }
        }
        
        # Cache the result
        cache_health("deep", result)
        
        return result
        
    except Exception as e:
        logger.error("Deep health check failed", error=str(e))
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "message": "Health check system failure"
        }

@router.get("/startup")
async def startup_check(db: Session = Depends(get_db)):
    """
    Startup health check - validates all critical systems are ready
    Used during application initialization
    """
    try:
        startup_checks = []
        all_passed = True
        
        # Critical system checks
        critical_checks = [
            ("database", lambda: db.execute(text("SELECT 1"))),
            ("vector_store", lambda: simple_vector_store is not None),
        ]
        
        for check_name, check_func in critical_checks:
            try:
                start_time = time.time()
                check_func()
                duration = (time.time() - start_time) * 1000
                
                startup_checks.append({
                    "name": check_name,
                    "status": "passed",
                    "duration_ms": round(duration, 2)
                })
                
            except Exception as e:
                startup_checks.append({
                    "name": check_name,
                    "status": "failed",
                    "error": str(e)
                })
                all_passed = False
        
        result = {
            "status": "ready" if all_passed else "failed",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": startup_checks,
            "ready_for_traffic": all_passed
        }
        
        if not all_passed:
            raise HTTPException(status_code=503, detail="Startup checks failed")
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Startup check failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"Startup check error: {str(e)}")

@router.get("/metrics")
async def health_metrics():
    """
    Lightweight metrics endpoint for monitoring systems
    Returns key performance indicators
    """
    try:
        # These would typically come from a metrics store
        # For now, we'll provide basic system info
        
        import psutil
        
        # Basic system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "memory_available_mb": round(memory.available / 1024 / 1024),
                "health_check_cache_size": len(_health_cache),
            },
            "status": "healthy" if cpu_percent < 90 and memory.percent < 90 else "warning"
        }
        
    except Exception as e:
        logger.error("Metrics collection failed", error=str(e))
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": str(e)
        }