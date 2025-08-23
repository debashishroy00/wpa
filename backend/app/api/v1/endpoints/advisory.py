"""
Step 5: Advisory Engine API Endpoints
RAG-powered advisory generation with citation tracking
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import json
from decimal import Decimal

from app.db.session import get_db
from app.models.plan_engine import PlanInput, PlanOutput
from app.services.plan_engine import DeterministicPlanEngine
from app.services.advisory_engine import AdvisoryEngine, AdvisoryOutput
from app.services.knowledge_base import KnowledgeBaseService
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.post("/generate", response_model=Dict[str, Any])
async def generate_advisory_report(
    plan_input: PlanInput,
    focus_areas: Optional[List[str]] = None,
    output_format: str = Query("full", enum=["full", "summary", "actions_only"]),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate professional advisory report from plan data
    Combines Step 4 calculations with RAG knowledge base
    """
    try:
        # Generate deterministic plan first
        plan_engine = DeterministicPlanEngine()
        plan_output = plan_engine.calculate_plan(plan_input)
        
        # Extract user profile from plan input and authenticated user
        user_profile = {
            'user_id': current_user.id if current_user else None,
            'user_name': f"{current_user.first_name} {current_user.last_name}" if current_user and current_user.first_name else "User",
            'user_email': current_user.email if current_user else None,
            'current_age': plan_input.goals.current_age,
            'annual_income': float(sum(plan_input.current_state.income.values())),
            'net_worth': float(plan_input.current_state.net_worth),
            'risk_tolerance': plan_input.goals.risk_tolerance,
            'tax_bracket': plan_input.constraints.tax_bracket,
            'monthly_expenses': float(sum(plan_input.current_state.expenses.values())),
            'cash_reserves': float(sum(
                v for k, v in plan_input.current_state.assets.items()
                if 'cash' in k.lower() or 'savings' in k.lower()
            ))
        }
        
        # Generate advisory report
        advisory_engine = AdvisoryEngine()
        advisory_output = advisory_engine.generate_advisory_report(
            plan_output=plan_output,
            user_profile=user_profile,
            focus_areas=focus_areas
        )
        
        # Format output based on requested format
        if output_format == "summary":
            response = _format_summary_output(advisory_output, plan_output)
        elif output_format == "actions_only":
            response = _format_actions_output(advisory_output)
        else:
            response = _format_full_output(advisory_output, plan_output)
        
        # Log advisory generation for audit
        _log_advisory_generation(db, current_user.id, plan_input, advisory_output)
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Advisory generation error")


