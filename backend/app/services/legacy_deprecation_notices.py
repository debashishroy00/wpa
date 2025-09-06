"""
Legacy Service Deprecation Notices
Centralized deprecation warnings for legacy services being replaced by modern architecture
"""

import logging
import warnings
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from functools import wraps
import inspect

logger = logging.getLogger(__name__)

class DeprecationLevel:
    """Deprecation severity levels"""
    INFO = "info"           # Service still works, replacement available
    WARNING = "warning"     # Service will be removed in future version
    DEPRECATED = "deprecated"  # Service should not be used, removal imminent
    REMOVED = "removed"     # Service has been removed

class LegacyServiceDeprecation:
    """Handles deprecation notices and migration guidance"""
    
    def __init__(self):
        self.deprecation_registry: Dict[str, Dict[str, Any]] = {}
        self.migration_log: Dict[str, datetime] = {}
        
    def register_deprecated_service(self,
                                  service_name: str,
                                  replacement_service: str,
                                  deprecation_level: str = DeprecationLevel.WARNING,
                                  removal_date: Optional[datetime] = None,
                                  migration_guide: Optional[str] = None,
                                  breaking_changes: Optional[List[str]] = None):
        """Register a service as deprecated with migration information"""
        
        self.deprecation_registry[service_name] = {
            'replacement_service': replacement_service,
            'deprecation_level': deprecation_level,
            'removal_date': removal_date or datetime.now() + timedelta(days=90),
            'migration_guide': migration_guide,
            'breaking_changes': breaking_changes or [],
            'registered_date': datetime.now()
        }
        
        logger.info(f"Registered deprecation for service: {service_name}")
    
    def emit_deprecation_warning(self, service_name: str, caller_info: Optional[str] = None):
        """Emit deprecation warning when legacy service is used"""
        
        if service_name not in self.deprecation_registry:
            return
        
        deprecation_info = self.deprecation_registry[service_name]
        level = deprecation_info['deprecation_level']
        replacement = deprecation_info['replacement_service']
        removal_date = deprecation_info['removal_date']
        
        # Create warning message
        message = f"""
🚨 DEPRECATED SERVICE USAGE 🚨
Service: {service_name}
Level: {level.upper()}
Replacement: {replacement}
Removal Date: {removal_date.strftime('%Y-%m-%d')}
"""
        
        if caller_info:
            message += f"Called from: {caller_info}\n"
        
        if deprecation_info['migration_guide']:
            message += f"Migration Guide: {deprecation_info['migration_guide']}\n"
        
        # Log based on severity
        if level == DeprecationLevel.REMOVED:
            logger.error(message)
            raise RuntimeError(f"Service {service_name} has been removed. Use {replacement} instead.")
        elif level == DeprecationLevel.DEPRECATED:
            logger.error(message)
        elif level == DeprecationLevel.WARNING:
            logger.warning(message)
        else:
            logger.info(message)
        
        # Track usage for metrics
        self.migration_log[service_name] = datetime.now()

def deprecated_service(replacement_service: str,
                      deprecation_level: str = DeprecationLevel.WARNING,
                      removal_date: Optional[datetime] = None,
                      migration_guide: Optional[str] = None,
                      breaking_changes: Optional[List[str]] = None):
    """Decorator to mark services/methods as deprecated"""
    
    def decorator(func):
        service_name = f"{func.__module__}.{func.__qualname__}"
        
        # Register the deprecation
        deprecation_manager.register_deprecated_service(
            service_name=service_name,
            replacement_service=replacement_service,
            deprecation_level=deprecation_level,
            removal_date=removal_date,
            migration_guide=migration_guide,
            breaking_changes=breaking_changes
        )
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get caller information
            frame = inspect.currentframe()
            caller_frame = frame.f_back
            caller_info = f"{caller_frame.f_code.co_filename}:{caller_frame.f_lineno}"
            
            # Emit deprecation warning
            deprecation_manager.emit_deprecation_warning(service_name, caller_info)
            
            # Call original function
            return func(*args, **kwargs)
        
        # Add deprecation metadata to function
        wrapper.__deprecated__ = True
        wrapper.__replacement__ = replacement_service
        wrapper.__deprecation_level__ = deprecation_level
        
        return wrapper
    
    return decorator

# Global deprecation manager instance
deprecation_manager = LegacyServiceDeprecation()

