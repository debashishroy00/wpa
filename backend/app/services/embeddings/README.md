# Hybrid Embedding System

Production-grade embedding architecture with intelligent routing, caching, and zero-disruption migration capabilities.

## Overview

The WealthPath AI Hybrid Embedding System provides:

- **Intelligent Routing**: Context-aware decisions between local and API providers
- **Two-tier Caching**: L1 in-memory + L2 Redis for optimal performance  
- **Cost Optimization**: Automatic budget management and provider switching
- **Privacy First**: PII detection forces local processing
- **Zero Downtime**: Shadow mode testing with backward compatibility

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Application   │───▶│ Compatibility    │───▶│ Hybrid Service  │
│      Code       │    │    Adapter       │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                       ┌─────────────────────────────────┼─────────────────────────────────┐
                       │                                 ▼                                 │
                       │                        ┌─────────────────┐                        │
                       │                        │     Router      │                        │
                       │                        │   (Intelligent  │                        │
                       │                        │    Routing)     │                        │
                       │                        └─────────────────┘                        │
                       │                                 │                                 │
                       │                ┌────────────────┼────────────────┐                │
                       │                ▼                                 ▼                │
                       │    ┌─────────────────┐                ┌─────────────────┐         │
                       │    │ Local Provider  │                │ OpenAI Provider │         │
                       │    │ (Sentence       │                │ (API with       │         │
                       │    │ Transformers)   │                │ Circuit Breaker)│         │
                       │    └─────────────────┘                └─────────────────┘         │
                       │                │                                 │                 │
                       │                └────────────────┬────────────────┘                 │
                       │                                 ▼                                 │
                       │                        ┌─────────────────┐                        │
                       │                        │  Cache Layer    │                        │
                       │                        │ L1: In-Memory   │                        │
                       │                        │ L2: Redis       │                        │
                       │                        └─────────────────┘                        │
                       │                                 │                                 │
                       └─────────────────────────────────┼─────────────────────────────────┘
                                                         ▼
                                              ┌─────────────────┐
                                              │   Monitoring    │
                                              │   & Alerts      │
                                              └─────────────────┘
```

## Key Components

### 1. **Compatibility Adapter** (`compatibility.py`)
- Maintains backward compatibility with existing APIs
- Triggers shadow mode comparisons automatically
- Provides migration helpers and decorators

### 2. **Hybrid Service** (`hybrid_service.py`) 
- Main orchestration layer with feature flag control
- Coordinates all components based on configuration
- Implements gradual rollout and fallback logic

### 3. **Intelligent Router** (`router.py`)
- Context-aware routing decisions (realtime vs quality vs cost)
- PII detection and privacy enforcement
- Cost budget management and provider selection

### 4. **Provider Implementations**
- **Local Provider** (`local_provider.py`): Sentence transformers with lazy loading
- **OpenAI Provider** (`openai_provider.py`): API client with circuit breaker and retries

### 5. **Caching System** (`cache.py`)
- **L1 Cache**: In-memory LRU cache (1000 hot embeddings)
- **L2 Cache**: Redis persistent cache with smart TTL
- **Domain-specific warming**: Pre-loads 130+ financial terms

### 6. **Monitoring & Alerting** (`monitoring.py`, `alerts.py`)
- Real-time performance tracking (P50/P95/P99 latencies)
- Cost monitoring and budget alerts
- Quality comparison and degradation detection

### 7. **Shadow Mode Testing** (`shadow_mode.py`)
- Zero-impact parallel testing of new system
- Automatic quality comparisons with legacy system
- Statistical analysis and validation

## Configuration

All configuration is handled via environment variables:

### Feature Flags
```bash
# Main control flags
USE_HYBRID_EMBEDDINGS=false      # Enable hybrid system
EMBEDDING_SHADOW_MODE=true       # Enable shadow testing

# Component controls  
EMBEDDING_ENABLE_CACHING=true    # Enable caching layer
EMBEDDING_ENABLE_ROUTING=true    # Enable intelligent routing
EMBEDDING_ENABLE_MONITORING=true # Enable metrics collection
```

### Performance Tuning
```bash
# Cache configuration
EMBEDDING_L1_CACHE_SIZE=1000                    # In-memory cache size
EMBEDDING_L2_CACHE_TTL_API=604800              # Redis TTL for API (7 days)
EMBEDDING_L2_CACHE_TTL_LOCAL=86400             # Redis TTL for local (24 hours)