@router.post("/validate-citations")
async def validate_citations(
    advisory_content: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Validate citations in advisory content
    Ensures all KB-IDs reference actual knowledge base documents
    """
    try:
        kb_service = KnowledgeBaseService()
        
        # Extract citations from content
        import re
        citation_pattern = r'\[([A-Z]+-\d+)\]'
        found_citations = re.findall(citation_pattern, advisory_content)
        
        validation_results = {
            "total_citations": len(found_citations),
            "valid_citations": [],
            "invalid_citations": [],
            "missing_documents": []
        }
        
        # Check each citation
        for citation in set(found_citations):  # Remove duplicates
            # Find document by KB-ID
            documents = [doc for doc in kb_service.documents if doc.kb_id == citation]
            
            if documents:
                validation_results["valid_citations"].append({
                    "kb_id": citation,
                    "title": documents[0].title,
                    "category": documents[0].category
                })
            else:
                validation_results["invalid_citations"].append(citation)
        
        # Overall validation status
        validation_results["is_valid"] = len(validation_results["invalid_citations"]) == 0
        
        return validation_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Citation validation error: {str(e)}")


@router.get("/knowledge-base/search")
async def search_knowledge_base(
    query: str = Query(..., min_length=3),
    category: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
    top_k: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Search knowledge base for relevant content
    Supports semantic search with category and tag filtering
    """
    try:
        kb_service = KnowledgeBaseService()
        
        # Build filters
        filters = {}
        if category:
            filters['category'] = category
        if tags:
            filters['tags'] = tags
        
        # Perform search
        results = kb_service.search(query, filters=filters, top_k=top_k)
        
        # Format results for API response
        formatted_results = []
        for result in results:
            formatted_results.append({
                "kb_id": result.document.kb_id,
                "title": result.document.title,
                "category": result.document.category,
                "excerpt": result.document.content[:300] + "..." if len(result.document.content) > 300 else result.document.content,
                "score": round(result.score, 3),
                "relevance_explanation": result.relevance_explanation,
                "tags": result.document.tags
            })
        
        return {
            "query": query,
            "total_results": len(formatted_results),
            "results": formatted_results,
            "available_categories": kb_service.list_categories()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Knowledge base search error: {str(e)}")


@router.get("/knowledge-base/document/{kb_id}")
async def get_knowledge_base_document(
    kb_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Retrieve full knowledge base document by KB-ID
    Used for citation verification and detailed content access
    """
    try:
        kb_service = KnowledgeBaseService()
        
        # Find document by KB-ID
        documents = [doc for doc in kb_service.documents if doc.kb_id == kb_id]
        
        if not documents:
            raise HTTPException(status_code=404, detail=f"Document {kb_id} not found")
        
        document = documents[0]
        
        # Get related documents
        related = kb_service.get_related_documents(document.id, top_k=3)
        
        return {
            "kb_id": document.kb_id,
            "title": document.title,
            "category": document.category,
            "content": document.content,
            "tags": document.tags,
            "last_updated": document.last_updated,
            "file_path": document.file_path,
            "related_documents": [
                {
                    "kb_id": rel.document.kb_id,
                    "title": rel.document.title,
                    "score": round(rel.score, 3)
                }
                for rel in related
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document retrieval error: {str(e)}")


@router.get("/templates")
async def get_advisory_templates(
    template_type: str = Query("full", enum=["full", "summary", "checklist"]),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get advisory report templates for different output formats
    Helps ensure consistent formatting and required sections
    """
    templates = {
        "full": {
            "sections": [
                {
                    "name": "executive_summary",
                    "title": "Executive Summary",
                    "description": "2-3 key takeaways with specific figures",
                    "required": True
                },
                {
                    "name": "immediate_actions",
                    "title": "Immediate Actions (Next 30 Days)",
                    "description": "Specific actionable steps with timelines",
                    "required": True
                },
                {
                    "name": "twelve_month_strategy",
                    "title": "12-Month Strategy",
                    "description": "Long-term implementation plan",
                    "required": True
                },
                {
                    "name": "risk_management",
                    "title": "Risk Management",
                    "description": "Risk mitigation strategies",
                    "required": True
                },
                {
                    "name": "tax_considerations",
                    "title": "Tax Considerations",
                    "description": "Tax optimization opportunities",
                    "required": True
                }
            ],
            "citation_format": "[KB-ID]",
            "required_disclaimers": [
                "Educational purposes only",
                "Not personalized financial advice",
                "Past performance not predictive"
            ]
        },
        "summary": {
            "sections": [
                {
                    "name": "key_insights",
                    "title": "Key Insights",
                    "description": "Top 3 insights from analysis",
                    "required": True
                },
                {
                    "name": "priority_actions",
                    "title": "Priority Actions",
                    "description": "Top 3 recommended actions",
                    "required": True
                }
            ]
        },
        "checklist": {
            "sections": [
                {
                    "name": "immediate_checklist",
                    "title": "30-Day Action Checklist",
                    "description": "Checkboxes for immediate actions",
                    "required": True
                },
                {
                    "name": "quarterly_checklist",
                    "title": "Quarterly Review Checklist",
                    "description": "Ongoing monitoring tasks",
                    "required": True
                }
            ]
        }
    }
    
    return {
        "template_type": template_type,
        "template": templates.get(template_type, templates["full"]),
        "available_types": list(templates.keys())
    }


@router.post("/compare-scenarios")
async def compare_advisory_scenarios(
    base_plan: PlanInput,
    alternative_scenarios: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Compare advisory recommendations across different scenarios
    Useful for sensitivity analysis and what-if planning
    """
    try:
        plan_engine = DeterministicPlanEngine()
        advisory_engine = AdvisoryEngine()
        
        # Generate base scenario
        base_plan_output = plan_engine.calculate_plan(base_plan)
        base_profile = _extract_user_profile(base_plan)
        base_advisory = advisory_engine.generate_advisory_report(base_plan_output, base_profile)
        
        # Generate alternative scenarios
        scenario_results = []
        for i, scenario_changes in enumerate(alternative_scenarios):
            # Apply changes to base plan
            modified_plan = _apply_scenario_changes(base_plan, scenario_changes)
            
            # Generate plan and advisory
            scenario_plan_output = plan_engine.calculate_plan(modified_plan)
            scenario_profile = _extract_user_profile(modified_plan)
            scenario_advisory = advisory_engine.generate_advisory_report(scenario_plan_output, scenario_profile)
            
            scenario_results.append({
                "scenario_id": i + 1,
                "changes": scenario_changes,
                "success_rate": scenario_plan_output.gap_analysis.monte_carlo_success_rate,
                "required_savings": float(scenario_plan_output.contribution_schedule.total_monthly),
                "key_differences": _compare_advisories(base_advisory, scenario_advisory),
                "advisory_summary": {
                    "executive_summary": scenario_advisory.executive_summary,
                    "immediate_actions_count": len(scenario_advisory.immediate_actions),
                    "risk_level": _assess_risk_level(scenario_plan_output)
                }
            })
        
        return {
            "base_scenario": {
                "success_rate": base_plan_output.gap_analysis.monte_carlo_success_rate,
                "required_savings": float(base_plan_output.contribution_schedule.total_monthly),
                "advisory_summary": {
                    "executive_summary": base_advisory.executive_summary,
                    "immediate_actions_count": len(base_advisory.immediate_actions)
                }
            },
            "alternative_scenarios": scenario_results,
            "comparison_summary": _generate_comparison_summary(base_plan_output, scenario_results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scenario comparison error: {str(e)}")


def _format_full_output(advisory_output: AdvisoryOutput, plan_output: PlanOutput) -> Dict[str, Any]:
    """Format complete advisory output"""
    return {
        "report_type": "full_advisory",
        "generation_timestamp": advisory_output.generation_timestamp,
        "plan_calculation_timestamp": plan_output.calculation_timestamp,
        "executive_summary": advisory_output.executive_summary,
        "immediate_actions": advisory_output.immediate_actions,
        "twelve_month_strategy": advisory_output.twelve_month_strategy,
        "risk_management": advisory_output.risk_management,
        "tax_considerations": advisory_output.tax_considerations,
        "supporting_data": {
            "success_rate": plan_output.gap_analysis.monte_carlo_success_rate,
            "required_monthly_savings": float(plan_output.contribution_schedule.total_monthly),
            "target_allocation": {
                "stocks": plan_output.target_allocation.us_stocks + plan_output.target_allocation.intl_stocks,
                "bonds": plan_output.target_allocation.bonds,
                "alternatives": plan_output.target_allocation.reits + plan_output.target_allocation.cash
            }
        },
        "citations": advisory_output.citations,
        "plan_data_sources": advisory_output.plan_data_sources,
        "disclaimers": advisory_output.disclaimers
    }


def _format_summary_output(advisory_output: AdvisoryOutput, plan_output: PlanOutput) -> Dict[str, Any]:
    """Format summary advisory output"""
    return {
        "report_type": "summary",
        "key_insights": advisory_output.executive_summary,
        "priority_actions": advisory_output.immediate_actions[:3],  # Top 3 actions
        "success_rate": plan_output.gap_analysis.monte_carlo_success_rate,
        "monthly_savings_target": float(plan_output.contribution_schedule.total_monthly),
        "primary_citations": advisory_output.citations[:3],
        "disclaimers": ["Educational content only", "Not personalized advice"]
    }


def _format_actions_output(advisory_output: AdvisoryOutput) -> Dict[str, Any]:
    """Format actions-only output"""
    all_actions = []
    
    # Combine immediate and strategic actions
    for action in advisory_output.immediate_actions:
        all_actions.append({
            **action,
            "timeframe": "immediate",
            "priority": "high"
        })
    
    for action in advisory_output.twelve_month_strategy:
        all_actions.append({
            **action,
            "timeframe": "strategic",
            "priority": "medium"
        })
    
    return {
        "report_type": "actions_checklist",
        "total_actions": len(all_actions),
        "actions": all_actions,
        "citations": advisory_output.citations
    }


def _extract_user_profile(plan_input: PlanInput) -> Dict[str, Any]:
    """Extract user profile from plan input"""
    return {
        'current_age': plan_input.goals.current_age,
        'annual_income': float(sum(plan_input.current_state.income.values())),
        'net_worth': float(plan_input.current_state.net_worth),
        'risk_tolerance': plan_input.goals.risk_tolerance,
        'tax_bracket': plan_input.constraints.tax_bracket,
        'monthly_expenses': float(sum(plan_input.current_state.expenses.values())),
        'cash_reserves': float(sum(
            v for k, v in plan_input.current_state.assets.items()
            if 'cash' in k.lower() or 'savings' in k.lower()
        ))
    }


def _apply_scenario_changes(base_plan: PlanInput, changes: Dict[str, Any]) -> PlanInput:
    """Apply scenario changes to base plan"""
    import copy
    modified_plan = copy.deepcopy(base_plan)
    
    # Apply changes based on scenario type
    if 'income_change' in changes:
        income_multiplier = changes['income_change']
        for key in modified_plan.current_state.income:
            modified_plan.current_state.income[key] *= Decimal(str(income_multiplier))
    
    if 'retirement_age_change' in changes:
        modified_plan.goals.retirement_age += changes['retirement_age_change']
    
    if 'risk_tolerance_change' in changes:
        new_risk = modified_plan.goals.risk_tolerance + changes['risk_tolerance_change']
        modified_plan.goals.risk_tolerance = max(1, min(10, new_risk))
    
    # Recalculate net worth if assets changed
    modified_plan.current_state.net_worth = (
        sum(modified_plan.current_state.assets.values()) - 
        sum(modified_plan.current_state.liabilities.values())
    )
    
    return modified_plan


def _compare_advisories(base: AdvisoryOutput, scenario: AdvisoryOutput) -> List[str]:
    """Compare two advisory outputs and highlight differences"""
    differences = []
    
    # Compare action counts
    if len(scenario.immediate_actions) != len(base.immediate_actions):
        differences.append(f"Action count changed: {len(base.immediate_actions)} → {len(scenario.immediate_actions)}")
    
    # Compare citations (indicates different knowledge areas accessed)
    base_citations = set(base.citations)
    scenario_citations = set(scenario.citations)
    
    if base_citations != scenario_citations:
        new_citations = scenario_citations - base_citations
        if new_citations:
            differences.append(f"New knowledge areas: {', '.join(new_citations)}")
    
    return differences


def _assess_risk_level(plan_output: PlanOutput) -> str:
    """Assess overall risk level of plan"""
    success_rate = plan_output.gap_analysis.monte_carlo_success_rate
    savings_rate = plan_output.plan_metrics.required_savings_rate
    
    if success_rate > 0.85 and savings_rate < 0.2:
        return "low"
    elif success_rate > 0.7 and savings_rate < 0.35:
        return "moderate"
    else:
        return "high"


def _generate_comparison_summary(base_plan: PlanOutput, scenarios: List[Dict]) -> Dict[str, Any]:
    """Generate summary of scenario comparison"""
    success_rates = [s['success_rate'] for s in scenarios] + [base_plan.gap_analysis.monte_carlo_success_rate]
    savings_amounts = [s['required_savings'] for s in scenarios] + [float(base_plan.contribution_schedule.total_monthly)]
    
    return {
        "success_rate_range": {
            "min": min(success_rates),
            "max": max(success_rates),
            "spread": max(success_rates) - min(success_rates)
        },
        "savings_range": {
            "min": min(savings_amounts),
            "max": max(savings_amounts),
            "spread": max(savings_amounts) - min(savings_amounts)
        },
        "recommendation": "Consider scenario with highest success rate within acceptable savings range"
    }


def _log_advisory_generation(db: Session, user_id: int, plan_input: PlanInput, advisory_output: AdvisoryOutput):
    """Log advisory generation for audit trail"""
    # This would store in an advisory_logs table
    # For now, just a placeholder
    pass