# Register known deprecated services
def register_legacy_services():
    """Register all known legacy services for deprecation tracking"""
    
    # Chat Services - Using existing insight_level instead
    deprecation_manager.register_deprecated_service(
        service_name="app.services.chat_intelligence_service",
        replacement_service="USE EXISTING insight_level parameter",
        deprecation_level=DeprecationLevel.WARNING,
        removal_date=datetime(2024, 6, 1),
        migration_guide="/docs/migration/use-insight-level.md",
        breaking_changes=[
            "Use existing insight_level parameter (detailed/balanced/concise)",
            "No need for separate personality service",
            "Response style controlled via LLM settings"
        ]
    )
    
    deprecation_manager.register_deprecated_service(
        service_name="app.services.prompt_builder_service",
        replacement_service="USE EXISTING insight_level parameter",
        deprecation_level=DeprecationLevel.WARNING,
        removal_date=datetime(2024, 6, 15),
        migration_guide="/docs/migration/use-insight-level.md",
        breaking_changes=[
            "Use existing insight_level parameter instead",
            "No need for complex prompt building",
            "Response style controlled via LLM settings"
        ]
    )
    
    # Alert/Monitoring Services
    deprecation_manager.register_deprecated_service(
        service_name="app.services.embeddings.alerts",
        replacement_service="app.services.modern.proactive_insights",
        deprecation_level=DeprecationLevel.WARNING,
        removal_date=datetime(2024, 7, 1),
        migration_guide="/docs/migration/proactive-insights.md",
        breaking_changes=[
            "ProactiveInsight dataclass replaces Alert class",
            "InsightType enum for better categorization",
            "Enhanced user-specific insight generation",
            "Automatic cooldown and deduplication"
        ]
    )
    
    # Calculation Services
    deprecation_manager.register_deprecated_service(
        service_name="app.services.comprehensive_financial_calculator",
        replacement_service="app.services.modern.interactive_calculations",
        deprecation_level=DeprecationLevel.INFO,
        removal_date=datetime(2024, 8, 1),
        migration_guide="/docs/migration/interactive-calculations.md",
        breaking_changes=[
            "CalculationType enum for better organization",
            "CalculationResult dataclass with visualization data",
            "Async calculation methods for better performance",
            "Built-in recommendation generation"
        ]
    )
    
    # Advisory Services
    deprecation_manager.register_deprecated_service(
        service_name="app.services.advisory_engine",
        replacement_service="app.services.modern.document_generation",
        deprecation_level=DeprecationLevel.INFO,
        removal_date=datetime(2024, 9, 1),
        migration_guide="/docs/migration/document-generation.md",
        breaking_changes=[
            "DocumentType enum for different report types",
            "Enhanced template system with CSS styling",
            "Multiple output formats (PDF, HTML, JSON, Email)",
            "Professional document metadata and versioning"
        ]
    )
    
    # Frontend Components - Corrected to work WITH LLM settings
    deprecation_manager.register_deprecated_service(
        service_name="frontend.src.components.modern.NotificationSystem",
        replacement_service="NONE - Not needed in chat interface",
        deprecation_level=DeprecationLevel.DEPRECATED,
        removal_date=datetime(2024, 6, 1),
        migration_guide="/docs/migration/chat-focus.md",
        breaking_changes=[
            "Financial insights belong in dedicated dashboard (Step 5)",
            "Chat interface focuses on conversational AI only",
            "No notification management needed in chat"
        ]
    )
    
    deprecation_manager.register_deprecated_service(
        service_name="frontend.src.components.modern.CelebrationSystem",
        replacement_service="NONE - Not needed in chat interface", 
        deprecation_level=DeprecationLevel.DEPRECATED,
        removal_date=datetime(2024, 6, 1),
        migration_guide="/docs/migration/chat-focus.md",
        breaking_changes=[
            "Visual celebrations not appropriate for chat interface",
            "Chat interface focuses on conversational AI only",
            "Milestone celebrations belong in dashboard views"
        ]
    )
    
    deprecation_manager.register_deprecated_service(
        service_name="frontend.src.components.modern.InteractiveCharts",
        replacement_service="NONE - Not needed in chat interface",
        deprecation_level=DeprecationLevel.DEPRECATED, 
        removal_date=datetime(2024, 6, 1),
        migration_guide="/docs/migration/chat-focus.md",
        breaking_changes=[
            "Charts and visualizations belong in dashboard steps (1-5)",
            "Chat interface focuses on conversational AI only",
            "Interactive financial tools belong in dedicated views"
        ]
    )
    
    deprecation_manager.register_deprecated_service(
        service_name="frontend.src.components.modern.AdvisorStyleSelector",
        replacement_service="USE EXISTING LLM Settings Response Depth",
        deprecation_level=DeprecationLevel.DEPRECATED,
        removal_date=datetime(2024, 6, 1),
        migration_guide="/docs/migration/use-llm-settings.md",
        breaking_changes=[
            "Response Depth in LLM Settings provides same functionality",
            "insight_level parameter (detailed/balanced/concise) controls style",
            "No need for duplicate advisor style selection"
        ]
    )
    
    deprecation_manager.register_deprecated_service(
        service_name="app.services.modern.advisor_personality",
        replacement_service="USE EXISTING insight_level parameter",
        deprecation_level=DeprecationLevel.DEPRECATED,
        removal_date=datetime(2024, 6, 1),
        migration_guide="/docs/migration/use-insight-level.md",
        breaking_changes=[
            "insight_level parameter already controls response style",
            "No need for separate personality service",
            "LLM Settings Response Depth provides user control"
        ]
    )

