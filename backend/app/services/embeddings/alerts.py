"""
Production monitoring alerts and thresholds for hybrid embedding system.
Proactive monitoring with configurable alerting rules.
"""

import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import structlog

from .monitoring import EmbeddingMonitor
from .shadow_mode import get_shadow_collector
from app.core.config import settings

logger = structlog.get_logger(__name__)

class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertType(str, Enum):
    """Types of alerts"""
    API_BUDGET = "api_budget"
    CACHE_EFFICIENCY = "cache_efficiency"  
    LATENCY_DEGRADATION = "latency_degradation"
    CIRCUIT_BREAKER = "circuit_breaker"
    QUALITY_DEGRADATION = "quality_degradation"
    PROVIDER_HEALTH = "provider_health"
    COST_SPIKE = "cost_spike"
    ERROR_RATE = "error_rate"

@dataclass
class Alert:
    """Alert message"""
    level: AlertLevel
    type: AlertType
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None
    timestamp: float = None
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.context is None:
            self.context = {}

@dataclass
class AlertThresholds:
    """Configurable alert thresholds"""
    # Budget alerts
    api_budget_warning: float = 0.8      # 80% of daily budget
    api_budget_critical: float = 0.95    # 95% of daily budget
    
    # Cache efficiency
    cache_hit_rate_warning: float = 0.7  # 70% hit rate
    cache_hit_rate_error: float = 0.5    # 50% hit rate
    
    # Latency thresholds  
    p95_latency_warning: float = 500     # 500ms P95
    p95_latency_error: float = 1000      # 1000ms P95
    
    # Quality thresholds
    similarity_warning: float = 0.95     # 95% similarity
    similarity_error: float = 0.9        # 90% similarity
    
    # Error rates
    error_rate_warning: float = 0.05     # 5% error rate
    error_rate_error: float = 0.1        # 10% error rate
    
    # Cost spikes
    cost_spike_multiplier: float = 2.0   # 2x normal cost
    
    @classmethod
    def from_settings(cls) -> 'AlertThresholds':
        """Create thresholds from settings"""
        return cls(
            api_budget_warning=getattr(settings, 'ALERT_API_BUDGET_WARNING', 0.8),
            api_budget_critical=getattr(settings, 'ALERT_API_BUDGET_CRITICAL', 0.95),
            cache_hit_rate_warning=getattr(settings, 'ALERT_CACHE_HIT_WARNING', 0.7),
            cache_hit_rate_error=getattr(settings, 'ALERT_CACHE_HIT_ERROR', 0.5),
            p95_latency_warning=getattr(settings, 'ALERT_P95_LATENCY_WARNING', 500),
            p95_latency_error=getattr(settings, 'ALERT_P95_LATENCY_ERROR', 1000),
            similarity_warning=getattr(settings, 'ALERT_SIMILARITY_WARNING', 0.95),
            similarity_error=getattr(settings, 'ALERT_SIMILARITY_ERROR', 0.9),
            error_rate_warning=getattr(settings, 'ALERT_ERROR_RATE_WARNING', 0.05),
            error_rate_error=getattr(settings, 'ALERT_ERROR_RATE_ERROR', 0.1)
        )

