"""
Lightweight unit tests for patched chat/RAG/calculator glue logic.
These tests avoid external deps by stubbing sqlalchemy and the vector store.
"""
import sys
import os
import types


def stub_sqlalchemy():
    sa = types.ModuleType("sqlalchemy")
    orm = types.ModuleType("sqlalchemy.orm")
    class Session:  # stub for type annotation
        pass
    orm.Session = Session
    sa.orm = orm
    sys.modules["sqlalchemy"] = sa
    sys.modules["sqlalchemy.orm"] = orm


def stub_app_services_light():
    """Stub heavy service modules to avoid importing external deps."""
    # structlog stub
    mod_sl = types.ModuleType("structlog")
    class _Logger:
        def info(self, *a, **k):
            pass
        def warning(self, *a, **k):
            pass
        def error(self, *a, **k):
            pass
    def get_logger():
        return _Logger()
    mod_sl.get_logger = get_logger
    sys.modules["structlog"] = mod_sl
    # app.services.identity_math
    mod_im = types.ModuleType("app.services.identity_math")
    class IdentityMath:  # minimal stub
        def compute_claims(self, user_id, db):
            return {}
    mod_im.IdentityMath = IdentityMath
    sys.modules["app.services.identity_math"] = mod_im

    # app.services.trust_engine
    mod_te = types.ModuleType("app.services.trust_engine")
    class TrustEngine:
        def validate(self, text, facts):
            return {"response": text, "confidence": "MEDIUM", "assumptions": []}
    mod_te.TrustEngine = TrustEngine
    sys.modules["app.services.trust_engine"] = mod_te

    # app.services.core_prompts
    mod_cp = types.ModuleType("app.services.core_prompts")
    class _CorePrompts:
        def format_prompt(self, *args, **kwargs):
            return "PROMPT"
    mod_cp.core_prompts = _CorePrompts()
    sys.modules["app.services.core_prompts"] = mod_cp

    # app.services.comprehensive_financial_calculator
    mod_cfc = types.ModuleType("app.services.comprehensive_financial_calculator")
    class _DummyCalc:
        def calculate_with_assumptions(self, *a, **k):
            return {"success": True}
    mod_cfc.comprehensive_calculator = _DummyCalc()
    sys.modules["app.services.comprehensive_financial_calculator"] = mod_cfc

    # Do not stub calculation_router; real router is lightweight and OK to import

    # app.services.llm_service
    mod_llm = types.ModuleType("app.services.llm_service")
    class _LLMService:
        def __init__(self):
            self.clients = {}
        async def generate(self, req):
            class R: content = "ok"
            return R()
    mod_llm.llm_service = _LLMService()
    sys.modules["app.services.llm_service"] = mod_llm

    # app.models.llm_models
    mod_llmm = types.ModuleType("app.models.llm_models")
    class LLMRequest:
        def __init__(self, **kwargs):
            pass
    mod_llmm.LLMRequest = LLMRequest
    sys.modules["app.models.llm_models"] = mod_llmm

    # precision_gate is pure python – no stub needed


def test_goal_adjustment_formatting():
    from app.services.agentic_rag import AgenticRAG

    rag = AgenticRAG()

    # Increase goal: should say add years
    inc_result = {
        'calculation_type': 'retirement_goal_adjustment',
        'original_goal': 3_500_000,
        'new_goal': 4_000_000,
        'years_saved': -2,  # negative means added years
        'original_years': 4,
        'new_years': 6,
    }
    txt_inc = rag._format_goal_adjustment_response(inc_result, {}, 'balanced')
    assert 'add 2 years' in txt_inc.lower(), f"Increase wording wrong: {txt_inc}"

    # Reduce goal: should say save years
    red_result = {
        'calculation_type': 'retirement_goal_adjustment',
        'original_goal': 3_500_000,
        'new_goal': 3_100_000,
        'years_saved': 2,
        'original_years': 6,
        'new_years': 4,
    }
    txt_red = rag._format_goal_adjustment_response(red_result, {}, 'balanced')
    assert 'save you 2 years' in txt_red.lower(), f"Reduction wording wrong: {txt_red}"


