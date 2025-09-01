"""
Agentic RAG for WealthPath AI - Phase 2: Query Decomposition & Smart Planning
Adds intelligent query planning and multi-step execution.
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
import logging
import json
import asyncio
from datetime import datetime
from hashlib import md5

from app.services.identity_math import IdentityMath
from app.services.simple_vector_store import SimpleVectorStore
from app.services.trust_engine import TrustEngine
from app.services.llm_service import llm_service
from app.models.llm_models import LLMRequest

logger = logging.getLogger(__name__)

class QueryParser:
    """Phase 1: Simple query parser - extract basic intent."""
    
    def parse(self, message: str) -> Dict[str, Any]:
        """Simple intent parsing based on keywords."""
        msg_lower = message.lower()
        
        # Basic intent detection
        if any(word in msg_lower for word in ["net worth", "worth", "wealth", "assets"]):
            intent = "net_worth"
        elif any(word in msg_lower for word in ["401k", "retirement", "retire"]):
            intent = "retirement"
        elif any(word in msg_lower for word in ["tax", "taxes", "deduction"]):
            intent = "tax"
        elif any(word in msg_lower for word in ["expense", "spending", "budget"]):
            intent = "expenses"
        else:
            intent = "general"
            
        return {
            "intent": intent,
            "entities": [],  # Phase 1: keep simple
            "confidence": 0.8
        }

class VectorStoreWrapper:
    """Wrapper around SimpleVectorStore to match expected interface."""
    
    def __init__(self):
        self.store = SimpleVectorStore()
    
    async def query(self, index: str, query: str, filters: Dict) -> List[Dict[str, Any]]:
        """Query the vector store and return formatted results."""
        try:
            limit = filters.get("limit", 5)
            results = self.store.search(query, limit=limit)
            
            formatted_results = []
            for doc_id, score, doc in results:
                formatted_results.append({
                    "text": doc.content[:500],  # Limit text length
                    "source": doc.metadata.get("category", "unknown"),
                    "doc_id": doc_id,
                    "score": score
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Vector store query failed: {e}")
            return []

class QueryRouter:
    """Phase 1: Simple router that returns default strategy."""
    
    def get_strategy(self, intent: str, facts: Dict) -> Dict[str, Any]:
        # Start dead simple - we'll enhance this in Phase 2
        return {
            "indices": ["authority"],
            "max_chunks": 6,
            "include_history": False,
            "focus_areas": []
        }

class AgenticRAG:
    """Phase 2: Intelligent RAG with query planning and decomposition."""
    
    def __init__(self):
        self.parser = QueryParser()
        self.vector_store = VectorStoreWrapper()
        self.identity_math = IdentityMath()
        self.trust_engine = TrustEngine()
        self.router = QueryRouter()
        self.max_chunks = 6
        self.max_steps = 4  # NEW: limit iterations
        self.decomposition_cache = {}  # NEW: cache plans
    
    async def handle_query(self, user_id: int, message: str, db: Session) -> Dict[str, Any]:
        """
        Phase 1: Basic query handling without fancy planning.
        Just prove the pipeline works end-to-end.
        """
        try:
            # Step 1: Parse the query
            intent = self.parser.parse(message)
            logger.info(f"Parsed intent: {intent['intent']}")
            
            # Step 2: Get user facts
            facts = self.identity_math.compute_claims(user_id, db)
            if "error" in facts:
                return {
                    "response_markdown": "Please update your financial profile first.",
                    "insight_cards": [],
                    "citations": [],
                    "confidence": "LOW",
                    "warnings": ["missing_profile"]
                }
            logger.info(f"Got facts for user {user_id}: {list(facts.keys())}")
            
            # Step 3: Simple vector search (no planning yet)
            search_results = await self.vector_store.query(
                index="authority",
                query=message,
                filters={"limit": 5}
            )
            logger.info(f"Vector search returned {len(search_results)} results")
            
            # Step 4: Package evidence (simplified)
            evidence = []
            for result in search_results[:self.max_chunks]:
                evidence.append({
                    "text": result.get("text", ""),
                    "source": result.get("source", "unknown"),
                    "doc_id": result.get("doc_id", "unknown"),
                    "score": result.get("score", 0.0)
                })
            
            # Step 5: Basic LLM response (no fancy prompting yet)
            # Try to use a registered LLM provider (fallback to openai if gemini not available)
            available_providers = ["openai", "gemini", "claude"]
            selected_provider = "openai"  # Default fallback
            
            for provider in available_providers:
                if provider in llm_service.clients:
                    selected_provider = provider
                    break
            
            llm_request = LLMRequest(
                provider=selected_provider,
                model_tier="dev", 
                system_prompt="You are a financial advisor. Answer based on the context provided.",
                user_prompt=f"Context: {json.dumps(facts)[:1000]}\n\nQuestion: {message}",
                temperature=0.3
            )
            llm_response = await llm_service.generate(llm_request)
            
            # Step 6: Return basic response
            return {
                "response": llm_response.content[:500],  # Truncate for safety
                "insight_cards": [],
                "citations": [f"{e['source']}#{e['doc_id']}" for e in evidence],
                "confidence": "MEDIUM",
                "warnings": []
            }
            
        except Exception as e:
            logger.error(f"Phase 1 RAG failed: {e}")
            return {
                "response": f"Error in Phase 1: {str(e)}",
                "insight_cards": [],
                "citations": [],
                "confidence": "LOW", 
                "warnings": ["phase1_error"]
            }