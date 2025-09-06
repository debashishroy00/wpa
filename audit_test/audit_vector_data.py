"""
Audit: Vector Store Data (in-container)
Inspects what documents exist and whether key values (e.g., real estate %) are present.
"""
import json
import re

import sys, os
sys.path.insert(0, '/app')
from app.services.simple_vector_store import get_vector_store, SimpleDocument


def audit_vector_store(user_id: int = 1):
    store = get_vector_store()

    out = {
        "documents": [],
        "stats": store.get_stats(),
        "real_estate_pct": None,
    }

    doc_types = [
        "financial_summary",
        "asset_allocation",
        "income_breakdown",
        "expense_breakdown",
        "financial_goals",
        "estate_insurance",
        "chat_intelligence",
    ]

    for doc_type in doc_types:
        doc_id = f"user_{user_id}_{doc_type}"
        doc = store.get_document(doc_id)
        if doc:
            item = {"id": doc_id, "found": True}
            content = doc.content if isinstance(doc, SimpleDocument) else str(doc)
            if doc_type == "asset_allocation":
                m = re.search(r"real\s*estate[\w\s:\-()]*?(\d+\.?\d*)%", content, re.IGNORECASE)
                if m:
                    out["real_estate_pct"] = float(m.group(1))
                    item["real_estate_pct"] = out["real_estate_pct"]
            out["documents"].append(item)
        else:
            out["documents"].append({"id": doc_id, "found": False})

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    audit_vector_store()
