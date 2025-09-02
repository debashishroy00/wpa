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
from app.services.comprehensive_financial_calculator import comprehensive_calculator
from app.services.calculation_router import calculation_router

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

    async def handle_query(self, user_id: int, message: str, db: Session, mode: str = "balanced", session_id: str = None) -> Dict[str, Any]:
        """Phase 3: Add iterative refinement and sufficiency checking."""
        logger.info(f"🎛️ Mode in handle_query: {mode}")
        
        # Get conversation history for context
        try:
            conversation_history = self._get_conversation_history(user_id, session_id, db) if session_id else []
            logger.info(f"Retrieved {len(conversation_history)} messages from conversation history")
        except Exception as e:
            logger.warning(f"Failed to retrieve conversation history: {e}")
            conversation_history = []
        
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
            
            # NEW: Check if this query requires mathematical calculation
            calculation_info = calculation_router.detect_calculation_needed(message, conversation_history)
            if calculation_info:
                logger.info(f"🧮 Mathematical calculation detected: {calculation_info['calculation_type']}")
                return await self._handle_calculation(calculation_info, message, facts, user_id, mode, conversation_history)
            
            logger.info(f"No calculation needed, proceeding with regular RAG flow")
            
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
            response = await self._generate_intelligent_response(user_id, message, facts, evidence, intent, context.get('gaps', []), mode, conversation_history)
            
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
    
    def _enforce_specificity(self, prompt: str, mode: str) -> str:
        """Ultra-aggressive specificity enforcement"""
        return prompt  # Ultra-specific prompts handle this directly now
    
    def _validate_ultra_specific_response(self, response: str, mode: str) -> Dict[str, Any]:
        """Check if response meets ultra-specificity requirements"""
        
        validation_results = {
            "is_valid": True,
            "violations": [],
            "missing_elements": []
        }
        
        if mode == "comprehensive":
            # Ultra-banned words list
            banned_words = [
                "consider", "review", "explore", "evaluate", "analyze", 
                "prioritize", "warrant", "potentially", "might", "could", 
                "would", "should", "beneficial", "advisable", "prudent",
                "recommend reviewing", "you may want", "it might be good",
                "think about", "look into", "worth exploring"
            ]
            
            response_lower = response.lower()
            for word in banned_words:
                if word in response_lower:
                    validation_results["is_valid"] = False
                    validation_results["violations"].append(f"Banned word: '{word}'")
            
            # Required elements for ultra-specificity
            required_elements = [
                ("$", "Dollar amounts"),
                ("%", "Percentages"),
                ("call", "Phone action"),
                ("by ", "Specific dates"),
                ("save", "Savings calculations")
            ]
            
            for element, description in required_elements:
                if element not in response_lower:
                    validation_results["missing_elements"].append(description)
        
        return validation_results

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
    
    async def _generate_intelligent_response(self, user_id: int, message: str, facts: Dict, evidence: List[Dict], intent: Dict, gaps: List[Dict], mode: str = "balanced", conversation_history: List[Dict] = None) -> Dict:
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
        
        # Build comprehensive evidence text with proper formatting
        formatted_evidence = self._format_evidence_for_prompt(evidence)
        
        # Enhanced prompt that REQUIRES using evidence
        prompt = f"""
        You are a financial advisor with access to the user's complete financial database.
        
        User Question: {message}
        
        CORE FINANCIAL FACTS:
        - Net Worth: ${facts.get('net_worth', 0):,.2f}
        - Monthly Income: ${facts.get('monthly_income', 0):,.2f}
        - Monthly Expenses: ${facts.get('monthly_expenses', 0):,.2f}
        - Monthly Surplus: ${facts.get('monthly_surplus', 0):,.2f}
        - Investment Total: ${facts.get('investment_total', 0):,.2f}
        - Retirement Total: ${facts.get('retirement_total', 0):,.2f}
        - Age: {facts.get('_context', {}).get('age', 'unknown')}
        - State: {facts.get('_context', {}).get('state', 'unknown')}
        
        RETRIEVED DETAILED DATA FROM DATABASE:
        {formatted_evidence}
        {gap_text}
        
        CRITICAL INSTRUCTIONS:
        1. USE THE DETAILED DATA ABOVE to answer the question
        2. If asked about expenses → use expense breakdown from retrieved data
        3. If asked about income → use income breakdown from retrieved data  
        4. If asked about assets → use asset allocation from retrieved data
        5. If asked about goals → use financial goals from retrieved data
        6. If asked about insurance/estate → use estate & insurance data
        7. NEVER make up categories or amounts - use ONLY what's provided above
        8. Always cite specific numbers from the retrieved data
        
        Answer the question using the specific data provided above.
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
        
        # Format conversation history for all modes
        history_text = ""
        if conversation_history and len(conversation_history) > 0:
            history_text = "\nCONVERSATION HISTORY:\n"
            for msg in conversation_history:
                history_text += f"{msg['role'].title()}: {msg['content']}\n"
            history_text += f"\nCURRENT QUESTION: {message}\n"
        
        if mode == "direct":
            system_prompt = """You are a precise financial data assistant. 
            Provide a direct, factual answer using the specific data provided."""
            
            # Extract user name
            first_name = facts.get('_context', {}).get('first_name', 'User')
            
            # Format evidence properly
            formatted_evidence = self._format_evidence_for_prompt(evidence)
            
            user_prompt = f"""
            Question: {message}
            
            {history_text}
            
            Core Facts: {json.dumps(facts, indent=2)}
            
            DETAILED DATA FROM DATABASE:
            {formatted_evidence}
            
            Name: {first_name}
            
            Instructions:
            - If asked about specific categories (expenses, income, assets, etc.), use the detailed data above
            - Provide a direct, factual answer with specific numbers
            - Keep response concise but complete
            - If this is a follow-up question, build on previous context
            
            {f"Note: Answer limited due to {[gap.get('description', 'missing data') for gap in gaps]}" if gaps else ""}
            """
            temperature = 0.1
            
        elif mode == "comprehensive":
            # Extract THIS user's actual data - no hardcoding!
            first_name = facts.get('_context', {}).get('first_name', 'User')
            age = facts.get('_context', {}).get('age', 'unknown')
            state = facts.get('_context', {}).get('state', 'unknown')
            net_worth = facts.get('net_worth', 0)
            monthly_surplus = facts.get('monthly_surplus', 0)
            investment_total = facts.get('investment_total', 0)
            
            system_prompt = f"""You are a sophisticated financial advisor with access to complete financial data for a client with:
            - Net worth: ${net_worth:,.0f}
            - Age: {age}
            - State: {state}
            - Monthly surplus: ${monthly_surplus:,.0f}
            - Current investments: ${investment_total:,.0f}
            
            IMPORTANT: Use ALL the evidence and data provided below to answer questions accurately."""
            
            user_prompt = f"""
            Client: {first_name}, Age {age}, {state}
            Question: {message}
            
            {history_text}
            
            Their Complete Financial Data:
            {json.dumps(facts, indent=2)}
            
            RETRIEVED EVIDENCE FROM DATABASE:
            {self._format_evidence_for_prompt(evidence)}
            
            CRITICAL INSTRUCTIONS:
            1. If asked about expenses, use the expense breakdown from the evidence above
            2. If asked about assets, use the asset allocation from the evidence above
            3. If asked about goals, use the financial goals from the evidence above
            4. Always cite specific numbers from the data and evidence provided
            5. Never make up categories or amounts - use only what's provided
            6. If there's conversation history, consider context from previous questions
            7. For follow-up questions, reference previous answers and build upon them
            
            Answer their question using the specific data provided above and conversation context.
            """
            
            temperature = 0.4  # Allow more natural variation
            
        else:  # balanced
            # Extract THIS user's actual data - no hardcoded values
            first_name = facts.get('_context', {}).get('first_name', 'User')
            age = facts.get('_context', {}).get('age', 'unknown')
            state = facts.get('_context', {}).get('state', 'unknown')
            net_worth = facts.get('net_worth', 0)
            
            system_prompt = f"""You are a financial advisor for a {age}-year-old in {state} with ${net_worth:,.0f} net worth.
            
            Use the evidence and data provided to give accurate, specific answers."""
            
            user_prompt = f"""
            Question: {message}
            
            Client: {first_name}, Age {age}, {state}
            
            {history_text}
            
            Financial Data: {json.dumps(facts, indent=2)}
            
            EVIDENCE FROM DATABASE:
            {self._format_evidence_for_prompt(evidence)}
            
            Instructions:
            1. Answer with specific numbers from the data/evidence above
            2. Explain what this means for their situation
            3. Suggest one concrete action
            4. If there's conversation history, build upon previous context
            
            If asked about expenses, use the expense breakdown from evidence.
            If asked about assets, use the asset allocation from evidence.
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
        
        # Let the response be natural and intelligent - no more validation constraints
        
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
    
    def _format_evidence_for_prompt(self, evidence: List[Dict]) -> str:
        """Format evidence with full content for accurate data retrieval"""
        if not evidence:
            return "No detailed data retrieved from database."
        
        formatted = []
        for i, e in enumerate(evidence):
            source = e.get('source', 'unknown')
            text = e.get('text', 'No content')  # Don't truncate - we need full data
            
            # Add clear headers for different data types
            if 'expense' in source.lower():
                formatted.append(f"\n=== EXPENSE BREAKDOWN ===\n{text}")
            elif 'income' in source.lower():
                formatted.append(f"\n=== INCOME BREAKDOWN ===\n{text}")
            elif 'asset' in source.lower() or 'allocation' in source.lower():
                formatted.append(f"\n=== ASSET ALLOCATION ===\n{text}")
            elif 'goal' in source.lower():
                formatted.append(f"\n=== FINANCIAL GOALS ===\n{text}")
            elif 'insurance' in source.lower() or 'estate' in source.lower():
                formatted.append(f"\n=== ESTATE & INSURANCE ===\n{text}")
            elif 'summary' in source.lower():
                formatted.append(f"\n=== FINANCIAL SUMMARY ===\n{text}")
            else:
                formatted.append(f"\n=== ADDITIONAL DATA (from {source}) ===\n{text}")
        
        return "\n".join(formatted) if formatted else "No detailed data retrieved."
    
    def _get_conversation_history(self, user_id: int, session_id: str, db: Session) -> List[Dict[str, str]]:
        """Get recent conversation history for context"""
        try:
            from app.models.chat import ChatSession, ChatMessage
            
            # Find the session
            session = db.query(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatSession.session_id == session_id,
                ChatSession.is_active == True
            ).first()
            
            if not session:
                return []
            
            # Get last 6 messages (3 exchanges)
            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session.id
            ).order_by(ChatMessage.created_at.desc()).limit(6).all()
            
            # Reverse to get chronological order
            messages.reverse()
            
            # Format for prompt
            history = []
            for msg in messages:
                history.append({
                    "role": msg.role,
                    "content": msg.content[:200] + "..." if len(msg.content) > 200 else msg.content,
                    "timestamp": msg.created_at.isoformat()
                })
            
            return history
            
        except Exception as e:
            logger.warning(f"Failed to get conversation history: {e}")
            return []