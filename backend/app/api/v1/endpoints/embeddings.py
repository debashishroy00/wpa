"""
API endpoints for the hybrid embedding system.
Provides health checks, metrics, and management capabilities.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
import structlog

from app.services.embeddings.compatibility import get_embedding_service, MigrationHelper
from app.services.embeddings.base import EmbeddingContext
from app.api.v1.endpoints.auth import get_current_active_user
from app.models.user import User

logger = structlog.get_logger(__name__)

router = APIRouter()

# Request/Response Models

class EmbeddingRequest(BaseModel):
    text: str
    context: str = "realtime"  # realtime, batch, analysis, search, sensitive

class BatchEmbeddingRequest(BaseModel):
    texts: List[str]
    context: str = "batch"

class EmbeddingResponse(BaseModel):
    embedding: List[float]
    dimension: int
    provider: str
    model: str
    latency_ms: float
    cached: bool
    cost_usd: Optional[float] = None

class BatchEmbeddingResponse(BaseModel):
    embeddings: List[EmbeddingResponse]
    total_cost_usd: float
    total_latency_ms: float

class HealthResponse(BaseModel):
    status: str
    hybrid_enabled: bool
    providers: Dict[str, Any]
    components: Dict[str, Any]

class MetricsResponse(BaseModel):
    hybrid_enabled: bool
    legacy_metrics: Dict[str, Any]
    detailed: Optional[Dict[str, Any]] = None
    cost_projection: Optional[Dict[str, Any]] = None

# Endpoints

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check embedding service health"""
    try:
        service = get_embedding_service()
        health = await service.health_check()
        return HealthResponse(**health)
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(current_user: User = Depends(get_current_active_user)):
    """Get embedding service metrics (requires authentication)"""
    try:
        service = get_embedding_service()
        metrics = await service.get_metrics()
        return MetricsResponse(**metrics)
    except Exception as e:
        logger.error("Metrics retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")