# Routing thresholds
EMBEDDING_DAILY_API_BUDGET_USD=10.0             # Daily API budget
EMBEDDING_REALTIME_LATENCY_THRESHOLD_MS=1000   # Max latency for realtime
EMBEDDING_BATCH_SIZE_THRESHOLD=100              # Large batch threshold
```

### Provider Settings
```bash
# OpenAI configuration
OPENAI_API_KEY=your-api-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_MAX_RETRIES=3

# Local model configuration  
LOCAL_EMBEDDING_MODEL=all-MiniLM-L6-v2
LOCAL_EMBEDDING_DEVICE=auto                     # auto, cpu, or cuda
LOCAL_EMBEDDING_BATCH_SIZE=32
```

### Alert Thresholds
```bash
# Performance alerts
ALERT_P95_LATENCY_WARNING=500                   # 500ms P95 latency
ALERT_CACHE_HIT_WARNING=0.7                    # 70% cache hit rate

# Quality alerts  
ALERT_SIMILARITY_WARNING=0.95                  # 95% similarity
ALERT_ERROR_RATE_WARNING=0.05                  # 5% error rate

# Cost alerts
ALERT_API_BUDGET_WARNING=0.8                   # 80% budget utilization
```

## Usage Examples

### Basic Usage (Backward Compatible)
```python
from app.services.embeddings.compatibility import get_embedding_service

# Single embedding
service = get_embedding_service()
embedding = await service.generate_embedding("retirement planning advice")

# Batch embeddings  
embeddings = await service.generate_embeddings([
    "401k contribution strategies",
    "Roth IRA conversion timing", 
    "Social Security optimization"
])
```

### Enhanced Usage (New Features)
```python
from app.services.embeddings.compatibility import get_embedding_service
from app.services.embeddings.base import EmbeddingContext

service = get_embedding_service()

# Context-aware embedding
result = await service.generate_embedding_with_metadata(
    text="portfolio rebalancing strategy",
    context="analysis"  # Routes to high-quality API provider
)

# Access enhanced metadata
print(f"Provider: {result['provider']}")           # "openai" or "local" 
print(f"Cost: ${result['cost_usd']:.6f}")         # Actual cost incurred
print(f"Latency: {result['latency_ms']:.1f}ms")   # Response time
print(f"Cached: {result['cached']}")              # Cache hit/miss
```

### Advanced Configuration
```python
from app.services.embeddings.base import EmbeddingProvider, EmbeddingContext
from app.services.embeddings.hybrid_service import HybridEmbeddingService

# Create service with custom configuration  
service = HybridEmbeddingService(
    openai_api_key="your-key",
    redis_url="redis://localhost:6379",
    routing_config=RoutingConfig(
        daily_api_budget_usd=25.0,
        realtime_latency_threshold_ms=750
    )
)

# Generate with explicit provider preference
result = await service.generate_embeddings(
    texts=["tax optimization strategies"],
    context=EmbeddingContext.SENSITIVE,  # Forces local processing
    preferred_provider=EmbeddingProvider.LOCAL
)
```

## Shadow Mode Testing

Shadow mode allows testing the hybrid system alongside the existing system with zero user impact:

### 1. Enable Shadow Mode
```bash
# In .env file
EMBEDDING_SHADOW_MODE=true
USE_HYBRID_EMBEDDINGS=false
```

### 2. Start Monitoring
```bash
# Start server with shadow mode
bash start_shadow_mode.sh

# Monitor progress in another terminal
python3 monitor_shadow.py
```

### 3. Validate Results
```bash
# Quick validation test
python3 test_shadow_mode.py

