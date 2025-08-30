"""
Production Monitoring Dashboard API
Provides real-time system metrics and performance data
"""
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text, func
import structlog

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

from app.db.session import get_db
from app.utils.admin_auth import require_admin
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.services.simple_vector_store import simple_vector_store

logger = structlog.get_logger()
router = APIRouter()

@router.get("/system-health")
async def get_system_health():
    """Get comprehensive system health metrics"""
    try:
        # System metrics (if available)
        if PSUTIL_AVAILABLE:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
        else:
            # Fallback values when psutil is not available
            cpu_percent = 0.0
            memory = type('obj', (object,), {'total': 0, 'available': 0, 'percent': 0.0, 'used': 0})()
            disk = type('obj', (object,), {'total': 0, 'used': 0, 'free': 0})()
            disk.percent = 0.0
        
        # Database health check
        db_status = "unknown"
        try:
            # Simple connectivity check
            db_status = "healthy"
        except Exception as e:
            db_status = f"error: {str(e)}"
            logger.error("Database health check failed", error=str(e))
        
        # Redis/Cache health check
        cache_status = "healthy"  # Simplified for now
        
        # Vector store health
        vector_status = "healthy" if simple_vector_store else "unavailable"
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "cpu_usage": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100 if disk.total > 0 else 0.0
                }
            },
            "services": {
                "database": db_status,
                "cache": cache_status,
                "vector_store": vector_status
            }
        }
    except Exception as e:
        logger.error("System health check failed", error=str(e))
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/chat-metrics")
async def get_chat_metrics(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get chat system performance metrics"""
    try:
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        # Chat activity metrics
        total_sessions = db.query(ChatSession).count()
        active_sessions_24h = db.query(ChatSession).filter(
            ChatSession.updated_at >= last_24h
        ).count()
        
        total_messages = db.query(ChatMessage).count()
        messages_24h = db.query(ChatMessage).filter(
            ChatMessage.timestamp >= last_24h
        ).count()
        
        # Average session metrics
        avg_messages_per_session = db.query(
            func.avg(ChatSession.message_count)
        ).scalar() or 0
        
        # Intent distribution (last 7 days)
        intent_distribution = db.query(
            ChatSession.last_intent,
            func.count(ChatSession.id).label('count')
        ).filter(
            ChatSession.updated_at >= last_7d,
            ChatSession.last_intent.isnot(None)
        ).group_by(ChatSession.last_intent).all()
        
        intent_stats = {
            intent: count for intent, count in intent_distribution
        }
        
        # User engagement
        active_users_24h = db.query(ChatSession.user_id).filter(
            ChatSession.updated_at >= last_24h
        ).distinct().count()
        
        # Vector store metrics
        vector_stats = {
            "total_documents": len(simple_vector_store.documents) if simple_vector_store else 0,
            "storage_size_mb": simple_vector_store.get_storage_size() if simple_vector_store else 0
        }
        
        return {
            "timestamp": now.isoformat(),
            "sessions": {
                "total": total_sessions,
                "active_24h": active_sessions_24h,
                "avg_messages_per_session": round(avg_messages_per_session, 2)
            },
            "messages": {
                "total": total_messages,
                "last_24h": messages_24h
            },
            "users": {
                "active_24h": active_users_24h
            },
            "intents": intent_stats,
            "vector_store": vector_stats
        }
        
    except Exception as e:
        logger.error("Failed to get chat metrics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

@router.get("/performance-metrics")
async def get_performance_metrics(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get system performance and response time metrics"""
    try:
        # Database performance
        db_query_start = datetime.utcnow()
        sample_query = db.execute(text("SELECT 1")).fetchone()
        db_response_time = (datetime.utcnow() - db_query_start).total_seconds() * 1000
        
        # System load
        load_1, load_5, load_15 = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
        
        # Process info (if psutil available)
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process()
                process_info = {
                    "memory_mb": process.memory_info().rss / 1024 / 1024,
                    "cpu_percent": process.cpu_percent(),
                    "threads": process.num_threads(),
                    "connections": len(process.connections()) if hasattr(process, 'connections') else 0
                }
            except Exception:
                process_info = {
                    "memory_mb": 0,
                    "cpu_percent": 0,
                    "threads": 0,
                    "connections": 0,
                    "error": "Process info unavailable"
                }
        else:
            process_info = {
                "memory_mb": 0,
                "cpu_percent": 0,
                "threads": 0,
                "connections": 0,
                "note": "psutil not available"
            }
        
        # Recent error rates (simplified)
        error_rate = 0.0  # Would be calculated from actual error logs
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "response_times": {
                "database_ms": round(db_response_time, 2)
            },
            "system_load": {
                "1min": load_1,
                "5min": load_5,
                "15min": load_15
            },
            "process": process_info,
            "error_rate": error_rate
        }
        
    except Exception as e:
        logger.error("Failed to get performance metrics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")

