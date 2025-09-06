"""
Audit: Complete Context Generation Trace (in-container)
Builds the complete financial context and verifies enforcement sections and key values.
"""
import json
import re
import sys
sys.path.insert(0, '/app')
from app.services.complete_financial_context_service import CompleteFinancialContextService
from app.db.session import SessionLocal


def trace_context(user_id: int = 1):
    db = SessionLocal()
    try:
        service = CompleteFinancialContextService()
        context = service.build_complete_context(
            user_id=user_id,
            db=db,
            user_query="Why is my portfolio underperforming?",
            insight_level="balanced",
        )

        out = {
            "length": len(context) if isinstance(context, str) else None,
            "has_mandatory": isinstance(context, str) and ("MANDATORY" in context),
            "has_validation": isinstance(context, str) and ("VALIDATION" in context),
            "has_memory": isinstance(context, str) and ("CONVERSATION MEMORY" in context),
            "has_numbers": isinstance(context, str) and bool(re.search(r"\$[\d,]+", context or "")),
            "has_percent": isinstance(context, str) and bool(re.search(r"\d+\.?\d*%", context or "")),
            "allocations": [],
        }

        if isinstance(context, str):
            allocations = re.findall(r"^\s*[•\-]?\s*([A-Za-z /()]+):\s*\$?[\d,]+\s*\((\d+\.?\d*)%\)", context, flags=re.MULTILINE)
            out["allocations"] = [{"name": n.strip(), "pct": float(p)} for n, p in allocations]

        print(json.dumps(out, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    trace_context()
