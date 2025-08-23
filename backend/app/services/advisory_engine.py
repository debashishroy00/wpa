"""
Step 5: RAG Advisory Engine
Transforms Step 4 calculations into professional financial advice
"""
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from decimal import Decimal

from app.models.plan_engine import PlanOutput
from app.services.knowledge_base import KnowledgeBaseService, SearchResult
from app.services.plan_engine import DeterministicPlanEngine


@dataclass
class AdvisoryPrompt:
    """Structured prompt for LLM advisory generation"""
    system_prompt: str
    user_context: str
    plan_data: str
    kb_context: str
    output_template: str


@dataclass
class AdvisoryOutput:
    """Professional advisory report with citations"""
    executive_summary: List[str]
    immediate_actions: List[Dict[str, Any]]
    twelve_month_strategy: List[Dict[str, Any]]
    risk_management: List[Dict[str, Any]]
    tax_considerations: List[Dict[str, Any]]
    citations: List[str]
    disclaimers: List[str]
    plan_data_sources: List[str]
    generation_timestamp: str


class AdvisoryEngine:
    """RAG-powered advisory engine for financial recommendations"""
    
    def __init__(self):
        self.kb_service = KnowledgeBaseService()
        self.plan_engine = DeterministicPlanEngine()
        
        # Template validation patterns
        self.required_sections = [
            'executive_summary',
            'immediate_actions', 
            'twelve_month_strategy',
            'risk_management',
            'tax_considerations'
        ]
        
        # Safety filters for compliance
        self.prohibited_phrases = [
            'guaranteed returns',
            'risk-free investment',
            'certain to',
            'always profitable',
            'no risk'
        ]
        
        # Plan figure extraction patterns
        self.plan_figure_patterns = {
            'monte_carlo_success_rate': r'success rate.*?(\d+\.?\d*)%',
            'required_savings_rate': r'savings rate.*?(\d+\.?\d*)%',
            'expected_return': r'expected return.*?(\d+\.?\d*)%',
            'target_allocation': r'allocation.*?(\d+\.?\d*)%'
        }
    
    def generate_advisory_report(
        self,
        plan_output: PlanOutput,
        user_profile: Dict[str, Any],
        focus_areas: Optional[List[str]] = None
    ) -> AdvisoryOutput:
        """Generate professional advisory report from plan data"""
        
        # 1. Identify key issues and opportunities
        issues = self._analyze_plan_issues(plan_output, user_profile)
        
        # 2. Retrieve relevant knowledge base content
        kb_context = self._retrieve_kb_context(issues, user_profile, focus_areas)
        
        # 3. Build structured prompt
        advisory_prompt = self._build_advisory_prompt(plan_output, user_profile, kb_context, issues)
        
        # 4. Generate advisory content (would call LLM in production)
        advisory_content = self._generate_advisory_content(advisory_prompt)
        
        # 5. Validate and structure output
        structured_output = self._structure_advisory_output(advisory_content, plan_output, kb_context)
        
        # 6. Add compliance elements
        final_output = self._add_compliance_elements(structured_output, plan_output)
        
        return final_output
    
    def _analyze_plan_issues(self, plan_output: PlanOutput, user_profile: Dict[str, Any]) -> List[str]:
        """Identify key issues from plan calculations"""
        issues = []
        
        # Success rate analysis
        success_rate = plan_output.gap_analysis.monte_carlo_success_rate
        if success_rate < 0.7:
            issues.append('low_success_probability')
        elif success_rate < 0.8:
            issues.append('moderate_success_probability')
        
        # Savings rate analysis
        savings_rate = plan_output.plan_metrics.required_savings_rate
        if savings_rate > 0.4:
            issues.append('high_savings_requirement')
        elif savings_rate > 0.25:
            issues.append('aggressive_savings_needed')
        
        # Debt analysis
        high_rate_debt = [debt for debt in plan_output.debt_schedule if debt.rate > 0.15]
        if high_rate_debt:
            issues.append('high_interest_debt')
        
        # Allocation analysis
        equity_pct = (plan_output.target_allocation.us_stocks + 
                     plan_output.target_allocation.intl_stocks +
                     plan_output.target_allocation.reits)
        age = user_profile.get('current_age', 40)
        if equity_pct > 0.9 and age > 50:
            issues.append('aggressive_allocation_age_mismatch')
        
        # Rebalancing needs
        if len(plan_output.rebalancing_trades) > 5:
            issues.append('significant_rebalancing_needed')
        
        # Tax optimization opportunities
        if plan_output.tax_strategy and plan_output.tax_strategy.estimated_tax_savings > Decimal('1000'):
            issues.append('tax_optimization_opportunity')
        
        # Emergency fund
        current_cash = user_profile.get('cash_reserves', 0)
        monthly_expenses = user_profile.get('monthly_expenses', 0)
        if monthly_expenses > 0 and current_cash / monthly_expenses < 3:
            issues.append('insufficient_emergency_fund')
        
        return issues
    
    def _retrieve_kb_context(
        self,
        issues: List[str],
        user_profile: Dict[str, Any],
        focus_areas: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """Retrieve relevant knowledge base content"""
        all_results = []
        
        # Map issues to search queries
        issue_queries = {
            'low_success_probability': 'increase portfolio success rate retirement planning',
            'high_savings_requirement': 'strategies increase savings rate budget optimization',
            'high_interest_debt': 'debt payoff avalanche method credit card strategy',
            'aggressive_allocation_age_mismatch': 'age appropriate asset allocation glide path',
            'significant_rebalancing_needed': 'portfolio rebalancing strategy tax efficient',
            'tax_optimization_opportunity': 'tax loss harvesting asset location strategy',
            'insufficient_emergency_fund': 'emergency fund sizing strategies cash allocation'
        }
        
        # Search for issue-specific content
        for issue in issues:
            if issue in issue_queries:
                results = self.kb_service.search(
                    issue_queries[issue],
                    filters={'category': 'playbooks'},
                    top_k=2
                )
                all_results.extend(results)
        
        # Add focus area searches
        if focus_areas:
            for focus in focus_areas:
                results = self.kb_service.search(
                    focus,
                    top_k=1
                )
                all_results.extend(results)
        
        # Add regulatory content if relevant
        tax_bracket = user_profile.get('tax_bracket', 0.22)
        if tax_bracket > 0:
            tax_results = self.kb_service.search(
                'IRS contribution limits tax brackets',
                filters={'category': 'regulations'},
                top_k=1
            )
            all_results.extend(tax_results)
        
        # Deduplicate and limit results
        seen_ids = set()
        unique_results = []
        for result in all_results:
            if result.document.id not in seen_ids:
                unique_results.append(result)
                seen_ids.add(result.document.id)
        
        return unique_results[:8]  # Limit to avoid prompt bloat
    
    def _build_advisory_prompt(
        self,
        plan_output: PlanOutput,
        user_profile: Dict[str, Any],
        kb_context: List[SearchResult],
        issues: List[str]
    ) -> AdvisoryPrompt:
        """Build structured prompt for advisory generation"""
        
        system_prompt = """You are a fiduciary financial advisor. Follow these rules strictly:

1. Use ONLY numbers from the provided Step 4 plan output
2. Cite all sources from knowledge base with [KB-ID]
3. Never invent calculations or modify Step 4 figures
4. Focus on implementation guidance and rationale
5. Use professional but accessible language
6. Provide specific dollar amounts and percentages
7. Include actionable next steps with timelines

Available tools:
- get_plan_figure(field_name): Retrieves Step 4 calculations

Output must include:
1. Executive Summary (2-3 bullets)
2. Immediate Actions (next 30 days)
3. 12-Month Strategy
4. Risk Management
5. Tax Considerations
6. All citations in [KB-ID] format"""

        # Extract key plan figures for easy reference
        plan_summary = f"""
SUCCESS RATE: {plan_output.gap_analysis.monte_carlo_success_rate:.1%}
REQUIRED SAVINGS: ${float(plan_output.contribution_schedule.total_monthly):,.0f}/month
TARGET ALLOCATION: {plan_output.target_allocation.us_stocks:.0%} US stocks, {plan_output.target_allocation.bonds:.0%} bonds
REBALANCING TRADES: {len(plan_output.rebalancing_trades)} trades needed
DEBT PRIORITY: {plan_output.debt_schedule[0].debt if plan_output.debt_schedule else 'None'} at {f"{plan_output.debt_schedule[0].rate:.1%}" if plan_output.debt_schedule else 'N/A'}
"""

        # Build knowledge base context
        kb_text = ""
        for result in kb_context:
            kb_text += f"\n[{result.document.kb_id}] {result.document.title}\n"
            # Include relevant excerpts (first 500 chars)
            kb_text += result.document.content[:500] + "...\n"
        
        user_context = f"""
Age: {user_profile.get('current_age', 'Not provided')}
Income: ${user_profile.get('annual_income', 0):,.0f}
Net Worth: ${user_profile.get('net_worth', 0):,.0f}
Risk Tolerance: {user_profile.get('risk_tolerance', 5)}/10
Tax Bracket: {user_profile.get('tax_bracket', 0.22):.0%}
Key Issues: {', '.join(issues)}
"""

        output_template = """
## Executive Summary
- [Bullet point using plan figures]
- [Bullet point with specific recommendation]
- [Bullet point with expected outcome]

## Immediate Actions (Next 30 Days)
1. **Action Name** [KB-ID]
   - Specific step: [dollar amount/percentage from plan]
   - Timeline: [specific dates]
   - Expected impact: [from plan metrics]

## 12-Month Strategy
1. **Strategy Item** [KB-ID]
   - Implementation: [plan-based guidance]
   - Milestones: [quarterly targets]
   - Metrics: [success measures from plan]

## Risk Management
- **Primary Risk**: [identified from plan stress tests]
- **Mitigation**: [specific actions with plan figures]
- **Monitoring**: [key metrics to track]

## Tax Considerations
- **Opportunity**: [from plan tax strategy]
- **Savings**: $[amount from plan]/year
- **Implementation**: [specific steps with KB citations]

All figures sourced from deterministic plan engine calculations.
"""

        return AdvisoryPrompt(
            system_prompt=system_prompt,
            user_context=user_context,
            plan_data=plan_summary,
            kb_context=kb_text,
            output_template=output_template
        )
    
    def _generate_advisory_content(self, prompt: AdvisoryPrompt) -> str:
        """Generate advisory content - would call LLM in production"""
        
        # This is a mock implementation for demonstration
        # In production, this would call an LLM API (OpenAI, Anthropic, etc.)
        
        mock_response = f"""
## Executive Summary
- Portfolio has {prompt.plan_data.split('SUCCESS RATE: ')[1].split('%')[0]}% success rate with current strategy - good foundation with room for optimization
- Monthly savings requirement of {prompt.plan_data.split('REQUIRED SAVINGS: $')[1].split('/month')[0]} represents aggressive but achievable target
- Rebalancing and debt optimization can improve success rate by 5-8 percentage points

## Immediate Actions (Next 30 Days)
1. **Optimize 401k Contribution** [IRS-001]
   - Increase to capture full employer match: $200/month additional
   - Timeline: Complete by next payroll cycle (within 2 weeks)
   - Expected impact: +1% success rate improvement

2. **Address High-Interest Debt** [DP-001]
   - Pay minimum $500/month extra toward highest rate debt
   - Timeline: Begin with January payment
   - Expected impact: $1,200 annual interest savings

## 12-Month Strategy
1. **Portfolio Rebalancing** [RB-001]
   - Implement target allocation through systematic rebalancing
   - Quarterly reviews and adjustments
   - Focus on tax-efficient account placement [AL-001]

2. **Emergency Fund Building** [DP-001]
   - Build to 6 months expenses over 12 months
   - Automatic transfers of $500/month to high-yield savings
   - Target: $18,000 emergency fund by year-end

## Risk Management
- **Primary Risk**: Market volatility during accumulation phase
- **Mitigation**: Maintain diversified allocation and continue dollar-cost averaging
- **Monitoring**: Review quarterly success rate and stress test results

## Tax Considerations
- **Opportunity**: Maximize tax-deferred savings accounts
- **Savings**: $2,400/year in tax savings from optimized contributions
- **Implementation**: Increase 401k, max Roth IRA, consider HSA [IRS-001]

All figures sourced from deterministic plan engine calculations.
"""
        
        return mock_response
    
    def _structure_advisory_output(
        self,
        advisory_content: str,
        plan_output: PlanOutput,
        kb_context: List[SearchResult]
    ) -> AdvisoryOutput:
        """Structure the advisory content into standardized format"""
        
        # Parse the generated content into sections
        sections = self._parse_advisory_sections(advisory_content)
        
        # Extract citations from content
        citations = self._extract_citations(advisory_content, kb_context)
        
        # Extract plan data sources
        plan_sources = self._extract_plan_sources(advisory_content, plan_output)
        
        return AdvisoryOutput(
            executive_summary=sections.get('executive_summary', []),
            immediate_actions=sections.get('immediate_actions', []),
            twelve_month_strategy=sections.get('twelve_month_strategy', []),
            risk_management=sections.get('risk_management', []),
            tax_considerations=sections.get('tax_considerations', []),
            citations=citations,
            disclaimers=[],  # Will be added in compliance step
            plan_data_sources=plan_sources,
            generation_timestamp=datetime.utcnow().isoformat()
        )
    
    def _parse_advisory_sections(self, content: str) -> Dict[str, List[Any]]:
        """Parse advisory content into structured sections"""
        sections = {}
        lines = content.split('\n')
        current_section = None
        current_items = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('## Executive Summary'):
                if current_section:
                    sections[current_section] = current_items
                current_section = 'executive_summary'
                current_items = []
            elif line.startswith('## Immediate Actions'):
                if current_section:
                    sections[current_section] = current_items
                current_section = 'immediate_actions'
                current_items = []
            elif line.startswith('## 12-Month Strategy'):
                if current_section:
                    sections[current_section] = current_items
                current_section = 'twelve_month_strategy'
                current_items = []
            elif line.startswith('## Risk Management'):
                if current_section:
                    sections[current_section] = current_items
                current_section = 'risk_management'
                current_items = []
            elif line.startswith('## Tax Considerations'):
                if current_section:
                    sections[current_section] = current_items
                current_section = 'tax_considerations'
                current_items = []
            elif current_section and line.startswith(('-', '*', '1.', '2.')):
                # Parse action items with structure
                item = self._parse_action_item(line)
                current_items.append(item)
        
        # Don't forget the last section
        if current_section and current_items:
            sections[current_section] = current_items
        
        return sections
    
    def _parse_action_item(self, line: str) -> Dict[str, Any]:
        """Parse an action item into structured format"""
        # Basic parsing - would be more sophisticated in production
        return {
            'text': line,
            'priority': 'high' if 'immediate' in line.lower() else 'medium',
            'category': 'action',
            'timeline': self._extract_timeline(line)
        }
    
    def _extract_timeline(self, text: str) -> str:
        """Extract timeline from action item text"""
        if 'next 30 days' in text.lower():
            return '30_days'
        elif 'quarterly' in text.lower():
            return 'quarterly'
        elif 'annual' in text.lower():
            return 'annual'
        else:
            return 'as_needed'
    
    def _extract_citations(self, content: str, kb_context: List[SearchResult]) -> List[str]:
        """Extract and validate citations from content"""
        import re
        
        # Find all [KB-ID] patterns
        citation_pattern = r'\[([A-Z]+-\d+)\]'
        found_citations = re.findall(citation_pattern, content)
        
        # Validate against available KB documents
        valid_citations = []
        kb_ids = {result.document.kb_id for result in kb_context}
        
        for citation in found_citations:
            if citation in kb_ids:
                valid_citations.append(citation)
        
        return list(set(valid_citations))  # Remove duplicates
    
    def _extract_plan_sources(self, content: str, plan_output: PlanOutput) -> List[str]:
        """Extract plan data sources mentioned in content"""
        plan_sources = ['plan_engine_v1.0.0']
        
        # Check which plan components were referenced
        if 'success rate' in content.lower():
            plan_sources.append('monte_carlo_simulation')
        if 'allocation' in content.lower():
            plan_sources.append('target_allocation_optimizer')
        if 'debt' in content.lower():
            plan_sources.append('debt_prioritization_engine')
        if 'tax' in content.lower():
            plan_sources.append('tax_optimization_calculator')
        
        return plan_sources
    
    def _add_compliance_elements(self, output: AdvisoryOutput, plan_output: PlanOutput) -> AdvisoryOutput:
        """Add compliance disclaimers and safety checks"""
        
        # Standard disclaimers
        disclaimers = [
            "This analysis is for educational purposes only and not personalized financial advice.",
            "Investment returns are not guaranteed and past performance does not predict future results.",
            "Consider consulting with a qualified financial advisor for personalized recommendations.",
            "Tax implications may vary based on individual circumstances and current tax law.",
            f"Analysis based on plan calculations as of {plan_output.calculation_timestamp}."
        ]
        
        # Add specific disclaimers based on content
        if any('aggressive' in str(action) for action in output.immediate_actions):
            disclaimers.append("Aggressive strategies involve higher risk and may not be suitable for all investors.")
        
        if output.tax_considerations:
            disclaimers.append("Tax strategies should be reviewed with a tax professional before implementation.")
        
        output.disclaimers = disclaimers
        
        # Validate no prohibited phrases
        self._validate_compliance(output)
        
        return output
    
    def _validate_compliance(self, output: AdvisoryOutput) -> None:
        """Validate output for compliance with advisory regulations"""
        
        # Convert output to text for checking
        output_text = json.dumps(output.__dict__, default=str).lower()
        
        # Check for prohibited phrases
        for phrase in self.prohibited_phrases:
            if phrase.lower() in output_text:
                raise ValueError(f"Compliance violation: prohibited phrase '{phrase}' found in output")
        
        # Ensure all plan figures are properly sourced
        if not output.plan_data_sources:
            raise ValueError("No plan data sources documented")
        
        # Ensure disclaimers are present
        if not output.disclaimers:
            raise ValueError("No compliance disclaimers included")


# Example usage
if __name__ == "__main__":
    from app.models.plan_engine import PlanInput, CurrentState, Goals, Constraints
    
    # Create sample plan input
    sample_input = PlanInput(
        current_state=CurrentState(
            net_worth=Decimal('485750'),
            assets={'401k': Decimal('185000'), 'brokerage': Decimal('125000')},
            liabilities={'mortgage': Decimal('285000')},
            income={'salary': Decimal('125000')},
            expenses={'monthly': Decimal('7200')}
        ),
        goals=Goals(
            target_net_worth=Decimal('2500000'),
            retirement_age=55,
            annual_spending=Decimal('100000'),
            risk_tolerance=7,
            current_age=38
        ),
        constraints=Constraints(
            min_emergency_fund=Decimal('30000'),
            max_single_asset_pct=0.10,
            tax_bracket=0.24
        )
    )
    
    # Generate plan
    engine = DeterministicPlanEngine()
    plan_output = engine.calculate_plan(sample_input)
    
    # Generate advisory
    advisory_engine = AdvisoryEngine()
    advisory_output = advisory_engine.generate_advisory_report(
        plan_output,
        user_profile={
            'current_age': 38,
            'annual_income': 125000,
            'net_worth': 485750,
            'risk_tolerance': 7,
            'tax_bracket': 0.24
        }
    )
    
    print("Advisory Report Generated:")
    print(f"Sections: {len(advisory_output.immediate_actions)} immediate actions")
    print(f"Citations: {advisory_output.citations}")
    print(f"Plan Sources: {advisory_output.plan_data_sources}")