# Initialize on import
register_legacy_services()

def get_migration_status() -> Dict[str, Any]:
    """Get current migration status for all deprecated services"""
    
    status = {
        'total_deprecated_services': len(deprecation_manager.deprecation_registry),
        'services_by_level': {},
        'upcoming_removals': [],
        'recently_used_legacy': [],
        'migration_progress': {}
    }
    
    # Count by deprecation level
    for service_name, info in deprecation_manager.deprecation_registry.items():
        level = info['deprecation_level']
        if level not in status['services_by_level']:
            status['services_by_level'][level] = 0
        status['services_by_level'][level] += 1
    
    # Upcoming removals (within 30 days)
    cutoff_date = datetime.now() + timedelta(days=30)
    for service_name, info in deprecation_manager.deprecation_registry.items():
        if info['removal_date'] <= cutoff_date:
            status['upcoming_removals'].append({
                'service': service_name,
                'replacement': info['replacement_service'],
                'removal_date': info['removal_date'].isoformat(),
                'days_remaining': (info['removal_date'] - datetime.now()).days
            })
    
    # Recently used legacy services (within last 7 days)
    recent_cutoff = datetime.now() - timedelta(days=7)
    for service_name, last_used in deprecation_manager.migration_log.items():
        if last_used >= recent_cutoff:
            status['recently_used_legacy'].append({
                'service': service_name,
                'last_used': last_used.isoformat(),
                'replacement': deprecation_manager.deprecation_registry[service_name]['replacement_service']
            })
    
    return status

def generate_migration_plan() -> str:
    """Generate a comprehensive migration plan"""
    
    plan = """
# WealthPath AI Legacy to Modern Services Migration Plan

## Overview
This document outlines the migration from legacy services to modern, clean architecture services.

## Migration Timeline

"""
    
    # Sort services by removal date
    services_by_date = sorted(
        deprecation_manager.deprecation_registry.items(),
        key=lambda x: x[1]['removal_date']
    )
    
    for service_name, info in services_by_date:
        plan += f"""
### {service_name}
- **Replacement**: {info['replacement_service']}
- **Deprecation Level**: {info['deprecation_level'].upper()}
- **Removal Date**: {info['removal_date'].strftime('%Y-%m-%d')}
- **Days Remaining**: {(info['removal_date'] - datetime.now()).days}

"""
        
        if info['breaking_changes']:
            plan += "**Breaking Changes**:\n"
            for change in info['breaking_changes']:
                plan += f"- {change}\n"
            plan += "\n"
        
        if info['migration_guide']:
            plan += f"**Migration Guide**: {info['migration_guide']}\n\n"
    
    plan += """
## Migration Priority

1. **URGENT (< 30 days)**: Services with imminent removal dates
2. **HIGH (< 90 days)**: Services in DEPRECATED status
3. **MEDIUM (< 180 days)**: Services in WARNING status
4. **LOW (> 180 days)**: Services in INFO status

## Migration Benefits

### Modern Services Advantages:
- **Type Safety**: Full TypeScript/Python type annotations
- **Better Performance**: Async operations and optimized algorithms
- **Enhanced UX**: User-friendly interfaces and real-time features
- **Maintainability**: Clean architecture with single responsibility
- **Extensibility**: Easy to extend and modify for future requirements
- **Testing**: Built-in testing infrastructure and validation

### Risk Reduction:
- **Reduced Technical Debt**: Clean, modern codebase
- **Better Error Handling**: Comprehensive error management
- **Improved Monitoring**: Built-in logging and metrics
- **Enhanced Security**: Modern security practices

## Next Steps

1. Review deprecation warnings in logs
2. Update services based on priority timeline
3. Test thoroughly before deployment
4. Monitor for any issues post-migration
5. Remove legacy service imports once migration is complete

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return plan