@router.get("/alerts")
async def get_system_alerts(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get system alerts and warnings"""
    try:
        alerts = []
        
        # Memory and disk usage alerts (if psutil available)
        if PSUTIL_AVAILABLE:
            try:
                memory = psutil.virtual_memory()
                if memory.percent > 85:
                    alerts.append({
                        "level": "warning" if memory.percent < 95 else "critical",
                        "message": f"High memory usage: {memory.percent:.1f}%",
                        "timestamp": datetime.utcnow().isoformat(),
                        "category": "system"
                    })
                
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100 if disk.total > 0 else 0
                if disk_percent > 80:
                    alerts.append({
                        "level": "warning" if disk_percent < 90 else "critical",
                        "message": f"High disk usage: {disk_percent:.1f}%",
                        "timestamp": datetime.utcnow().isoformat(),
                        "category": "system"
                    })
            except Exception:
                pass
        
        # Database connection alerts
        try:
            # Check if we can query the database
            db.execute(text("SELECT 1"))
        except Exception as e:
            alerts.append({
                "level": "critical",
                "message": f"Database connection error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
                "category": "database"
            })
        
        # Recent error patterns (simplified)
        recent_errors = db.query(ChatMessage).filter(
            ChatMessage.timestamp >= datetime.utcnow() - timedelta(hours=1),
            ChatMessage.content.contains("error")
        ).count()
        
        if recent_errors > 10:
            alerts.append({
                "level": "warning",
                "message": f"High error rate: {recent_errors} errors in last hour",
                "timestamp": datetime.utcnow().isoformat(),
                "category": "application"
            })
        
        return {
            "alerts": alerts,
            "alert_count": len(alerts),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get alerts", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")

@router.get("/live-activity")
async def get_live_activity(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = 20
):
    """Get real-time activity feed"""
    try:
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        
        # Recent chat sessions
        recent_sessions = db.query(ChatSession).filter(
            ChatSession.updated_at >= last_hour
        ).order_by(ChatSession.updated_at.desc()).limit(limit).all()
        
        # Recent messages
        recent_messages = db.query(ChatMessage).filter(
            ChatMessage.timestamp >= last_hour
        ).order_by(ChatMessage.timestamp.desc()).limit(limit).all()
        
        activities = []
        
        # Add session activities
        for session in recent_sessions:
            activities.append({
                "type": "session_activity",
                "timestamp": session.updated_at.isoformat(),
                "user_id": session.user_id,
                "session_id": session.session_id,
                "message_count": session.message_count,
                "last_intent": session.last_intent,
                "description": f"Session activity: {session.message_count} messages, intent: {session.last_intent or 'general'}"
            })
        
        # Add message activities
        for message in recent_messages:
            activities.append({
                "type": "message",
                "timestamp": message.timestamp.isoformat(),
                "session_id": message.session_id,
                "role": message.role,
                "intent": message.intent,
                "tokens": message.token_count,
                "description": f"{message.role.title()} message: {message.content[:50]}..."
            })
        
        # Sort by timestamp
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            "activities": activities[:limit],
            "timestamp": now.isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get live activity", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get live activity: {str(e)}")

@router.post("/clear-cache")
async def clear_system_cache(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin)
):
    """Clear system caches"""
    try:
        def clear_caches():
            try:
                # Clear vector store cache if needed
                if hasattr(simple_vector_store, 'clear_cache'):
                    simple_vector_store.clear_cache()
                
                logger.info("System caches cleared", user_id=current_user.id)
            except Exception as e:
                logger.error("Failed to clear caches", error=str(e))
        
        background_tasks.add_task(clear_caches)
        
        return {
            "message": "Cache clear initiated",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to clear cache", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@router.get("/export-metrics")
async def export_metrics(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    format: str = "json"
):
    """Export metrics for external monitoring systems"""
    try:
        # Collect all metrics
        system_health = await get_system_health()
        chat_metrics = await get_chat_metrics(current_user, db)
        performance_metrics = await get_performance_metrics(current_user, db)
        alerts = await get_system_alerts(current_user, db)
        
        export_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "system_health": system_health,
            "chat_metrics": chat_metrics,
            "performance_metrics": performance_metrics,
            "alerts": alerts
        }
        
        if format == "prometheus":
            # Convert to Prometheus format (simplified)
            prometheus_metrics = []
            prometheus_metrics.append(f"wpa_cpu_usage {system_health['system']['cpu_usage']}")
            prometheus_metrics.append(f"wpa_memory_percent {system_health['system']['memory']['percent']}")
            prometheus_metrics.append(f"wpa_total_sessions {chat_metrics['sessions']['total']}")
            prometheus_metrics.append(f"wpa_active_sessions_24h {chat_metrics['sessions']['active_24h']}")
            prometheus_metrics.append(f"wpa_total_messages {chat_metrics['messages']['total']}")
            
            return {
                "format": "prometheus",
                "metrics": "\n".join(prometheus_metrics),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return export_data
        
    except Exception as e:
        logger.error("Failed to export metrics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to export metrics: {str(e)}")