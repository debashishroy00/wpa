"""
IdentityMath: Minimal financial facts and mathematical identities.
No calculations, no projections, no business logic.
"""

from typing import Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

def _num(value) -> float:
    """Safe numeric conversion"""
    try:
        return float(value or 0)
    except:
        return 0.0

def _int(value) -> int:
    """Safe integer conversion"""
    try:
        return int(float(value or 0))
    except:
        return 0

def _str(value) -> str:
    """Safe string conversion"""
    return str(value) if value else ""

class IdentityMath:
    """Extract mathematical facts from raw data"""
    
    SCHEMA_VERSION = "identitymath.min.v1"
    
    def compute_claims(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Returns raw facts and mathematical identities only"""
        try:
            # Get raw data
            from app.services.financial_summary_service import financial_summary_service
            data = financial_summary_service.get_user_financial_summary(user_id, db)
            
            if not data:
                return {"error": "No data", "_warnings": ["no_data"]}
            
            # Timestamps
            now_iso = datetime.now(timezone.utc).isoformat()
            as_of = data.get("asOf") or now_iso
            
            # Build facts - no calculations beyond identities
            facts = {
                "schema_version": self.SCHEMA_VERSION,
                "as_of": as_of,
                
                # Raw facts from database
                "total_assets": _num(data.get("totalAssets")),
                "total_liabilities": _num(data.get("totalLiabilities")),
                "monthly_income": _num(data.get("monthlyIncome")),
                "monthly_expenses": _num(data.get("monthlyExpenses")),
                "monthly_debt_payments": _num(data.get("monthlyDebtPayments")),  # May overlap with expenses
                "liquid_assets": _num(data.get("liquidAssets")),
                "investment_total": _num(data.get("investmentTotal")),
                "retirement_total": _num(data.get("retirementTotal")),
                "annual_401k": _num(data.get("annual401k")),
                
                # Mathematical identities (computed here for validation)
                "net_worth": 0.0,  # Will be calculated below
                "monthly_surplus": 0.0,  # Will be calculated below
                
                # Derived financial metrics for LLM context
                "savings_rate": 0.0,  # monthly_surplus / monthly_income
                "debt_to_asset_ratio": 0.0,  # total_liabilities / total_assets
                "liquid_months": 0.0,  # liquid_assets / monthly_expenses
                "fi_number": 0.0,  # monthly_expenses * 12 * 25 (4% rule)
                "fi_progress": 0.0,  # net_worth / fi_number
                "years_to_fi": 0.0,  # calculation based on savings rate
                "investment_allocation": 0.0,  # investment_total / total_assets
                
                # Context for LLM reasoning
                "_context": {
                    "age": _int(data.get("age")),
                    "state": _str(data.get("state")),
                    "filing_status": _str(data.get("filingStatus")),
                    "dependents": _int(data.get("dependents")),
                    "marital_status": _str(data.get("maritalStatus")),
                    "risk_tolerance": _str(data.get("riskTolerance"))
                },
                
                # Evidence trail
                "_evidence": [
                    "source:database",
                    f"timestamp:{as_of}",
                    "calc:net_worth=total_assets-total_liabilities",
                    "calc:monthly_surplus=monthly_income-monthly_expenses",
                    "calc:savings_rate=monthly_surplus/monthly_income",
                    "calc:debt_to_asset_ratio=total_liabilities/total_assets", 
                    "calc:liquid_months=liquid_assets/monthly_expenses",
                    "calc:fi_number=monthly_expenses*12*25",
                    "calc:fi_progress=net_worth/fi_number",
                    "calc:years_to_fi=complex_calculation",
                    "calc:investment_allocation=investment_total/total_assets"
                ],
                
                # Evidence mapping for Trust Engine
                "_evidence_map": {
                    "total_assets": "db:financial_summary.totalAssets",
                    "total_liabilities": "db:financial_summary.totalLiabilities",
                    "monthly_income": "db:financial_summary.monthlyIncome",
                    "monthly_expenses": "db:financial_summary.monthlyExpenses",
                    "net_worth": "calc:total_assets-total_liabilities",
                    "monthly_surplus": "calc:monthly_income-monthly_expenses",
                    "savings_rate": "calc:monthly_surplus/monthly_income",
                    "debt_to_asset_ratio": "calc:total_liabilities/total_assets",
                    "liquid_months": "calc:liquid_assets/monthly_expenses",
                    "fi_number": "calc:monthly_expenses*12*25",
                    "fi_progress": "calc:net_worth/fi_number",
                    "years_to_fi": "calc:complex_fi_calculation",
                    "investment_allocation": "calc:investment_total/total_assets"
                },
                
                "_warnings": [],
                "_missing": []
            }
            
            # Calculate identities
            facts["net_worth"] = facts["total_assets"] - facts["total_liabilities"]
            facts["monthly_surplus"] = facts["monthly_income"] - facts["monthly_expenses"]
            
            # Calculate derived financial metrics
            facts["savings_rate"] = (facts["monthly_surplus"] / facts["monthly_income"]) if facts["monthly_income"] > 0 else 0.0
            facts["debt_to_asset_ratio"] = (facts["total_liabilities"] / facts["total_assets"]) if facts["total_assets"] > 0 else 0.0
            facts["liquid_months"] = (facts["liquid_assets"] / facts["monthly_expenses"]) if facts["monthly_expenses"] > 0 else 0.0
            facts["fi_number"] = facts["monthly_expenses"] * 12 * 25  # 4% rule
            facts["fi_progress"] = (facts["net_worth"] / facts["fi_number"]) if facts["fi_number"] > 0 else 0.0
            facts["investment_allocation"] = (facts["investment_total"] / facts["total_assets"]) if facts["total_assets"] > 0 else 0.0
            
            # Calculate years to FI (simplified - assumes current savings rate continues)
            if facts["savings_rate"] > 0 and facts["fi_number"] > 0:
                annual_savings = facts["monthly_surplus"] * 12
                if annual_savings > 0:
                    # Simplified calculation: (FI_target - current_net_worth) / annual_savings
                    remaining_to_fi = max(0, facts["fi_number"] - facts["net_worth"])
                    facts["years_to_fi"] = remaining_to_fi / annual_savings
                else:
                    facts["years_to_fi"] = float('inf')
            else:
                facts["years_to_fi"] = float('inf')
            
            # Validate
            self._validate(facts, data)
            
            return facts
            
        except Exception as e:
            logger.error(f"Error computing claims for user {user_id}: {e}")
            return {"error": str(e), "_warnings": ["computation_error"]}
    
    def _validate(self, facts: Dict, raw_data: Dict) -> None:
        """Validate identities and flag issues"""
        # Check mathematical identities
        calc_net_worth = facts["total_assets"] - facts["total_liabilities"]
        if abs(facts["net_worth"] - calc_net_worth) > 0.01:
            facts["_warnings"].append("net_worth_identity_violation")
            
        calc_surplus = facts["monthly_income"] - facts["monthly_expenses"]
        if abs(facts["monthly_surplus"] - calc_surplus) > 0.01:
            facts["_warnings"].append("surplus_identity_violation")
        
        # Flag data issues
        if facts["monthly_surplus"] < 0:
            facts["_warnings"].append("negative_surplus")
        
        if "asOf" not in raw_data:
            facts["_warnings"].append("missing_as_of_date")
            
        # Track missing context and add warnings for critical missing data
        if not facts["_context"]["age"]:
            facts["_missing"].append("age")
            facts["_warnings"].append("age_missing_retirement_calculations_may_be_inaccurate")
        if not facts["_context"]["state"]:
            facts["_missing"].append("state")
            facts["_warnings"].append("state_missing_tax_calculations_unavailable")
        if not facts["_context"]["filing_status"]:
            facts["_missing"].append("filing_status")
            facts["_warnings"].append("filing_status_missing_tax_optimization_unavailable")

# No singleton - create instances as needed