class AlertManager:
    """Manages alert generation and delivery"""
    
    def __init__(self, thresholds: AlertThresholds = None):
        self.thresholds = thresholds or AlertThresholds.from_settings()
        self.recent_alerts: List[Alert] = []
        self.alert_handlers: List[Callable[[Alert], None]] = []
        self.last_check = time.time()
        
        # Alert suppression (prevent spam)
        self.alert_cooldown = {}  # type -> last_alert_time
        self.cooldown_seconds = 300  # 5 minutes between similar alerts
        
        logger.info("Alert manager initialized", thresholds=self.thresholds)
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add alert handler (e.g., email, Slack, webhook)"""
        self.alert_handlers.append(handler)
    
    def check_alerts(self, monitor: EmbeddingMonitor) -> List[Alert]:
        """Check all alert conditions and return new alerts"""
        alerts = []
        
        try:
            # Get current metrics
            report = monitor.get_performance_report()
            health = monitor.get_health_summary()
            
            # Check API budget
            alerts.extend(self._check_api_budget(report))
            
            # Check cache efficiency
            alerts.extend(self._check_cache_efficiency(report))
            
            # Check latency
            alerts.extend(self._check_latency(report))
            
            # Check provider health
            alerts.extend(self._check_provider_health(health))
            
            # Check error rates
            alerts.extend(self._check_error_rates(report))
            
            # Check shadow mode (if enabled)
            if getattr(settings, 'EMBEDDING_SHADOW_MODE', False):
                alerts.extend(self._check_shadow_mode())
            
            # Filter out suppressed alerts
            filtered_alerts = self._filter_suppressed_alerts(alerts)
            
            # Send alerts
            for alert in filtered_alerts:
                self._send_alert(alert)
                self.recent_alerts.append(alert)
            
            # Keep only recent alerts
            cutoff_time = time.time() - 24 * 3600  # 24 hours
            self.recent_alerts = [a for a in self.recent_alerts if a.timestamp > cutoff_time]
            
            self.last_check = time.time()
            
            return filtered_alerts
            
        except Exception as e:
            logger.error("Alert check failed", error=str(e))
            return []
    
    def _check_api_budget(self, report: Dict[str, Any]) -> List[Alert]:
        """Check API budget utilization"""
        alerts = []
        costs = report.get("costs", {})
        
        # Calculate budget utilization
        daily_budget = getattr(settings, 'EMBEDDING_DAILY_API_BUDGET_USD', 10.0)
        current_cost = costs.get("total_cost_usd", 0.0)
        utilization = current_cost / daily_budget if daily_budget > 0 else 0
        
        if utilization >= self.thresholds.api_budget_critical:
            alerts.append(Alert(
                level=AlertLevel.CRITICAL,
                type=AlertType.API_BUDGET,
                message=f"API budget critically high: {utilization:.1%} of daily budget used",
                value=utilization,
                threshold=self.thresholds.api_budget_critical,
                context={"current_cost": current_cost, "daily_budget": daily_budget}
            ))
        elif utilization >= self.thresholds.api_budget_warning:
            alerts.append(Alert(
                level=AlertLevel.WARNING,
                type=AlertType.API_BUDGET,
                message=f"API budget high: {utilization:.1%} of daily budget used",
                value=utilization,
                threshold=self.thresholds.api_budget_warning,
                context={"current_cost": current_cost, "daily_budget": daily_budget}
            ))
        
        return alerts
    
    def _check_cache_efficiency(self, report: Dict[str, Any]) -> List[Alert]:
        """Check cache hit rates"""
        alerts = []
        cache = report.get("cache", {})
        hit_rate = cache.get("hit_rate", 1.0)
        
        if hit_rate < self.thresholds.cache_hit_rate_error:
            alerts.append(Alert(
                level=AlertLevel.ERROR,
                type=AlertType.CACHE_EFFICIENCY,
                message=f"Cache hit rate very low: {hit_rate:.1%}",
                value=hit_rate,
                threshold=self.thresholds.cache_hit_rate_error
            ))
        elif hit_rate < self.thresholds.cache_hit_rate_warning:
            alerts.append(Alert(
                level=AlertLevel.WARNING,
                type=AlertType.CACHE_EFFICIENCY,
                message=f"Cache hit rate below target: {hit_rate:.1%}",
                value=hit_rate,
                threshold=self.thresholds.cache_hit_rate_warning
            ))
        
        return alerts
    
    def _check_latency(self, report: Dict[str, Any]) -> List[Alert]:
        """Check latency metrics"""
        alerts = []
        
        for provider, perf in report.get("performance", {}).items():
            p95_latency = perf.get("p95_latency_ms", 0)
            
            if p95_latency > self.thresholds.p95_latency_error:
                alerts.append(Alert(
                    level=AlertLevel.ERROR,
                    type=AlertType.LATENCY_DEGRADATION,
                    message=f"{provider} P95 latency high: {p95_latency:.0f}ms",
                    value=p95_latency,
                    threshold=self.thresholds.p95_latency_error,
                    context={"provider": provider}
                ))
            elif p95_latency > self.thresholds.p95_latency_warning:
                alerts.append(Alert(
                    level=AlertLevel.WARNING,
                    type=AlertType.LATENCY_DEGRADATION,
                    message=f"{provider} P95 latency elevated: {p95_latency:.0f}ms",
                    value=p95_latency,
                    threshold=self.thresholds.p95_latency_warning,
                    context={"provider": provider}
                ))
        
        return alerts
    
    def _check_provider_health(self, health: Dict[str, Any]) -> List[Alert]:
        """Check provider health status"""
        alerts = []
        
        for provider, provider_health in health.get("providers", {}).items():
            status = provider_health.get("status", "unknown")
            
            if status == "unhealthy":
                alerts.append(Alert(
                    level=AlertLevel.CRITICAL,
                    type=AlertType.PROVIDER_HEALTH,
                    message=f"{provider} provider unhealthy",
                    context={"provider": provider, "health": provider_health}
                ))
            elif status != "healthy":
                alerts.append(Alert(
                    level=AlertLevel.WARNING,
                    type=AlertType.PROVIDER_HEALTH,
                    message=f"{provider} provider status: {status}",
                    context={"provider": provider, "health": provider_health}
                ))
        
        # Check circuit breaker status
        for provider, provider_health in health.get("providers", {}).items():
            cb_state = provider_health.get("circuit_breaker", {}).get("state")
            if cb_state == "open":
                alerts.append(Alert(
                    level=AlertLevel.ERROR,
                    type=AlertType.CIRCUIT_BREAKER,
                    message=f"{provider} circuit breaker opened",
                    context={"provider": provider}
                ))
        
        return alerts
    
    def _check_error_rates(self, report: Dict[str, Any]) -> List[Alert]:
        """Check error rates by provider"""
        alerts = []
        
        # Calculate overall error rate
        total_requests = 0
        total_errors = 0
        
        for provider, perf in report.get("performance", {}).items():
            requests = perf.get("total_requests", 0)
            total_requests += requests
        
        errors = report.get("errors", {})
        for provider, error_count in errors.get("total_by_provider", {}).items():
            total_errors += error_count
        
        if total_requests > 10:  # Need minimum sample size
            error_rate = total_errors / total_requests
            
            if error_rate > self.thresholds.error_rate_error:
                alerts.append(Alert(
                    level=AlertLevel.ERROR,
                    type=AlertType.ERROR_RATE,
                    message=f"High error rate: {error_rate:.1%}",
                    value=error_rate,
                    threshold=self.thresholds.error_rate_error
                ))
            elif error_rate > self.thresholds.error_rate_warning:
                alerts.append(Alert(
                    level=AlertLevel.WARNING,
                    type=AlertType.ERROR_RATE,
                    message=f"Elevated error rate: {error_rate:.1%}",
                    value=error_rate,
                    threshold=self.thresholds.error_rate_warning
                ))
        
        return alerts
    
    def _check_shadow_mode(self) -> List[Alert]:
        """Check shadow mode metrics"""
        alerts = []
        
        try:
            collector = get_shadow_collector()
            stats = collector.get_statistics()
            
            if stats.get("status") != "active":
                return alerts
            
            # Check quality metrics
            quality = stats.get("quality_metrics", {})
            avg_similarity = quality.get("average_similarity", 1.0)
            
            if avg_similarity < self.thresholds.similarity_error:
                alerts.append(Alert(
                    level=AlertLevel.ERROR,
                    type=AlertType.QUALITY_DEGRADATION,
                    message=f"Shadow mode: Low similarity {avg_similarity:.3f}",
                    value=avg_similarity,
                    threshold=self.thresholds.similarity_error
                ))
            elif avg_similarity < self.thresholds.similarity_warning:
                alerts.append(Alert(
                    level=AlertLevel.WARNING,
                    type=AlertType.QUALITY_DEGRADATION,
                    message=f"Shadow mode: Below target similarity {avg_similarity:.3f}",
                    value=avg_similarity,
                    threshold=self.thresholds.similarity_warning
                ))
            
        except Exception as e:
            logger.error("Shadow mode alert check failed", error=str(e))
        
        return alerts
    
    def _filter_suppressed_alerts(self, alerts: List[Alert]) -> List[Alert]:
        """Filter out suppressed alerts based on cooldown"""
        filtered = []
        current_time = time.time()
        
        for alert in alerts:
            alert_key = f"{alert.type.value}_{alert.level.value}"
            last_alert_time = self.alert_cooldown.get(alert_key, 0)
            
            if current_time - last_alert_time > self.cooldown_seconds:
                filtered.append(alert)
                self.alert_cooldown[alert_key] = current_time
            else:
                logger.debug("Alert suppressed due to cooldown", alert_type=alert.type.value)
        
        return filtered
    
    def _send_alert(self, alert: Alert):
        """Send alert to all registered handlers"""
        # Log the alert
        log_func = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,  
            AlertLevel.ERROR: logger.error,
            AlertLevel.CRITICAL: logger.critical
        }.get(alert.level, logger.info)
        
        log_func(
            "Embedding system alert",
            level=alert.level.value,
            type=alert.type.value,
            message=alert.message,
            value=alert.value,
            threshold=alert.threshold
        )
        
        # Send to handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error("Alert handler failed", handler=str(handler), error=str(e))
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of recent alerts"""
        if not self.recent_alerts:
            return {"status": "no_alerts", "count": 0}
        
        # Group by level and type
        by_level = {}
        by_type = {}
        
        for alert in self.recent_alerts:
            by_level[alert.level.value] = by_level.get(alert.level.value, 0) + 1
            by_type[alert.type.value] = by_type.get(alert.type.value, 0) + 1
        
        return {
            "status": "active",
            "count": len(self.recent_alerts),
            "by_level": by_level,
            "by_type": by_type,
            "latest": self.recent_alerts[-1].__dict__ if self.recent_alerts else None,
            "last_check": self.last_check
        }

# Default alert handlers

def console_alert_handler(alert: Alert):
    """Simple console alert handler"""
    print(f"🚨 [{alert.level.value.upper()}] {alert.type.value}: {alert.message}")

def webhook_alert_handler(webhook_url: str):
    """Create webhook alert handler"""
    def handler(alert: Alert):
        import httpx
        try:
            payload = {
                "level": alert.level.value,
                "type": alert.type.value,
                "message": alert.message,
                "timestamp": alert.timestamp,
                "value": alert.value,
                "threshold": alert.threshold,
                "context": alert.context
            }
            # In production, you'd use async client
            response = httpx.post(webhook_url, json=payload, timeout=5.0)
            response.raise_for_status()
        except Exception as e:
            logger.error("Webhook alert failed", webhook_url=webhook_url, error=str(e))
    
    return handler