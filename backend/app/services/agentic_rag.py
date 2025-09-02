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
from app.services.core_prompts import core_prompts

logger = logging.getLogger(__name__)

# Import debug payload storage
try:
    from app.api.v1.endpoints.debug import store_llm_payload
except ImportError:
    # Fallback if debug module not available
    def store_llm_payload(user_id, payload):
        pass

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

    async def handle_query(self, user_id: int, message: str, db: Session, mode: str = "balanced") -> Dict[str, Any]:
        """Phase 3: Add iterative refinement and sufficiency checking."""
        logger.info(f"🎛️ Mode in handle_query: {mode}")
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
            response = await self._generate_intelligent_response(user_id, message, facts, evidence, intent, context.get('gaps', []), mode)
            
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
            first_name = facts.get('_context', {}).get('first_name', 'User')
            age = facts.get('_context', {}).get('age', 'unknown')
            state = facts.get('_context', {}).get('state', 'unknown')
            
            decomposition_prompt = f"""
            You are a financial query planner. Break down user questions into precise 
            sub-questions categorized as FACT, RULE, or PATTERN. 
            Return only valid JSON.
            
            Break down this query into 2–3 sub-questions.
            
            Query: {message}
            User context: Name {first_name}, Age {age}, State {state}, Intent {intent['intent']}
            
            Return JSON:
            [
              {{"step": 1, "type": "FACT", "question": "...", "index": "facts"}},
              {{"step": 2, "type": "RULE", "question": "...", "index": "authority"}},
              {{"step": 3, "type": "PATTERN", "question": "...", "index": "history"}}
            ]
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
                system_prompt="You are a financial query planner. Return only valid JSON.",
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
            
            search_query = step.get("search_query", plan["original_query"])
            index = step.get("index", "authority")
            filters = {"limit": 3}
            
            # CRITICAL DEBUG LOGGING
            logger.error(f"🔍 ABOUT TO SEARCH: query='{search_query}', index='{index}', filters={filters}")
            
            results = await self.vector_store.query(
                index=index,
                query=search_query,
                filters=filters
            )
            
            # CRITICAL RESULT LOGGING
            logger.error(f"🔍 VECTOR SEARCH RETURNED: {len(results)} results for query: '{search_query}'")
            if results:
                logger.info(f"First result preview: {results[0].get('text', '')[:100]}...")
                logger.info(f"Result sources: {[r.get('source', 'unknown') for r in results]}")
            else:
                logger.warning(f"No results returned for search query: '{search_query}'")
            
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
                search_query = search["query"]
                logger.info(f"Executing follow-up search: {search_query}")
                
                results = await self.vector_store.query(
                    index="authority",
                    query=search_query,
                    filters={"limit": 2}  # Fewer results per follow-up
                )
                
                # ADD DEBUG LOGGING FOR FOLLOW-UP
                logger.info(f"Follow-up search returned {len(results)} results for: '{search_query}'")
                if results:
                    logger.info(f"Follow-up result sources: {[r.get('source', 'unknown') for r in results]}")
                
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
        
        # Force iteration logic for testing and real gaps
        unique_sources = len(set(r['doc_id'] for r in context['search_results']))
        unique_source_types = len(set(r['source'] for r in context['search_results']))
        current_iteration = context.get("iterations", 0)
        
        logger.info(f"Sufficiency check - Sources: {unique_sources}, Source types: {unique_source_types}, Iteration: {current_iteration}")
        
        # Identify specific gaps based on query content
        query_lower = query.lower()
        potential_gaps = []
        
        # Gap detection logic
        if any(word in query_lower for word in ['tax', 'taxes', 'deduction', 'rmd', 'distribution']) and facts.get('_context', {}).get('state') == 'unknown':
            potential_gaps.append({"gap_type": "state_tax_rules", "description": "Missing state-specific tax information"})
        
        if any(word in query_lower for word in ['retire', 'retirement', 'timeline', 'when']) and not any('age' in r['text'].lower() for r in context['search_results']):
            potential_gaps.append({"gap_type": "retirement_timeline", "description": "No age-specific retirement guidance found"})
        
        if any(word in query_lower for word in ['risk', 'allocation', 'investment']) and not any('risk' in r['text'].lower() for r in context['search_results']):
            potential_gaps.append({"gap_type": "risk_assessment", "description": "Missing risk tolerance analysis"})
        
        if any(word in query_lower for word in ['401k', 'ira', 'contribution', 'limit']) and not any('limit' in r['text'].lower() for r in context['search_results']):
            potential_gaps.append({"gap_type": "contribution_limits", "description": "Current year contribution limits not found"})
        
        # Force iteration conditions
        force_iteration = (
            unique_sources < 3 or  # Need more diverse sources
            unique_source_types < 2 or  # Need different types of information
            len(potential_gaps) > 0 or  # Detected specific gaps
            len(context['search_results']) < 4  # Not enough total evidence
        )
        
        # Don't iterate beyond max_iterations
        if current_iteration >= self.max_iterations:
            force_iteration = False
        
        assessment_prompt = f"""
        Assess if we have sufficient information to answer this financial question comprehensively.
        
        Query: {query}
        
        User Context:
        - Age: {facts.get('_context', {}).get('age', 'unknown')}
        - Net Worth: ${facts.get('net_worth', 0):,.2f}
        - State: {facts.get('_context', {}).get('state', 'unknown')}
        
        Available Evidence ({len(context['search_results'])} results from {unique_sources} unique sources):
        {evidence_text}
        
        Current iteration: {current_iteration}/{self.max_iterations}
        
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
        
        Be STRICT - financial advice requires comprehensive information. Consider gaps in: tax implications, timeline/age factors, risk tolerance, state-specific rules, income details, expense analysis, current regulations.
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
                system_prompt="You are a strict assessment engine. Financial advice requires comprehensive information. Return only valid JSON.",
                user_prompt=assessment_prompt,
                temperature=0.2
            )
            llm_response = await llm_service.generate(llm_request)
            
            assessment = json.loads(llm_response.content)
            
            # Override with forced iteration logic if needed
            if force_iteration and current_iteration < self.max_iterations:
                assessment["sufficient"] = False
                if not assessment.get("gaps"):
                    assessment["gaps"] = potential_gaps or [{"gap_type": "insufficient_sources", "description": f"Only {unique_sources} unique sources found"}]
                logger.info(f"Forcing iteration due to insufficient evidence: {len(context['search_results'])} results, {unique_sources} sources")
            
            return assessment
            
        except Exception as e:
            logger.warning(f"Sufficiency assessment failed: {e}")
            # More aggressive fallback - force iteration if we don't have much info
            gaps = potential_gaps or [{"gap_type": "general", "description": "LLM assessment unavailable, need more sources"}]
            
            return {
                "sufficient": not force_iteration,  # Use force_iteration logic
                "confidence": 0.4,  # Lower confidence when assessment fails
                "gaps": gaps if force_iteration else [],
                "reasoning": f"Fallback assessment - {unique_sources} sources, {len(context['search_results'])} results"
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
    
    async def _generate_intelligent_response(self, user_id: int, message: str, facts: Dict, evidence: List[Dict], intent: Dict, gaps: List[Dict], mode: str = "balanced") -> Dict:
        """Phase 3: Intelligent response generation with gap awareness."""
        logger.info(f"🎛️ Mode in _generate_intelligent_response: {mode}")
        
        # Build context from evidence with iteration info
        logger.info(f"🔍 Evidence pieces passed to response generation: {len(evidence)}")
        for i, e in enumerate(evidence):
            logger.info(f"  Evidence {i+1}: {e.get('text', 'NO TEXT')[:100]}... (score: {e.get('score', 0):.2f})")
        
        evidence_text = "\n".join([
            f"- {e['text']} (iteration: {e.get('iteration', 0)}, score: {e.get('score', 0):.2f})" 
            for e in evidence
        ])
        
        logger.info(f"📝 Evidence text length: {len(evidence_text)} chars")
        
        # Gap information
        gap_text = ""
        if gaps:
            gap_descriptions = "\n".join([f"- {gap.get('gap_type', 'unknown')}: {gap.get('description', 'no description')}" for gap in gaps])
            gap_text = f"\n\nNote: Some information gaps were identified:\n{gap_descriptions}\nAcknowledge these limitations in your response."
        
        # Enhanced prompt with gap awareness
        prompt = f"""
        You are a financial advisor. Answer the user's question using the provided facts and evidence.
        
        User Question: {message}
        
        User Facts:
        - Net Worth: ${facts.get('net_worth', 0):,.2f}
        - Monthly Surplus: ${facts.get('monthly_surplus', 0):,.2f}
        - Age: {facts.get('_context', {}).get('age', 'unknown')}
        
        Available Evidence (with search iteration details):
        {evidence_text}
        {gap_text}
        
        Provide a clear, actionable answer. Be specific with numbers and recommendations.
        If there are information gaps, acknowledge them and provide the best guidance possible with available data.
        """
        
        # Try to use a registered LLM provider
        available_providers = ["openai", "gemini", "claude"]
        selected_provider = "openai"  # Default fallback
        
        for provider in available_providers:
            if provider in llm_service.clients:
                selected_provider = provider
                break
        
        # Generate mode-specific prompts
        logger.info(f"🎛️ About to generate prompts for mode: {mode}")
        if mode == "direct":
            system_prompt = """You are a precise financial data assistant. 
            Provide a single factual sentence, grounded only in the provided numbers. 
            If the user's name is available, address them directly."""
            
            # Extract user name
            first_name = facts.get('_context', {}).get('first_name', 'User')
            
            user_prompt = f"""
            Question: {message}
            Facts: {json.dumps(facts, indent=2)}
            Name: {first_name}
            
            Answer with exactly one sentence.
            
            {f"Note: Answer limited due to {[gap.get('description', 'missing data') for gap in gaps]}" if gaps else ""}
            """
            temperature = 0.1
            
        elif mode == "comprehensive":
            system_prompt = """You are an expert financial strategist providing full advisory reports. 
            Always personalize using the user's name. 
            Provide structured, professional responses that mimic a human financial advisor. 
            Ground everything in facts and context — never hallucinate numbers."""
            
            # Extract comprehensive user context for human-advisor replacement
            first_name = facts.get('_context', {}).get('first_name', 'User')
            age = facts.get('_context', {}).get('age', 'unknown')
            state = facts.get('_context', {}).get('state', 'unknown') 
            filing_status = facts.get('_context', {}).get('filing_status', 'unknown')
            risk_tolerance = facts.get('_context', {}).get('risk_tolerance', 'moderate')
            fi_progress = facts.get('FI_progress', 'unknown')
            retirement_timeline = facts.get('_context', {}).get('retirement_timeline', 'unknown')
            
            user_prompt = f"""
            Question: {message}
            
            Complete Financial Picture:
            {json.dumps(facts, indent=2)}
            
            Context:
            - Name: {first_name}
            - Age: {age}
            - State: {state}
            - Filing Status: {filing_status}
            - Risk Tolerance: {risk_tolerance}
            - FI Progress: {fi_progress}
            - Retirement Timeline: {retirement_timeline}
            
            Deliver your response in four sections:
            
            1. {first_name}'s Current Position 
               - Restate facts and ratios in plain English
            2. Patterns & Risks
               - Non-obvious trends, vulnerabilities, tax/state-specific considerations
            3. Strategic Opportunities
               - Advanced wealth, tax, and retirement strategies personalized to context
            4. Behavioral Considerations
               - Biases, decision habits, lifestyle trade-offs, goal alignment
            
            Keep tone professional and advisor-like. Always use {first_name}'s name throughout.
            """
            temperature = 0.5
            
        else:  # balanced
            system_prompt = """You are a professional financial advisor. 
            Provide a concise but insightful response that combines facts with personalized analysis. 
            Always address the user by name if available."""
            
            # Limited evidence for balanced mode (top 3 pieces)
            limited_evidence = evidence[:3] if evidence else []
            
            # Extract comprehensive user context for advisor-level analysis
            first_name = facts.get('_context', {}).get('first_name', 'User')
            age = facts.get('_context', {}).get('age', 'unknown')
            state = facts.get('_context', {}).get('state', 'unknown')
            risk_tolerance = facts.get('_context', {}).get('risk_tolerance', 'moderate')
            fi_progress = facts.get('FI_progress', 'unknown')
            
            user_prompt = f"""
            Question: {message}
            
            Financial Facts:
            {json.dumps(facts, indent=2)}
            
            User Context:
            - Name: {first_name}
            - Age: {age}
            - State: {state}
            - Risk Tolerance: {risk_tolerance}
            - FI Progress: {fi_progress}
            
            Answer with:
            1. Direct factual answer addressed to the user by name
            2. Two personalized insights referencing age, state, and FI progress
            3. One practical, next-step recommendation
            
            {f"Note: Limited by {[gap.get('description', 'missing data') for gap in gaps]}" if gaps else ""}
            """
            temperature = 0.3
        
        llm_request = LLMRequest(
            provider=selected_provider,
            model_tier="dev",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            mode=mode,
            temperature=temperature
        )
        llm_response = await llm_service.generate(llm_request)
        
        # Store LLM payload for debugging
        store_llm_payload(user_id, {
            "query": message,
            "provider": selected_provider,
            "model_tier": "dev",
            "system_prompt": system_prompt,
            "user_message": user_prompt,
            "context_used": json.dumps({
                "agentic_rag_used": True,
                "evidence_count": len(evidence),
                "gaps_identified": len(gaps),
                "iterations_performed": max([e.get('iteration', 0) for e in evidence]) if evidence else 0,
                "mode": mode,
                "temperature": temperature
            }),
            "llm_response": llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
        })
        
        # Enhanced confidence assessment
        base_confidence = min(len(evidence), 6) / 6.0  # 0.0 to 1.0 based on evidence count
        gap_penalty = len(gaps) * 0.1 if gaps else 0.0
        iteration_bonus = min(sum([e.get('iteration', 0) for e in evidence]) * 0.05, 0.2)
        
        final_confidence = max(0.2, min(1.0, base_confidence - gap_penalty + iteration_bonus))
        
        if final_confidence >= 0.75:
            confidence_level = "HIGH"
        elif final_confidence >= 0.5:
            confidence_level = "MEDIUM"
        else:
            confidence_level = "LOW"
        
        warnings = []
        if gaps:
            warnings.append("information_gaps_identified")
        
        return {
            "response": llm_response.content,
            "insight_cards": [],  # Future enhancement
            "citations": [f"{e['source']}#{e['doc_id']}" for e in evidence],
            "confidence": confidence_level,
            "warnings": warnings,
            "gaps_identified": len(gaps),
            "iterations_performed": max([e.get('iteration', 0) for e in evidence]) if evidence else 0
        }
    
    def _format_evidence(self, evidence: List[Dict]) -> str:
        """Format evidence for inclusion in prompts"""
        if not evidence:
            return "No relevant historical context found."
        
        formatted = []
        for i, e in enumerate(evidence[:5]):  # Limit to top 5 pieces
            text = e.get('text', 'No content')[:300]  # Truncate long content
            score = e.get('score', 0)
            iteration = e.get('iteration', 0)
            formatted.append(f"Evidence {i+1} (score: {score:.2f}, iteration: {iteration}): {text}")
        
        return "\n".join(formatted)