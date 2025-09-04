"""
Precision Gate: lightweight, heuristic clarifier to prevent vague answers.
Runs before intent expansion/analytics. Pure-Python, no external deps.
"""
from typing import Dict, List, Tuple


# Ambiguity tokens (lowercased)
AMBIGUITY = {
    "optimize", "better", "okay", "ok", "thoughts", "update",
    "next steps", "expenses?", "investments?", "retirement?", "taxes?",
    "help", "plan?", "what next", "advice?",
}

# Required slots per domain intent
REQUIRED_SLOTS: Dict[str, List[str]] = {
    "expense_audit": ["timeframe"],
    "tax_planning": ["tax_year"],
    "retirement_plan": [],  # allow defaults
    "investing": ["scope"],  # which accounts/portfolio
}


def need_clarification(msg: str, intent: str, confidence: float, slots: Dict) -> Tuple[bool, str, List[str]]:
    """Return (should_clarify, reason, missing_slots)."""
    msg_l = (msg or "").lower().strip()
    reasons: List[str] = []

    # Confidence gate
    if confidence is not None and confidence < 0.65:
        reasons.append("low_intent_confidence")

    # Short + ambiguous wording
    words = msg_l.split()
    if len(words) < 6 and any(tok in msg_l for tok in AMBIGUITY):
        reasons.append("short_ambiguous")

    # Missing required slots
    required = REQUIRED_SLOTS.get(intent, [])
    missing = [s for s in required if not slots.get(s)]
    if missing:
        reasons.append(f"missing_slots:{','.join(missing)}")

    return (len(reasons) > 0, "|".join(reasons), missing)


def map_message_to_domain(msg: str) -> str:
    """Heuristic domain mapping to one of our intents."""
    m = (msg or "").lower()
    if any(k in m for k in ["expense", "spend", "subscription", "budget"]):
        return "expense_audit"
    if any(k in m for k in ["tax", "irs", "bracket", "deduction", "2025"]):
        return "tax_planning"
    if any(k in m for k in ["invest", "portfolio", "rebalance", "allocation"]):
        return "investing"
    # Default to retirement when vague
    return "retirement_plan"


def build_clarify_card(intent: str, reason: str, user_ctx: Dict = None) -> Dict:
    """Build the clarifier JSON payload for the given intent/domain."""
    user_ctx = user_ctx or {}

    if intent == "expense_audit":
        return {
            "schema_version": "clarify.v1",
            "reason": reason,
            "message": "What should I focus on for expenses?",
            "options": [
                {"id": "breakdown_last_month", "label": "Full breakdown (last month)"},
                {"id": "overspend_alerts_3m", "label": "Find overspending & trends (3 months)"},
                {"id": "subscriptions", "label": "Subscriptions & price creep"},
                {"id": "benchmarks_nc", "label": "Compare to NC/Charlotte peers"},
                {"id": "optimize_$200+", "label": "Cut ≥$200/mo & re-route (dated plan)"},
            ],
            "assumptions_if_skipped": [
                "Timeframe = last full month",
                "Benchmarks = NC state-level",
                "Savings redirected to 401k first, then taxable",
            ],
            "fallbacks": [
                {"id": "show_everything", "label": "Show everything (long report)"},
                {"id": "use_defaults", "label": "Skip: use defaults"},
            ],
        }

    if intent == "retirement_plan":
        return {
            "schema_version": "clarify.v1",
            "reason": reason,
            "message": "Which retirement view do you want?",
            "options": [
                {"id": "timeline_age", "label": "Target-age timeline"},
                {"id": "funding_gap_now", "label": "Funding gap now"},
                {"id": "roth_vs_trad_this_year", "label": "Roth vs Traditional this year"},
                {"id": "ss_timing", "label": "Social Security timing"},
                {"id": "fire_variant", "label": "FIRE/Lean-FIRE plan"},
            ],
            "assumptions_if_skipped": [
                "View = Target-age timeline",
                "Growth = portfolio-weighted capped for retirement",
                "Contributions = monthly surplus",
            ],
            "fallbacks": [
                {"id": "show_everything", "label": "Show everything (long report)"},
                {"id": "use_defaults", "label": "Skip: use defaults"},
            ],
        }

    if intent == "tax_planning":
        return {
            "schema_version": "clarify.v1",
            "reason": reason,
            "message": "Which tax task for this year?",
            "options": [
                {"id": "marginal_bracket", "label": "Tax bracket & marginal"},
                {"id": "maximize_deductions", "label": "Maximize deductions"},
                {"id": "roth_conversion_window", "label": "Roth conversion window"},
                {"id": "tlh_candidates", "label": "Tax-loss harvest candidates"},
                {"id": "nc_specific_moves", "label": "NC-specific moves"},
            ],
            "assumptions_if_skipped": [
                "Tax year = current year",
            ],
            "fallbacks": [
                {"id": "show_everything", "label": "Show everything (long report)"},
                {"id": "use_defaults", "label": "Skip: use defaults"},
            ],
        }

    # investing
    return {
        "schema_version": "clarify.v1",
        "reason": reason,
        "message": "Which investment task?",
        "options": [
            {"id": "rebalance_to_target", "label": "Rebalance to target"},
            {"id": "tax_efficient_location", "label": "Tax‑efficient asset location"},
            {"id": "deploy_new_cash", "label": "New cash deployment"},
            {"id": "fees_and_drag", "label": "Fees & performance drag"},
            {"id": "risk_check", "label": "Risk check vs tolerance"},
        ],
        "assumptions_if_skipped": [
            "Scope = all taxable + retirement accounts",
        ],
        "fallbacks": [
            {"id": "show_everything", "label": "Show everything (long report)"},
            {"id": "use_defaults", "label": "Skip: use defaults"},
        ],
    }