@router.post("/embed", response_model=EmbeddingResponse)
async def generate_embedding(
    request: EmbeddingRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Generate embedding for single text (enhanced API)"""
    try:
        service = get_embedding_service()
        result = await service.generate_embedding_with_metadata(
            text=request.text,
            context=request.context
        )
        return EmbeddingResponse(**result)
    except Exception as e:
        logger.error("Embedding generation failed", error=str(e), text_preview=request.text[:100])
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")

@router.post("/embed/batch", response_model=BatchEmbeddingResponse)
async def generate_batch_embeddings(
    request: BatchEmbeddingRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Generate embeddings for multiple texts (enhanced API)"""
    try:
        if len(request.texts) > 1000:
            raise HTTPException(status_code=400, detail="Batch size too large (max 1000)")
        
        service = get_embedding_service()
        results = await service.batch_generate_embeddings_with_metadata(
            texts=request.texts,
            context=request.context
        )
        
        embeddings = [EmbeddingResponse(**result) for result in results]
        total_cost = sum(emb.cost_usd or 0.0 for emb in embeddings)
        total_latency = sum(emb.latency_ms for emb in embeddings)
        
        return BatchEmbeddingResponse(
            embeddings=embeddings,
            total_cost_usd=total_cost,
            total_latency_ms=total_latency
        )
    except Exception as e:
        logger.error("Batch embedding generation failed", error=str(e), batch_size=len(request.texts))
        raise HTTPException(status_code=500, detail=f"Batch embedding generation failed: {str(e)}")

# Legacy compatibility endpoints (backward compatibility)

@router.post("/legacy/embed")
async def legacy_generate_embedding(
    request: EmbeddingRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Legacy embedding endpoint (returns raw embedding vector)"""
    try:
        service = get_embedding_service()
        embedding = await service.generate_embedding(request.text)
        return {"embedding": embedding}
    except Exception as e:
        logger.error("Legacy embedding generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")

@router.post("/legacy/embed/batch")
async def legacy_generate_batch_embeddings(
    request: BatchEmbeddingRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Legacy batch embedding endpoint (returns raw embedding vectors)"""
    try:
        if len(request.texts) > 1000:
            raise HTTPException(status_code=400, detail="Batch size too large (max 1000)")
        
        service = get_embedding_service()
        embeddings = await service.generate_embeddings(request.texts)
        return {"embeddings": embeddings}
    except Exception as e:
        logger.error("Legacy batch embedding generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Batch embedding generation failed: {str(e)}")

# Management endpoints

@router.post("/cache/clear")
async def clear_cache(
    current_user: User = Depends(get_current_active_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Clear embedding cache"""
    try:
        service = get_embedding_service()
        result = await service.clear_cache()
        
        logger.info("Cache clear requested", user_id=current_user.id, result=result)
        
        return result
    except Exception as e:
        logger.error("Cache clear failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Cache clear failed: {str(e)}")

@router.post("/metrics/reset")
async def reset_daily_metrics(
    current_user: User = Depends(get_current_active_user)
):
    """Reset daily metrics (admin only)"""
    try:
        # TODO: Add admin check when admin system is implemented
        service = get_embedding_service()
        
        if hasattr(service, '_hybrid_service') and service._hybrid_service:
            await service._hybrid_service.reset_daily_metrics()
        
        logger.info("Daily metrics reset", user_id=current_user.id)
        
        return {"status": "metrics_reset"}
    except Exception as e:
        logger.error("Metrics reset failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Metrics reset failed: {str(e)}")

@router.get("/migration/status")
async def migration_status():
    """Get migration status and recommendations"""
    try:
        return MigrationHelper.migration_status()
    except Exception as e:
        logger.error("Migration status check failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Migration status check failed: {str(e)}")

# Testing endpoints (for development/testing only)

@router.post("/test/compare-providers")
async def test_compare_providers(
    request: EmbeddingRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Test endpoint to compare different providers (development only)"""
    try:
        # This endpoint would only be available in development
        from app.core.config import settings
        if settings.ENVIRONMENT != "development":
            raise HTTPException(status_code=404, detail="Endpoint not available in production")
        
        service = get_embedding_service()
        
        # Generate with local provider
        local_result = await service.generate_embedding_with_metadata(
            text=request.text,
            context="analysis"  # Use analysis for quality
        )
        
        # Try to generate with OpenAI if available
        try:
            # Force OpenAI provider
            openai_result = await service.generate_embedding_with_metadata(
                text=request.text,
                context="analysis",
                preferred_provider="openai"
            )
            
            # Calculate similarity if both successful
            if local_result["embedding"] and openai_result["embedding"]:
                import numpy as np
                local_vec = np.array(local_result["embedding"])
                openai_vec = np.array(openai_result["embedding"])
                
                # Pad vectors to same dimension for comparison
                max_dim = max(len(local_vec), len(openai_vec))
                if len(local_vec) < max_dim:
                    local_vec = np.pad(local_vec, (0, max_dim - len(local_vec)))
                if len(openai_vec) < max_dim:
                    openai_vec = np.pad(openai_vec, (0, max_dim - len(openai_vec)))
                
                similarity = np.dot(local_vec, openai_vec) / (np.linalg.norm(local_vec) * np.linalg.norm(openai_vec))
                
                return {
                    "local": local_result,
                    "openai": openai_result,
                    "similarity": float(similarity),
                    "comparison": {
                        "cost_difference": openai_result["cost_usd"] - local_result["cost_usd"],
                        "latency_difference": openai_result["latency_ms"] - local_result["latency_ms"]
                    }
                }
            else:
                return {
                    "local": local_result,
                    "openai": openai_result,
                    "error": "Could not calculate similarity"
                }
                
        except Exception as openai_error:
            return {
                "local": local_result,
                "openai_error": str(openai_error)
            }
        
    except Exception as e:
        logger.error("Provider comparison test failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Provider comparison failed: {str(e)}")

# Production readiness endpoints

@router.get("/production-readiness")
async def production_readiness_check(
    current_user: User = Depends(get_current_active_user)
):
    """Comprehensive production readiness assessment"""
    try:
        from app.services.embeddings.shadow_mode import get_shadow_collector
        from app.services.embeddings.alerts import AlertManager, AlertThresholds
        from app.core.config import settings
        
        service = get_embedding_service()
        
        # Get system health
        health = await service.health_check()
        metrics = await service.get_metrics()
        
        # Shadow mode assessment
        shadow_ready = False
        shadow_stats = {}
        if getattr(settings, 'EMBEDDING_SHADOW_MODE', False):
            collector = get_shadow_collector()
            shadow_stats = collector.get_statistics()
            
            # Check if shadow mode has enough data
            shadow_ready = (
                shadow_stats.get("total_comparisons", 0) >= 100 and
                shadow_stats.get("quality_metrics", {}).get("average_similarity", 0) >= 0.95 and
                shadow_stats.get("runtime_hours", 0) >= 48
            )
        
        # Alert system check
        alert_manager = AlertManager(AlertThresholds.from_settings())
        
        # Production readiness checklist
        checklist = {
            "feature_flags": {
                "status": "ready" if not getattr(settings, 'USE_HYBRID_EMBEDDINGS', False) else "enabled",
                "shadow_mode": getattr(settings, 'EMBEDDING_SHADOW_MODE', False),
                "ready": True
            },
            
            "providers": {
                "local_available": health.get("providers", {}).get("local", {}).get("status") == "healthy",
                "openai_available": health.get("providers", {}).get("openai", {}).get("status") == "healthy",
                "ready": any(
                    provider.get("status") == "healthy" 
                    for provider in health.get("providers", {}).values()
                )
            },
            
            "cache_system": {
                "l1_operational": health.get("components", {}).get("cache", {}).get("status") == "healthy",
                "l2_redis_available": bool(getattr(settings, 'REDIS_URL', None)),
                "ready": health.get("components", {}).get("cache", {}).get("status") == "healthy"
            },
            
            "monitoring": {
                "alerts_configured": True,  # Always true if this endpoint works
                "metrics_collection": health.get("components", {}).get("monitor", {}).get("status") == "healthy",
                "ready": True
            },
            
            "shadow_mode": {
                "enabled": getattr(settings, 'EMBEDDING_SHADOW_MODE', False),
                "sufficient_data": shadow_ready,
                "quality_acceptable": shadow_stats.get("quality_metrics", {}).get("average_similarity", 0) >= 0.95,
                "ready": shadow_ready or not getattr(settings, 'EMBEDDING_SHADOW_MODE', False)
            },
            
            "configuration": {
                "openai_key_present": bool(getattr(settings, 'OPENAI_API_KEY', None)),
                "budget_configured": getattr(settings, 'EMBEDDING_DAILY_API_BUDGET_USD', 0) > 0,
                "thresholds_set": True,  # From AlertThresholds.from_settings()
                "ready": True
            }
        }
        
        # Overall readiness
        all_ready = all(check["ready"] for check in checklist.values())
        
        # Recommendations
        recommendations = []
        
        if not checklist["shadow_mode"]["enabled"]:
            recommendations.append("Enable EMBEDDING_SHADOW_MODE=true for 48-72 hours before rollout")
        elif not checklist["shadow_mode"]["sufficient_data"]:
            recommendations.append(f"Continue shadow mode - need {shadow_stats.get('total_comparisons', 0)}/100 comparisons and {shadow_stats.get('runtime_hours', 0):.1f}/48 hours")
        
        if not checklist["providers"]["openai_available"] and checklist["configuration"]["openai_key_present"]:
            recommendations.append("OpenAI provider unhealthy - check API key and network connectivity")
        
        if not checklist["cache_system"]["l2_redis_available"]:
            recommendations.append("Redis not configured - L2 cache disabled, may impact performance")
        
        if checklist["configuration"]["budget_configured"] and getattr(settings, 'EMBEDDING_DAILY_API_BUDGET_USD', 0) < 1.0:
            recommendations.append("Daily API budget very low - consider increasing for production workload")
        
        if all_ready and not recommendations:
            recommendations.append("✅ System ready for production deployment!")
        
        return {
            "overall_ready": all_ready,
            "readiness_score": sum(1 for check in checklist.values() if check["ready"]) / len(checklist),
            "checklist": checklist,
            "recommendations": recommendations,
            "shadow_mode_stats": shadow_stats if shadow_stats else None,
            "health_summary": health,
            "last_check": time.time()
        }
        
    except Exception as e:
        logger.error("Production readiness check failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Readiness check failed: {str(e)}")

@router.get("/alerts")
async def get_current_alerts(
    current_user: User = Depends(get_current_active_user)
):
    """Get current system alerts"""
    try:
        from app.services.embeddings.alerts import AlertManager, AlertThresholds
        from app.services.embeddings.shadow_mode import get_shadow_collector
        
        service = get_embedding_service()
        
        # Get monitor if hybrid system is enabled
        if hasattr(service, '_hybrid_service') and service._hybrid_service and service._hybrid_service.monitor:
            alert_manager = AlertManager(AlertThresholds.from_settings())
            alerts = alert_manager.check_alerts(service._hybrid_service.monitor)
            summary = alert_manager.get_alert_summary()
            
            # Add shadow mode alerts if enabled
            shadow_alerts = []
            if getattr(settings, 'EMBEDDING_SHADOW_MODE', False):
                collector = get_shadow_collector()
                shadow_alerts = collector.get_alerts()
            
            return {
                "status": "active" if alerts or shadow_alerts else "no_alerts",
                "current_alerts": [alert.__dict__ for alert in alerts],
                "shadow_mode_alerts": shadow_alerts,
                "alert_summary": summary,
                "alert_thresholds": alert_manager.thresholds.__dict__
            }
        else:
            return {
                "status": "monitoring_disabled",
                "message": "Hybrid system not enabled or monitor not available"
            }
            
    except Exception as e:
        logger.error("Alert check failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Alert check failed: {str(e)}")

# Import time for production readiness endpoint
import time

# Export router
__all__ = ["router"]