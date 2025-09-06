"""
Audit: Data Accuracy Verification (in-container)
Compare DB financial summary vs vector store content for drift/staleness.
"""
import json
import sys
sys.path.insert(0, '/app')
from app.services.financial_summary_service import financial_summary_service
from app.services.simple_vector_store import get_vector_store
from app.db.session import SessionLocal


def verify_data(user_id: int = 1):
    db = SessionLocal()
    try:
        summary = financial_summary_service.get_user_financial_summary(user_id, db)
        store = get_vector_store()
        vec_doc = store.get_document(f"user_{user_id}_asset_allocation")
        vec_content = vec_doc.content if vec_doc else ""
        total_assets = summary.get("totalAssets", 0)
        out = {
            "summary_loaded": "error" not in summary and bool(summary),
            "total_assets": total_assets,
            "vector_has_total": str(int(total_assets)).replace(",", "") in (vec_content or "").replace(",", ""),
        }
        print(json.dumps(out, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    verify_data()