def test_vector_store_user_filtering():
    from app.services.agentic_rag import VectorStoreWrapper

    class Doc:
        def __init__(self, content, user_id, category="profile"):
            self.content = content
            self.metadata = {"user_id": user_id, "category": category}

    class DummyStore:
        def search(self, query, limit=10):
            docs = [
                ("a", 0.9, Doc("x for 123", "123")),
                ("b", 0.8, Doc("y for 456", "456")),
                ("c", 0.7, Doc("z for 123", 123)),  # numeric id mixed type
            ]
            return docs[:limit]

    wrap = VectorStoreWrapper()
    wrap.store = DummyStore()

    # Filter for user_id=123 should include only doc a and c
    res = sys.get_coroutine_wrapper() if hasattr(sys, 'get_coroutine_wrapper') else None
    import asyncio
    filtered = asyncio.get_event_loop().run_until_complete(
        wrap.query("authority", "q", {"limit": 5, "user_id": 123})
    )
    ids = {r["doc_id"] for r in filtered}
    assert ids == {"a", "c"}, f"Filtering failed, got ids={ids}"


def test_goal_adjustment_detection():
    # Ensure detection works for "reduce to 3,400,000" without 'goal'
    from app.services.calculation_router import CalculationRouter
    router = CalculationRouter()
    msg = "what if i reduce to 3,400,000"
    info = router.detect_calculation_needed(msg, [])
    assert info, "No detection returned"
    assert info.get('calculation_type') == 'retirement_goal_adjustment', f"Wrong calc type: {info}"
    nums = info.get('extracted_numbers', [])
    assert any(abs(n - 3400000) < 1 for n in nums), f"Did not extract 3.4M: {nums}"

    # Relative change: lower by 200k
    msg2 = "can we lower by 200k?"
    info2 = router.detect_calculation_needed(msg2, [])
    assert info2 and info2.get('calculation_type') == 'retirement_goal_adjustment', f"Wrong type for relative: {info2}"
    params2 = router.extract_calculation_params(msg2, {'_context': {'retirement_goal': 3500000}}, info2)
    assert abs(params2.get('new_goal', 0) - 3300000) < 1, f"Relative lowering failed: {params2}"


def test_net_worth_projection_detection():
    from app.services.calculation_router import CalculationRouter
    router = CalculationRouter()
    msg = "in 10 years, how much will my net worth be?"
    info = router.detect_calculation_needed(msg, [])
    assert info and info.get('calculation_type') == 'compound_growth_scenarios', f"Wrong calc type: {info}"
    params = router.extract_calculation_params(msg, {
        'net_worth': 2500000,
        'monthly_surplus': 7500
    }, info)
    assert params.get('years') == 10, f"Years not extracted: {params}"
    assert params.get('principal') == 2500000, f"Principal should use net_worth: {params}"
    assert params.get('monthly_contributions') == 7500, f"Monthly contributions missing: {params}"


def test_explain_last_short_circuit():
    # Ensure explain requests return stored record without recomputation
    from app.services.agentic_rag import AgenticRAG
    rag = AgenticRAG()
    session_id = "test_session"
    # Build and stash a record
    rec = rag._build_calculation_record(
        user_id=1,
        session_id=session_id,
        calc_type='years_to_retirement_goal',
        inputs={'current_assets': 2500000, 'target_goal': 3500000, 'monthly_additions': 8000},
        assumptions={'rate': 0.06, 'explanation': 'conservative'},
        outputs={'calculation_type': 'years_to_retirement_goal', 'years': 4}
    )
    rag._calc_record_by_session[session_id] = rec

    import asyncio
    result = asyncio.get_event_loop().run_until_complete(
        rag.handle_query(user_id=1, message="show me the calculations", db=None, mode='balanced', session_id=session_id)
    )
    assert 'Calculation Details' in result['response'], result
    assert rec['calculation_id'] in result['response'], result['response']


