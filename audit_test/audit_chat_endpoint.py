"""
Audit: Chat Endpoint Integration (in-container)
Verifies prompt sections and lack of early-return RAG path.
"""
import json
import inspect
import sys
sys.path.insert(0, '/app')
import app.api.v1.endpoints.chat_simple as chat_simple


def audit_endpoint():
    src = inspect.getsource(chat_simple)
    out = {
        "has_complete_context_section": "COMPLETE FINANCIAL CONTEXT (USE THIS AS PRIMARY DATA SOURCE)" in src,
        "system_prompt_mentions_facts": "system_prompt=\"Financial advisor using provided facts" in src,
        "agentic_rag_disabled": "use_agentic_rag = False" in src,
        "add_message_pair_calls": src.count("add_message_pair(")
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    audit_endpoint()
