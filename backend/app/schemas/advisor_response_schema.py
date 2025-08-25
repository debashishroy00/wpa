"""
Advisor Response JSON Schema
Enforces strict structure for LLM responses - no free-form essays
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum


class HealthBand(str, Enum):
    """Health status bands from Step-4"""
    STABILIZE_FIRST = "stabilize_first"
    ON_TRACK = "on_track"
    OPTIMIZING = "optimizing"
    EXCELLING = "excelling"


class ActionType(str, Enum):
    """Types of recommended actions"""
    IMMEDIATE = "immediate"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    TOOL_TRIGGER = "tool_trigger"


class RecommendedAction(BaseModel):
    """Single recommended action with validation"""
    action_type: ActionType
    title: str = Field(..., max_length=100)
    description: str = Field(..., max_length=300)
    timeline: str = Field(..., max_length=50)
    priority: int = Field(..., ge=1, le=5)
    kb_citation: Optional[str] = Field(None, pattern=r'^KB-\d+$')
    tool_trigger: Optional[str] = Field(None, pattern=r'^\[computed → run [A-Za-z\-\s]+\]$')
    
    @validator('description')
    def no_new_math_in_description(cls, v):
        """Ensure no calculation keywords in descriptions"""
        calc_keywords = ['calculate', 'multiply', 'divide', '4% rule', 'assuming']
        for keyword in calc_keywords:
            if keyword.lower() in v.lower():
                raise ValueError(f"Calculation keyword '{keyword}' not allowed")
        return v


class QuarterlyMilestone(BaseModel):
    """Quarterly milestone with specific targets"""
    quarter: str = Field(..., pattern=r'^Q[1-4] \d{4}$')
    milestone: str = Field(..., max_length=200)
    target_metric: Optional[str] = Field(None, max_length=100)
    kb_citation: Optional[str] = Field(None, pattern=r'^KB-\d+$')


class AdvisorResponseJSON(BaseModel):
    """
    Strict JSON schema for LLM advisor responses
    Prevents free-form essays and enforces structure
    """
    
    # Executive Summary (required)
    health_band: HealthBand
    health_score: Optional[int] = Field(None, ge=0, le=100)
    executive_summary: str = Field(..., min_length=100, max_length=500)
    key_insight: str = Field(..., max_length=200)
    
    # Current Status (Step-4 values only)
    current_position: Dict[str, Any] = Field(..., description="Step-4 computed values only")
    
    # Immediate Actions (required, 5-7 actions)
    immediate_actions: List[RecommendedAction] = Field(..., min_items=5, max_items=7)
    
    # 12-Month Strategy (required)
    quarterly_milestones: List[QuarterlyMilestone] = Field(..., min_items=4, max_items=4)
    
    # Risk Management
    primary_risks: List[str] = Field(..., max_items=3)
    mitigation_strategies: List[str] = Field(..., max_items=3)
    
    # Citations (KB-only)
    knowledge_base_citations: List[str] = Field(default_factory=list)
    
    # Guardrails (from Step-4)
    guardrails_applied: List[str] = Field(default_factory=list)
    
    # Metadata
    response_timestamp: str
    step4_timestamp: Optional[str] = None
    
    @validator('knowledge_base_citations')
    def validate_kb_citations(cls, v):
        """Ensure all citations are KB-format"""
        for citation in v:
            if not citation.startswith('KB-'):
                raise ValueError(f"Invalid citation format: {citation}. Must be KB-XXX")
        return v
    
    @validator('executive_summary', 'key_insight')
    def no_calculations_in_text(cls, v):
        """Prevent calculation language in narrative text"""
        forbidden_phrases = [
            'calculate', 'multiply by', 'divide by', '4% rule', 
            'assuming', 'estimated', 'projected', 'computed'
        ]
        v_lower = v.lower()
        for phrase in forbidden_phrases:
            if phrase in v_lower:
                raise ValueError(f"Calculation phrase '{phrase}' not allowed in narrative")
        return v
    
    @validator('current_position')
    def validate_step4_only(cls, v):
        """Ensure current_position contains only Step-4 values"""
        # This would be enhanced to check against actual Step-4 data
        required_fields = ['net_worth', 'monthly_surplus', 'health_score']
        for field in required_fields:
            if field not in v:
                raise ValueError(f"Required Step-4 field missing: {field}")
        return v
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"  # Prevent additional fields


class AdvisorResponseValidator:
    """Validates LLM responses against schema and Step-4 data"""
    
    def __init__(self):
        self.schema = AdvisorResponseJSON
    
    def validate_response(self, response_json: Dict, step4_data: Dict) -> Dict[str, Any]:
        """
        Validate LLM response against schema and Step-4 data
        
        Args:
            response_json: LLM response as JSON
            step4_data: Step-4 computed values for validation
            
        Returns:
            Validation result with errors if any
        """
        try:
            # Schema validation
            validated_response = self.schema(**response_json)
            
            # Step-4 data validation
            step4_violations = self._validate_against_step4(response_json, step4_data)
            
            # Number validation
            number_violations = self._validate_no_new_numbers(response_json, step4_data)
            
            return {
                "is_valid": len(step4_violations) == 0 and len(number_violations) == 0,
                "validated_response": validated_response,
                "step4_violations": step4_violations,
                "number_violations": number_violations
            }
            
        except Exception as e:
            return {
                "is_valid": False,
                "schema_error": str(e),
                "validated_response": None
            }
    
    def _validate_against_step4(self, response_json: Dict, step4_data: Dict) -> List[str]:
        """Validate that response uses only Step-4 computed values"""
        violations = []
        
        # Check current_position against Step-4
        current_pos = response_json.get('current_position', {})
        step4_financial = step4_data.get('financial_position', {})
        
        for key, value in current_pos.items():
            if key in step4_financial:
                step4_value = step4_financial[key]
                if isinstance(value, (int, float)) and abs(value - step4_value) > 0.01:
                    violations.append(f"Value mismatch for {key}: response={value}, step4={step4_value}")
            else:
                violations.append(f"Value {key} not found in Step-4 data")
        
        return violations
    
    def _validate_no_new_numbers(self, response_json: Dict, step4_data: Dict) -> List[str]:
        """Validate that no new numbers were calculated"""
        import re
        
        violations = []
        
        # Convert response to string for number extraction
        response_str = str(response_json)
        
        # Extract all numbers
        dollar_pattern = r'\$[\d,]+(?:\.\d{2})?'
        percent_pattern = r'\b\d+(?:\.\d+)?%'
        
        response_dollars = re.findall(dollar_pattern, response_str)
        response_percentages = re.findall(percent_pattern, response_str)
        
        # Get valid Step-4 numbers
        valid_numbers = self._extract_step4_numbers(step4_data)
        
        # Check violations
        for dollar in response_dollars:
            if dollar not in valid_numbers['dollars']:
                violations.append(f"Unauthorized dollar amount: {dollar}")
        
        for percent in response_percentages:
            if percent not in valid_numbers['percentages']:
                violations.append(f"Unauthorized percentage: {percent}")
        
        return violations
    
    def _extract_step4_numbers(self, step4_data: Dict) -> Dict[str, set]:
        """Extract all valid numbers from Step-4 data"""
        valid_dollars = set()
        valid_percentages = set()
        
        def extract_recursive(data):
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        if 'percentage' in key or 'rate' in key or key.endswith('_pct'):
                            valid_percentages.add(f"{value:.1f}%")
                        elif 'amount' in key or 'worth' in key or 'surplus' in key:
                            valid_dollars.add(f"${value:,.0f}")
                    elif isinstance(value, (dict, list)):
                        extract_recursive(value)
            elif isinstance(data, list):
                for item in data:
                    extract_recursive(item)
        
        extract_recursive(step4_data)
        
        return {
            'dollars': valid_dollars,
            'percentages': valid_percentages
        }


# Global validator instance
advisor_response_validator = AdvisorResponseValidator()