def test_precision_gate_triggers_for_ambiguous_short_message():
    from app.services.precision_gate import need_clarification, map_message_to_domain, build_clarify_card
    msg = "optimize expenses?"
    intent = map_message_to_domain(msg)
    ok, reason, missing = need_clarification(msg, intent, confidence=0.5, slots={})
    assert ok and "short_ambiguous" in reason or "low_intent_confidence" in reason
    card = build_clarify_card(intent, reason)
    assert card.get("schema_version") == "clarify.v1"
    assert isinstance(card.get("options"), list) and len(card["options"]) >= 3


def test_goal_for_timeframe_routes_to_projection():
    from app.services.calculation_router import CalculationRouter
    router = CalculationRouter()
    msg = "What if I retire in 2 years, what should be my goal?"
    info = router.detect_calculation_needed(msg, [])
    assert info and info.get('calculation_type') == 'compound_growth_scenarios', info
    params = router.extract_calculation_params(msg, {'net_worth': 2500000, 'monthly_surplus': 7000}, info)
    assert params.get('years') == 2, params
    assert params.get('principal') == 2500000, params
    assert params.get('monthly_contributions') == 7000, params


def test_withdrawal_sustainability_defaults():
    from app.services.calculation_router import CalculationRouter
    router = CalculationRouter()
    msg = "Can I safely withdraw 4% from my portfolio?"
    info = router.detect_calculation_needed(msg, [])
    assert info and info.get('calculation_type') == 'withdrawal_sustainability', info
    params = router.extract_calculation_params(msg, {'net_worth': 2500000}, info)
    assert params.get('assets') == 2500000, params
    assert abs(params.get('annual_withdrawal', 0) - 100000) < 1, params  # 4% of 2.5M
    assert params.get('years_needed') == 30, params


def test_detailed_calculation_formatting():
    from app.services.agentic_rag import AgenticRAG
    rag = AgenticRAG()
    # Simulate a goal adjustment result
    result = {
        'calculation_type': 'retirement_goal_adjustment',
        'original_goal': 3_500_000,
        'new_goal': 3_300_000,
        'original_years': 4,
        'new_years': 3,
        'years_saved': 1,
    }
    assumptions = {'rate': 0.06, 'explanation': 'conservative growth assumptions'}
    txt = rag._format_calculation_details(result, assumptions)
    assert 'Goal adjustment' in txt or 'Type: Goal adjustment' in txt, txt
    assert '$3,500,000' in txt and '$3,300,000' in txt, txt
    assert 'saved 1 years' in txt.lower() or 'saved 1 year' in txt.lower(), txt


def main():
    # Stub sqlalchemy before importing modules that reference it
    stub_sqlalchemy()
    # Add backend package root to sys.path so 'app' can be imported
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    backend_root = os.path.join(repo_root, "backend")
    if backend_root not in sys.path:
        sys.path.insert(0, backend_root)
    # Stub heavy service modules to avoid importing external deps during import
    stub_app_services_light()

    tests = [
        ("goal_adjustment_formatting", test_goal_adjustment_formatting),
        ("vector_store_user_filtering", test_vector_store_user_filtering),
        ("goal_adjustment_detection", test_goal_adjustment_detection),
        ("detailed_calculation_formatting", test_detailed_calculation_formatting),
        ("net_worth_projection_detection", test_net_worth_projection_detection),
        ("explain_last_short_circuit", test_explain_last_short_circuit),
        ("precision_gate_triggers", test_precision_gate_triggers_for_ambiguous_short_message),
    ]
    failures = []
    for name, fn in tests:
        try:
            fn()
            print(f"[PASS] {name}")
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            failures.append((name, e))
    if failures:
        sys.exit(1)
    print("All lightweight tests passed.")


if __name__ == "__main__":
    main()
