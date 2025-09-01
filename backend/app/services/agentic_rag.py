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
    """Phase 3: Intelligent RAG with iterative refinement and sufficiency checking."""
    
    def __init__(self):
        self.parser = QueryParser()
        self.vector_store = VectorStoreWrapper()
        self.identity_math = IdentityMath()
        self.trust_engine = TrustEngine()
        self.router = QueryRouter()
        self.max_chunks = 6
        self.max_steps = 4  # NEW: limit iterations
        self.max_iterations = 2  # Phase 3: iterative refinement limit
        self.decomposition_cache = {}  # NEW: cache plans

    async def handle_query(self, user_id: int, message: str, db: Session) -> Dict[str, Any]:
        """Phase 3: Add iterative refinement and sufficiency checking."""
        try:
            # Steps 1-2: Same as Phase 1
            intent = self.parser.parse(message)
            logger.info(f"Parsed intent: {intent['intent']}")
            
            facts = self.identity_math.compute_claims(user_id, db)
            if "error" in facts:
                return {
                    "response": "Please update your financial profile first.",
                    "insight_cards": [],
                    "citations": [],
                    "confidence": "LOW",
                    "warnings": ["missing_profile"]
                }
            logger.info(f"Got facts for user {user_id}: {list(facts.keys())}")
            
            # NEW Step 3: Plan the query
            plan = await self._plan_query(message, intent, facts)
            logger.info(f"Generated plan with {len(plan['steps'])} steps")
            
            # NEW Step 4: Execute the plan with iterative refinement (Phase 3)
            context = await self._execute_plan_with_refinement(plan, user_id, facts, message)
            logger.info(f"Executed plan with refinement, got {len(context['search_results'])} total results")
            
            # Step 5: Rank and package evidence intelligently (Phase 3)
            evidence = self._rank_and_package_evidence(context)
            logger.info(f"Ranked and packaged {len(evidence)} evidence items")
            
            # Step 6: Generate intelligent response with gap awareness (Phase 3)
            response = await self._generate_intelligent_response(message, facts, evidence, intent, context.get('gaps', []))
            
            return response
            
        except Exception as e:
            logger.error(f"Phase 3 RAG failed: {e}")
            import traceback
            logger.error(f"Phase 3 traceback: {traceback.format_exc()}")
            return {
                "response": f"Error in Phase 3: {str(e)}",
                "insight_cards": [],
                "citations": [],
                "confidence": "LOW",
                "warnings": ["phase3_error"]
            }

    async def _plan_query(self, message: str, intent: Dict, facts: Dict) -> Dict:
        """NEW: Decompose query into sub-questions."""
        
        # Check cache first
        cache_key = md5(f"{message}_{intent['intent']}".encode()).hexdigest()
        if cache_key in self.decomposition_cache:
            logger.info("Using cached plan")
            return self.decomposition_cache[cache_key]
        
        # Try LLM decomposition
        try:
            decomposition_prompt = f"""
            Break down this financial query into 2-3 specific sub-questions.
            
            Query: {message}
            User context: Age {facts.get('_context', {}).get('age', 'unknown')}, 
                         State: {facts.get('_context', {}).get('state', 'unknown')}
            Intent type: {intent['intent']}
            
            Return a JSON array of steps:
            [
                {{"step": 1, "question": "...", "search_query": "...", "index": "authority"}},
                {{"step": 2, "question": "...", "search_query": "...", "index": "authority"}}
            ]
            
            Keep it simple - max 3 steps.
            """
            
            # Try to use a registered LLM provider
            available_providers = ["openai", "gemini", "claude"]
            selected_provider = "openai"  # Default fallback
            
            for provider in available_providers:
                if provider in llm_service.clients:
                    selected_provider = provider
                    break
            
            llm_request = LLMRequest(
                provider=selected_provider,
                model_tier="dev",
                system_prompt="You are a query planner. Return only valid JSON.",
                user_prompt=decomposition_prompt,
                temperature=0.3
            )
            llm_response = await llm_service.generate(llm_request)
            
            # Parse the response
            steps = json.loads(llm_response.content)
            plan = {"steps": steps[:self.max_steps], "original_query": message}
            
        except Exception as e:
            logger.warning(f"Decomposition failed, using fallback: {e}")
            # Fallback to simple plan
            plan = {
                "steps": [
                    {"step": 1, "question": message, "search_query": message, "index": "authority"}
                ],
                "original_query": message
            }
        
        # Cache the plan
        self.decomposition_cache[cache_key] = plan
        return plan
    
    async def _execute_plan(self, plan: Dict, user_id: int, facts: Dict) -> Dict:
        """NEW: Execute each step of the plan."""
        context = {
            "rules": [],
            "facts": facts,
            "search_results": []
        }
        
        for step in plan["steps"]:
            logger.info(f"Executing step {step.get('step', 0)}: {step.get('question', '')}")
            
            # Search based on the step
            results = await self.vector_store.query(
                index=step.get("index", "authority"),
                query=step.get("search_query", plan["original_query"]),
                filters={"limit": 3}  # Fewer results per step
            )
            
            # Add to context
            for result in results:
                context["search_results"].append({
                    "text": result.get("text", ""),
                    "source": result.get("source", "unknown"),
                    "doc_id": result.get("doc_id", "unknown"),
                    "score": result.get("score", 0.0),
                    "from_step": step.get("step", 0)
                })
        
        return context
    
    async def _execute_plan_with_refinement(self, plan: Dict, user_id: int, facts: Dict, original_query: str) -> Dict:
        """Phase 3: Execute plan with iterative refinement and sufficiency checking."""
        context = {
            "rules": [],
            "facts": facts,
            "search_results": [],
            "gaps": [],
            "iterations": 0
        }
        
        # Execute initial plan
        for step in plan["steps"]:
            logger.info(f"Executing initial step {step.get('step', 0)}: {step.get('question', '')}")
            
            results = await self.vector_store.query(
                index=step.get("index", "authority"),
                query=step.get("search_query", plan["original_query"]),
                filters={"limit": 3}
            )
            
            for result in results:
                context["search_results"].append({
                    "text": result.get("text", ""),
                    "source": result.get("source", "unknown"),
                    "doc_id": result.get("doc_id", "unknown"),
                    "score": result.get("score", 0.0),
                    "from_step": step.get("step", 0),
                    "iteration": 0
                })
        
        # Iterative refinement
        for iteration in range(1, self.max_iterations + 1):
            logger.info(f"Starting refinement iteration {iteration}")
            context["iterations"] = iteration
            
            # Assess sufficiency
            sufficiency = await self._assess_sufficiency(original_query, context, facts)
            logger.info(f"Sufficiency assessment - sufficient: {sufficiency['sufficient']}, gaps: {len(sufficiency['gaps'])}")
            
            if sufficiency["sufficient"]:
                logger.info("Information deemed sufficient, stopping refinement")
                break
            
            # Store gaps for response generation
            context["gaps"] = sufficiency["gaps"]
            
            # Generate follow-up searches
            follow_ups = await self._generate_follow_up_searches(original_query, sufficiency["gaps"], facts)
            logger.info(f"Generated {len(follow_ups)} follow-up searches")
            
            # Execute follow-up searches
            for search in follow_ups:
                logger.info(f"Executing follow-up search: {search['query']}")
                
                results = await self.vector_store.query(
                    index="authority",
                    query=search["query"],
                    filters={"limit": 2}  # Fewer results per follow-up
                )
                
                for result in results:
                    context["search_results"].append({
                        "text": result.get("text", ""),
                        "source": result.get("source", "unknown"),
                        "doc_id": result.get("doc_id", "unknown"),
                        "score": result.get("score", 0.0) + 0.1,  # Bonus for follow-up
                        "from_step": search.get("for_gap", "follow_up"),
                        "iteration": iteration,
                        "gap_target": search.get("gap_type", "unknown")
                    })
        
        return context
    
    async def _assess_sufficiency(self, query: str, context: Dict, facts: Dict) -> Dict:
        """Phase 3: Assess if we have sufficient information to answer the query."""
        evidence_text = "\n".join([f"- {r['text'][:200]}..." for r in context["search_results"][:5]])
        
        assessment_prompt = f"""
        Assess if we have sufficient information to answer this financial question comprehensively.
        
        Query: {query}
        
        User Context:
        - Age: {facts.get('_context', {}).get('age', 'unknown')}
        - Net Worth: ${facts.get('net_worth', 0):,.2f}
        - State: {facts.get('_context', {}).get('state', 'unknown')}
        
        Available Evidence:
        {evidence_text}
        
        Return JSON with this structure:
        {{
            "sufficient": true/false,
            "confidence": 0.0-1.0,
            "gaps": [
                {{"gap_type": "tax_implications", "description": "Missing state tax information"}},
                {{"gap_type": "timeline", "description": "No retirement timeline specified"}}
            ],
            "reasoning": "Brief explanation"
        }}
        
        Consider gaps in: tax implications, timeline/age factors, risk tolerance, state-specific rules, income details, expense analysis.
        """
        
        try:
            available_providers = ["openai", "gemini", "claude"]
            selected_provider = "openai"
            
            for provider in available_providers:
                if provider in llm_service.clients:
                    selected_provider = provider
                    break
            
            llm_request = LLMRequest(
                provider=selected_provider,
                model_tier="dev",
                system_prompt="You are an assessment engine. Return only valid JSON.",
                user_prompt=assessment_prompt,
                temperature=0.2
            )
            llm_response = await llm_service.generate(llm_request)
            
            assessment = json.loads(llm_response.content)
            return assessment
            
        except Exception as e:
            logger.warning(f"Sufficiency assessment failed: {e}")
            # Conservative fallback - always assume more info might be helpful
            return {
                "sufficient": len(context["search_results"]) >= 4,
                "confidence": 0.6,
                "gaps": [{"gap_type": "general", "description": "Assessment unavailable"}],
                "reasoning": "Fallback assessment"
            }
    
    async def _generate_follow_up_searches(self, original_query: str, gaps: List[Dict], facts: Dict) -> List[Dict]:
        """Phase 3: Generate targeted follow-up searches based on identified gaps."""
        if not gaps:
            return []
        
        gap_descriptions = "\n".join([f"- {gap['gap_type']}: {gap['description']}" for gap in gaps])
        
        follow_up_prompt = f"""
        Generate 1-2 specific follow-up search queries to fill these information gaps.
        
        Original Query: {original_query}
        
        Identified Gaps:
        {gap_descriptions}
        
        User Context:
        - Age: {facts.get('_context', {}).get('age', 'unknown')}
        - State: {facts.get('_context', {}).get('state', 'unknown')}
        
        Return JSON array:
        [
            {{"query": "specific search query", "gap_type": "tax_implications", "for_gap": "tax rules"}},
            {{"query": "another search query", "gap_type": "timeline", "for_gap": "retirement planning"}}
        ]
        
        Keep searches specific and actionable.
        """
        
        try:
            available_providers = ["openai", "gemini", "claude"]
            selected_provider = "openai"
            
            for provider in available_providers:
                if provider in llm_service.clients:
                    selected_provider = provider
                    break
            
            llm_request = LLMRequest(
                provider=selected_provider,
                model_tier="dev",
                system_prompt="You are a search query generator. Return only valid JSON.",
                user_prompt=follow_up_prompt,
                temperature=0.3
            )
            llm_response = await llm_service.generate(llm_request)
            
            follow_ups = json.loads(llm_response.content)
            return follow_ups[:2]  # Limit to 2 follow-ups
            
        except Exception as e:
            logger.warning(f"Follow-up generation failed: {e}")
            # Simple fallback based on gaps
            fallback_searches = []
            for gap in gaps[:2]:
                fallback_searches.append({
                    "query": f"{original_query} {gap['gap_type']} considerations",
                    "gap_type": gap["gap_type"],
                    "for_gap": gap["description"]
                })
            return fallback_searches
    
    def _rank_and_package_evidence(self, context: Dict) -> List[Dict]:
        """Phase 3: Smart evidence ranking with iteration bonuses."""
        evidence = []
        
        for result in context["search_results"]:
            # Base score
            score = result.get("score", 0.0)
            
            # Iteration bonus (later iterations get bonus for gap-filling)
            iteration_bonus = result.get("iteration", 0) * 0.05
            
            # Gap-targeting bonus
            gap_bonus = 0.1 if result.get("gap_target") else 0.0
            
            # Final score
            final_score = score + iteration_bonus + gap_bonus
            
            evidence.append({
                "text": result["text"][:500],
                "source": result["source"],
                "doc_id": result["doc_id"],
                "score": final_score,
                "iteration": result.get("iteration", 0),
                "gap_target": result.get("gap_target")
            })
        
        # Sort by final score and take top chunks
        evidence.sort(key=lambda x: x["score"], reverse=True)
        return evidence[:self.max_chunks]
    
    def _package_evidence(self, context: Dict) -> List[Dict]:
        """Enhanced evidence packaging."""
        evidence = []
        
        # Sort by score and take top chunks
        sorted_results = sorted(
            context["search_results"], 
            key=lambda x: x.get("score", 0.0), 
            reverse=True
        )
        
        for result in sorted_results[:self.max_chunks]:
            evidence.append({
                "text": result["text"][:500],  # Truncate long text
                "source": result["source"],
                "doc_id": result["doc_id"],
                "score": result["score"]
            })
        
        return evidence
    
    async def _generate_response(self, message: str, facts: Dict, evidence: List[Dict], intent: Dict) -> Dict:
        """NEW: Better response generation."""
        
        # Build context from evidence
        evidence_text = "\n".join([f"- {e['text']}" for e in evidence])
        
        # Enhanced prompt
        prompt = f"""
        You are a financial advisor. Answer the user's question using the provided facts and evidence.
        
        User Question: {message}
        
        User Facts:
        - Net Worth: ${facts.get('net_worth', 0):,.2f}
        - Monthly Surplus: ${facts.get('monthly_surplus', 0):,.2f}
        - Age: {facts.get('_context', {}).get('age', 'unknown')}
        
        Relevant Information:
        {evidence_text}
        
        Provide a clear, actionable answer. Be specific with numbers and recommendations.
        """
        
        # Try to use a registered LLM provider
        available_providers = ["openai", "gemini", "claude"]
        selected_provider = "openai"  # Default fallback
        
        for provider in available_providers:
            if provider in llm_service.clients:
                selected_provider = provider
                break
        
        llm_request = LLMRequest(
            provider=selected_provider,
            model_tier="dev",
            system_prompt="You are a helpful financial advisor.",
            user_prompt=prompt,
            temperature=0.3
        )
        llm_response = await llm_service.generate(llm_request)
        
        # Determine confidence based on evidence
        confidence = "HIGH" if len(evidence) >= 3 else "MEDIUM" if len(evidence) >= 1 else "LOW"
        
        return {
            "response": llm_response.content,
            "insight_cards": [],  # We'll add these in Phase 3
            "citations": [f"{e['source']}#{e['doc_id']}" for e in evidence],
            "confidence": confidence,
            "warnings": []
        }