# Shadow Mode Testing Checklist

## ✅ Pre-Launch Preparation

### System Requirements
- [ ] Redis running (or configured for in-memory fallback)
- [ ] Python 3.11+ available
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] OpenAI API key configured in `.env` file

### Environment Configuration
- [ ] `.env` file contains `EMBEDDING_SHADOW_MODE=true`
- [ ] `.env` file contains `USE_HYBRID_EMBEDDINGS=false`
- [ ] Alert thresholds configured appropriately
- [ ] Performance tuning parameters set

### Connectivity Tests
- [ ] Redis connection test: `redis-cli -u "redis://localhost:6379" ping`
- [ ] OpenAI API test: verify key is valid and has quota
- [ ] Port 8000 is available for the server

## ✅ Launch Sequence

### 1. Start Shadow Mode
- [ ] Run: `bash start_shadow_mode.sh`
- [ ] Verify server starts successfully (green checkmarks in output)
- [ ] Confirm no error messages in startup logs
- [ ] Check that shadow mode is enabled in configuration

### 2. Initial Health Check
- [ ] Open: http://localhost:8000/api/v1/embeddings/production-readiness
- [ ] Verify `shadow_mode.enabled: true`
- [ ] Verify `feature_flags.status: "ready"`
- [ ] Check that providers show as available

### 3. Monitoring Setup
- [ ] Run in separate terminal: `python3 monitor_shadow.py`
- [ ] Verify monitoring dashboard displays correctly
- [ ] Confirm real-time updates are working
- [ ] Check that all metrics show initial values

## ✅ Testing Phase

### Basic Functionality Tests
- [ ] Run: `python3 test_shadow_mode.py`
- [ ] Verify all tests pass (5/5 success rate)
- [ ] Address any configuration issues found
- [ ] Confirm shadow mode is actively ready

### Generate Test Data
- [ ] Use WealthPath AI normally (frontend, API calls, chat, etc.)
- [ ] Create financial plans and advisories
- [ ] Generate goal recommendations
- [ ] Use chat interface for financial questions
- [ ] Verify embedding requests are being processed

### Monitor Progress (First Hour)
- [ ] Check that `comparisons_made` is increasing
- [ ] Verify similarity scores are >90%
- [ ] Confirm no critical alerts are triggered
- [ ] Observe cache hit rates improving

### Performance Validation
- [ ] Average similarity score >95%
- [ ] P95 latency <500ms
- [ ] Cache hit rate >70% after warm-up
- [ ] No circuit breaker trips

## ✅ Daily Monitoring (48-72 hours)

### Daily Health Checks
- [ ] Review monitoring dashboard each morning
- [ ] Check alert status: `curl http://localhost:8000/api/v1/embeddings/alerts`
- [ ] Verify server stability and uptime
- [ ] Monitor cost accumulation and budget utilization

### Progress Tracking
- [ ] **Day 1**: 100+ comparisons, initial similarity baseline
- [ ] **Day 2**: 500+ comparisons, cache efficiency improving  
- [ ] **Day 3**: 1000+ comparisons, performance patterns established

### Quality Assurance
- [ ] No degradation in user experience
- [ ] Response times remain consistent
- [ ] No errors in application logs
- [ ] Financial data accuracy maintained

## 📊 Success Criteria (End of Testing)

### Minimum Requirements
- [ ] **1000+ comparisons** collected over 48-72 hours
- [ ] **>95% average similarity** between legacy and hybrid systems
- [ ] **No critical alerts** triggered during testing period
- [ ] **>90% readiness score** achieved

### Performance Benchmarks
- [ ] **Cache hit rate >80%** for repeated financial terms
- [ ] **P95 latency <500ms** for single embeddings
- [ ] **P99 latency <1000ms** for batch operations
- [ ] **Error rate <1%** across all embedding requests

### Cost and Efficiency
- [ ] **Daily cost <$10** for API usage during testing
- [ ] **Cost savings >60%** compared to API-only approach
- [ ] **Throughput >20 RPS** sustained during peak usage
- [ ] **Provider balance** between local and API appropriate

### System Stability
- [ ] **99.9% uptime** during testing period
- [ ] **Zero production incidents** caused by shadow mode
- [ ] **Graceful fallbacks** working correctly
- [ ] **Redis connection** stable or in-memory fallback functional

## 🚀 Go/No-Go Decision Criteria

### ✅ GO Conditions (All Must Be True)
- [ ] All success criteria met above
- [ ] Team confidence in system stability
- [ ] Rollback plan tested and verified
- [ ] Monitoring alerts configured and tested
- [ ] Cost projections within acceptable range

### ❌ NO-GO Conditions (Any One Triggers)
- [ ] Average similarity <95%
- [ ] More than 2 critical alerts during testing
- [ ] System caused any user-facing issues
- [ ] Cost exceeded budget by >20%
- [ ] Team lacks confidence in rollback procedure

## 🛠️ Troubleshooting Guide

### Common Issues and Solutions

#### "Shadow mode not enabled"
- Check `.env` file for correct `EMBEDDING_SHADOW_MODE=true`
- Restart server after environment changes
- Verify server is loading environment variables

#### "Low similarity scores"
- Review alert logs for specific embedding comparisons
- Check if different models being used (should be consistent)
- Verify text preprocessing is identical

#### "No comparisons being logged"
- Ensure WealthPath AI is generating embedding requests
- Check that shadow mode integration is triggered
- Verify no authentication blocking test calls

#### "Redis connection failed"
- Start Redis: `redis-server`
- Check Redis URL in `.env`: `REDIS_URL=redis://localhost:6379`
- Verify fallback to in-memory cache is working

#### "Server won't start"
- Check port 8000 availability: `lsof -i :8000`
- Verify Python dependencies: `pip install -r requirements.txt`
- Review server logs for specific error messages

## 📈 Next Steps After Success

### Immediate Actions (Within 24 hours)
- [ ] Document any performance optimizations discovered
- [ ] Share results with team for review and approval
- [ ] Plan canary deployment schedule (5% → 25% → 50% → 100%)
- [ ] Set up production monitoring and alerting

### Short-term Planning (1-2 weeks)
- [ ] Begin gradual rollout with feature flags
- [ ] Continue monitoring similarity and performance
- [ ] Optimize cache warming and provider routing
- [ ] Train team on new monitoring dashboards

### Long-term Optimization (1-2 months)
- [ ] Analyze cost savings and ROI
- [ ] Consider domain-specific model fine-tuning
- [ ] Implement advanced features (compression, regional routing)
- [ ] Plan for next-generation improvements

---

## 📞 Support and Escalation

### Development Team Contacts
- **Architecture Issues**: Check system logs and configuration
- **Performance Issues**: Review monitoring dashboards and alerts
- **Cost Concerns**: Analyze daily budget utilization
- **Quality Issues**: Examine similarity scores and comparison logs

### Emergency Procedures
- **Immediate Rollback**: Set `EMBEDDING_SHADOW_MODE=false` and restart
- **Budget Exceeded**: Check `EMBEDDING_DAILY_API_BUDGET_USD` setting
- **System Instability**: Review circuit breaker and error logs
- **User Impact**: Immediately disable and investigate

---

**Last Updated**: 2025-01-08  
**Version**: 1.0  
**Status**: Ready for Production Shadow Testing