# Check readiness dashboard
curl http://localhost:8000/api/v1/embeddings/production-readiness
```

### 4. Success Criteria
- 100+ comparisons collected over 48-72 hours
- >95% average similarity between systems  
- No critical alerts or performance degradation
- Cache hit rate >80% for common terms

## Monitoring and Alerting

### Real-time Dashboards
- **Production Readiness**: `/api/v1/embeddings/production-readiness`
- **Live Metrics**: `/api/v1/embeddings/metrics` 
- **System Health**: `/api/v1/embeddings/health`
- **Active Alerts**: `/api/v1/embeddings/alerts`

### Key Metrics Tracked
- **Performance**: P50/P95/P99 latencies, throughput, error rates
- **Cost**: Daily spend, provider usage, budget utilization  
- **Quality**: Embedding similarity, degradation detection
- **Cache**: Hit rates, efficiency, L1/L2 performance
- **Provider**: Health status, circuit breaker state, fallback usage

### Alert Conditions
- API budget utilization >80% (warning) or >95% (critical)
- Cache hit rate <70% (warning) or <50% (error)  
- P95 latency >500ms (warning) or >1000ms (error)
- Quality similarity <95% (warning) or <90% (error)
- Provider unhealthy or circuit breaker open

## Migration Strategy

### Phase 1: Shadow Mode (0% Impact)
```bash
EMBEDDING_SHADOW_MODE=true
USE_HYBRID_EMBEDDINGS=false
```
- Run for 48-72 hours collecting comparison data
- Validate quality, performance, and cost metrics
- Zero impact on users or existing functionality

### Phase 2: Canary Deployment (5% Traffic)
```bash  
USE_HYBRID_EMBEDDINGS=true
EMBEDDING_ROLLOUT_PERCENTAGE=5
```
- Enable hybrid system for small percentage of requests
- Monitor metrics and user experience closely
- Maintain dual-write for rollback capability

### Phase 3: Progressive Rollout (25%, 50%, 100%)
- Gradually increase traffic to hybrid system
- Monitor cost savings and performance improvements  
- Disable shadow mode after full rollout validation

### Phase 4: Legacy Cleanup
- Remove old embedding code after 30 days stable operation
- Optimize based on production usage patterns
- Implement advanced features (compression, regional routing)

## Performance Benchmarks

### Expected Performance
- **Local Provider**: ~100ms latency, unlimited scale, $0 cost
- **API Provider**: ~200ms latency, premium quality, ~$0.0001/embedding
- **Cache Hit**: ~1ms latency, 80%+ hit rate after warm-up
- **Overall Throughput**: >50 RPS sustained, >100 RPS peak

### Cost Optimization
- **Projected Savings**: 60-70% vs API-only approach
- **Break-even Point**: ~50 embeddings/day (varies by usage pattern)
- **Budget Control**: Hard limits prevent runaway costs
- **Automatic Switching**: Routes to local when approaching budget limits

### Quality Assurance  
- **Similarity Target**: >95% between local and API embeddings
- **Domain Optimization**: 130+ financial terms pre-cached
- **Consistency**: Same results across provider switches
- **Monitoring**: Continuous quality degradation detection

## Troubleshooting

### Common Issues

#### Shadow Mode Not Working
- Verify `EMBEDDING_SHADOW_MODE=true` in environment
- Check that server loaded environment variables correctly
- Ensure shadow comparison is triggered in existing code paths

#### Low Cache Hit Rates
- Verify Redis is running and accessible
- Check cache warming completed successfully  
- Monitor for cache eviction due to memory limits

#### High API Costs
- Review daily budget setting: `EMBEDDING_DAILY_API_BUDGET_USD`
- Check routing logic is working correctly
- Verify batch processing is using local provider

#### Quality Degradation
- Compare model versions between providers
- Check for text preprocessing differences
- Verify embedding dimensions match expectations

### Debug Commands
```bash
# Check system health
curl http://localhost:8000/api/v1/embeddings/health

# View current metrics
curl http://localhost:8000/api/v1/embeddings/metrics

# Test shadow mode setup
python3 test_shadow_mode.py --json

# Run load tests
python3 scripts/load_test_embeddings.py --users 10 --requests 50

# Verify rollback capability
python3 scripts/verify_rollback.py
```

## Development

### Adding New Providers
1. Implement `BaseEmbeddingProvider` interface
2. Add provider configuration to settings
3. Register provider in `HybridEmbeddingService`
4. Update routing logic in `EmbeddingRouter`
5. Add health check and monitoring support

### Extending Caching
1. Implement new cache backend in `cache.py`
2. Add configuration options
3. Update cache key generation logic
4. Add metrics and monitoring

### Custom Routing Logic
1. Extend `EmbeddingRouter` class
2. Implement custom routing decisions
3. Add configuration for new parameters
4. Update monitoring to track new metrics

---

## API Reference

See the [API documentation](http://localhost:8000/docs) when the server is running for complete endpoint details.

## License

Copyright (c) 2025 WealthPath AI. All rights reserved.