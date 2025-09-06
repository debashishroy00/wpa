"""
Audit: Intercept LLM Calls (in-container)
Monkeypatch llm_service.generate to capture the prompt payload and detect enforcement/memory.
"""
import asyncio
import json
from unittest.mock import patch
import sys
sys.path.insert(0, '/app')
from app.api.v1.endpoints.chat_simple import chat_message, ChatRequest
from app.db.session import SessionLocal


class MockUser:
    id = 1


async def run_intercept():
    sent = []

    async def fake_generate(llm_request):
        sent.append(llm_request)
        class R:
            content = "Test response from mock LLM"
        return R()

    db = SessionLocal()
    try:
        with patch("app.api.v1.endpoints.chat_simple.llm_service.generate", side_effect=fake_generate):
            # Use a fixed session_id to simulate multi-turn memory
            req = ChatRequest(message="How much of my portfolio is in real estate?", session_id="audit-session", insight_level="balanced")
            _ = await chat_message(req, MockUser(), db)
    finally:
        db.close()

    out = {"captured": bool(sent)}
    if sent:
        up = sent[-1].user_prompt if hasattr(sent[-1], "user_prompt") else ""
        out.update({
            "has_complete_context": "COMPLETE FINANCIAL CONTEXT" in up,
            "has_critical_instructions": "CRITICAL INSTRUCTIONS" in up,
            "has_conversation_memory": "CONVERSATION MEMORY" in up,
            "preview": up[:600]
        })
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    asyncio.run(run_intercept())
