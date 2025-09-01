# Service Inventory for Cleanup
Date: 2025-09-01

## Summary Statistics
- **Total Services**: 42 files
- **Total Lines of Code**: 17,237 lines
- **Largest Service**: vector_sync_service.py (2,284 lines)
- **Tax-Related Services**: 18 files
- **Calculator Services**: 3 files

## Services by Size (Top 20)
| Lines | Service | Category | Remove? |
|-------|---------|----------|---------|
| 2,284 | vector_sync_service.py | Vector/Embedding | Review |
| 1,104 | intelligence_engine.py | Intelligence | Keep/Refactor |
| 1,000 | complete_financial_context_service.py | Context | Review |
| 885 | projection_service.py | Calculation | **REMOVE** |
| 725 | prompt_builder_service.py | LLM Support | Keep/Refactor |
| 664 | tax_calculations.py | Tax Calculation | **REMOVE** |
| 574 | advisory_engine.py | Advisory | Keep/Refactor |
| 515 | chat_memory_service.py | Chat/Memory | Keep |
| 496 | llm_service.py | LLM Core | Keep |
| 479 | plan_engine.py | Planning | Review |
| 456 | data_integrity_service.py | Data Validation | Review |
| 446 | embeddings/alerts.py | Monitoring | Keep |
| 434 | embeddings/monitoring.py | Monitoring | Keep |
| 431 | embeddings/cache.py | Caching | Keep |
| 417 | embeddings/openai_provider.py | Embeddings | Keep |
| 410 | financial_health_scorer.py | Scoring/Calc | **REMOVE** |
| 373 | retirement_calculator.py | Calculator | **REMOVE** |
| 360 | knowledge_base.py | Knowledge | Keep/Refactor |
| 351 | embeddings/router.py | Embeddings | Keep |

## Complete Service List (42 files)

### Core Services to Keep/Refactor
1. **advisory_engine.py** - Main advisory service (574 lines)
2. **chat_memory_service.py** - Conversation memory (515 lines)
3. **llm_service.py** - LLM integration (496 lines)
4. **intelligence_engine.py** - Intelligence core (1,104 lines)
5. **prompt_builder_service.py** - Prompt management (725 lines)
6. **knowledge_base.py** - Knowledge management (360 lines)
7. **simple_vector_store.py** - Vector storage (JSON-based)
8. **session_service.py** - Session management
9. **user_service.py** - User management

### LLM Client Services (Keep)
10. **llm_clients/claude_client.py**
11. **llm_clients/gemini_client.py**
12. **llm_clients/openai_client.py**

### Embedding Services (Keep)
13. **embeddings/base.py**
14. **embeddings/cache.py**
15. **embeddings/openai_provider.py**
16. **embeddings/router.py**
17. **embeddings/monitoring.py**
18. **embeddings/alerts.py**
19. **embeddings/compatibility.py**

### Services to REMOVE (Hardcoded Calculations)
20. **tax_calculations.py** - 664 lines of hardcoded tax logic
21. **retirement_calculator.py** - 373 lines of retirement calculations
22. **projection_service.py** - 885 lines of financial projections
23. **financial_health_scorer.py** - 410 lines of scoring logic
24. **calculation_validator.py** - Validation for calculations
25. **formula_library.py** - Hardcoded formulas

### Services to Review for Removal
26. **complete_financial_context_service.py** - 1,000 lines (likely has calculations)
27. **plan_engine.py** - 479 lines (may have rule-based logic)
28. **financial_summary_service.py** - Summary generation
29. **tax_intelligence_formatter.py** - Tax formatting
30. **retirement_response_formatter.py** - Retirement formatting
31. **enhanced_intent_classifier.py** - Intent classification
32. **intent_service.py** - Intent handling
33. **chat_intelligence_service.py** - Chat intelligence
34. **basic_response_verifier.py** - Response verification
35. **data_integrity_service.py** - Data validation (456 lines)

### Infrastructure Services (Keep)
36. **vector_sync_service.py** - 2,284 lines (needs major refactor)
37. **vector_db_service.py** - Vector database service
38. **token_manager.py** - Token management
39. **ml_fallbacks.py** - ML alternatives (no heavy deps)
40. **__init__.py** - Package initialization

## Cleanup Strategy

### Phase 1: Remove Calculation Services (Save ~3,000 lines)
- [ ] Remove tax_calculations.py (664 lines)
- [ ] Remove retirement_calculator.py (373 lines)
- [ ] Remove projection_service.py (885 lines)
- [ ] Remove financial_health_scorer.py (410 lines)
- [ ] Remove calculation_validator.py
- [ ] Remove formula_library.py

### Phase 2: Create New Core Services
- [ ] Create IdentityMath service (simple facts only)
- [ ] Create TrustEngine service (validation)
- [ ] Create CorePrompts service (Tax, Risk, Goals)

### Phase 3: Refactor Intelligence Services
- [ ] Simplify intelligence_engine.py (1,104 → ~300 lines)
- [ ] Simplify complete_financial_context_service.py (1,000 → ~200 lines)
- [ ] Refactor prompt_builder_service.py for new architecture

### Phase 4: Clean Vector Services
- [ ] Refactor vector_sync_service.py (2,284 → ~500 lines)
- [ ] Ensure simple_vector_store.py is primary vector service

## Expected Outcome
- **Current**: 17,237 lines across 42 services
- **After Cleanup**: ~8,000 lines across ~25 services
- **Reduction**: ~9,000 lines (52% reduction)

## Next Steps
1. Review this inventory with the team
2. Backup current services before deletion
3. Start with Phase 1 removals
4. Implement new IdentityMath service
5. Build TrustEngine for validation
6. Create CorePrompts for LLM guidance