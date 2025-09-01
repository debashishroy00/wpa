"""
Financial Health Scorer Service
Provides comprehensive numerical scores and grades for financial health assessment
"""

from typing import Dict, List, Any, Tuple
from sqlalchemy.orm import Session
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


class FinancialHealthScorer:
    """Calculate comprehensive financial health score with detailed breakdown"""
    
    def __init__(self):
        # Age-based net worth benchmarks (50th, 75th, 90th, 95th percentiles)
        self.net_worth_benchmarks = {
            50: {'p50': 200000, 'p75': 500000, 'p90': 1200000, 'p95': 2000000},
            54: {'p50': 285000, 'p75': 650000, 'p90': 1400000, 'p95': 2100000},
            55: {'p50': 300000, 'p75': 700000, 'p90': 1500000, 'p95': 2300000},
            60: {'p50': 400000, 'p75': 900000, 'p90': 2000000, 'p95': 3500000}
        }
        
        # Scoring weights for different components
        self.score_weights = {
            'net_worth': 0.20,      # 20% - wealth accumulation
            'savings_rate': 0.20,   # 20% - saving behavior
            'debt_management': 0.15, # 15% - debt control
            'retirement_readiness': 0.25, # 25% - retirement preparation
            'liquidity': 0.10,      # 10% - emergency preparedness
            'diversification': 0.10  # 10% - risk management
        }
    
    def calculate_comprehensive_score(self, user_id: int, db: Session) -> Dict[str, Any]:
        """
        Calculate complete financial health score with detailed breakdown
        
        Returns actual numerical scores, not just descriptions
        """
        try:
            # Get complete financial data
            financial_data = self._get_complete_financial_data(user_id, db)
            
            if 'error' in financial_data:
                return {'error': financial_data['error']}
            
            # Calculate individual component scores
            component_scores = {
                'net_worth': self._score_net_worth(financial_data['net_worth'], financial_data['age']),
                'savings_rate': self._score_savings_rate(financial_data['savings_rate']),
                'debt_management': self._score_debt_management(financial_data['debt_to_income']),
                'retirement_readiness': self._score_retirement_readiness(financial_data['retirement_progress'], financial_data['age']),
                'liquidity': self._score_liquidity(financial_data['emergency_fund_months']),
                'diversification': self._score_diversification(financial_data['asset_allocation'])
            }
            
            # Calculate weighted overall score
            overall_score = sum(
                component_scores[component] * self.score_weights[component] 
                for component in component_scores
            )
            
            # Generate grade and percentile
            grade = self._calculate_grade(overall_score)
            percentile = self._calculate_percentile(financial_data['net_worth'], financial_data['age'])
            
            # Identify strengths and improvement areas
            strengths = self._identify_strengths(component_scores, financial_data)
            improvements = self._identify_improvements(component_scores, financial_data)
            
            return {
                'overall_score': round(overall_score, 1),
                'grade': grade,
                'percentile': percentile,
                'component_scores': {
                    'net_worth': {
                        'score': round(component_scores['net_worth'], 1),
                        'max_points': 20,
                        'points_earned': round(component_scores['net_worth'] * 0.20, 1),
                        'description': f"${financial_data['net_worth']:,.0f} net worth (age {financial_data['age']})"
                    },
                    'savings_rate': {
                        'score': round(component_scores['savings_rate'], 1),
                        'max_points': 20,
                        'points_earned': round(component_scores['savings_rate'] * 0.20, 1),
                        'description': f"{financial_data['savings_rate']:.1f}% savings rate"
                    },
                    'debt_management': {
                        'score': round(component_scores['debt_management'], 1),
                        'max_points': 15,
                        'points_earned': round(component_scores['debt_management'] * 0.15, 1),
                        'description': f"{financial_data['debt_to_income']:.1f}% debt-to-income ratio"
                    },
                    'retirement_readiness': {
                        'score': round(component_scores['retirement_readiness'], 1),
                        'max_points': 25,
                        'points_earned': round(component_scores['retirement_readiness'] * 0.25, 1),
                        'description': f"{financial_data['retirement_progress']:.1f}% retirement funded"
                    },
                    'liquidity': {
                        'score': round(component_scores['liquidity'], 1),
                        'max_points': 10,
                        'points_earned': round(component_scores['liquidity'] * 0.10, 1),
                        'description': f"{financial_data['emergency_fund_months']:.1f} months emergency fund"
                    },
                    'diversification': {
                        'score': round(component_scores['diversification'], 1),
                        'max_points': 10,
                        'points_earned': round(component_scores['diversification'] * 0.10, 1),
                        'description': "Asset allocation analysis"
                    }
                },
                'strengths': strengths,
                'improvements': improvements,
                'financial_summary': {
                    'net_worth': financial_data['net_worth'],
                    'total_assets': financial_data['total_assets'],
                    'monthly_surplus': financial_data['monthly_surplus'],
                    'retirement_goal': financial_data['retirement_goal'],
                    'years_to_goal': financial_data['years_to_goal']
                },
                'peer_comparison': {
                    'net_worth_percentile': percentile,
                    'savings_rate_percentile': self._get_savings_rate_percentile(financial_data['savings_rate']),
                    'age_group': financial_data['age'],
                    'status': 'exceptional' if percentile >= 95 else 'above_average' if percentile >= 75 else 'average'
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating financial health score for user {user_id}: {str(e)}")
            return {'error': f"Failed to calculate score: {str(e)}"}
    
    def _get_complete_financial_data(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get complete financial data for scoring"""
        try:
            from .financial_summary_service import financial_summary_service
            from ..models.user_profile import UserProfile
            from ..models.goals_v2 import Goal
            
            # Get financial summary
            summary = financial_summary_service.get_user_financial_summary(user_id, db)
            
            if 'error' in summary:
                return {'error': summary['error']}
            
            # Get user profile for age
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            age = profile.age if profile and profile.age else 54
            
            # Get retirement goal
            retirement_goals = db.query(Goal).filter(
                Goal.user_id == user_id,
                Goal.name.ilike('%retirement%')
            ).all()
            
            retirement_goal = 3500000  # Default $3.5M target
            if retirement_goals:
                retirement_goal = max(float(goal.target_amount) for goal in retirement_goals)
            
            # Calculate retirement progress by subtracting personal property from total assets
            personal_property_total = 0
            if 'assetsBreakdown' in summary and 'personal_property' in summary['assetsBreakdown']:
                for item in summary['assetsBreakdown']['personal_property']:
                    if isinstance(item, dict):
                        personal_property_total += item.get('value', 0)
            
            retirement_capable_assets = summary.get('totalAssets', 0) - personal_property_total
            retirement_progress = (retirement_capable_assets / retirement_goal * 100) if retirement_goal > 0 else 0
            
            # Calculate emergency fund months
            monthly_expenses = summary.get('monthlyExpenses', 0)
            liquid_assets = 0
            if 'assetsBreakdown' in summary and 'cash_bank_accounts' in summary['assetsBreakdown']:
                for account in summary['assetsBreakdown']['cash_bank_accounts']:
                    if isinstance(account, dict):
                        liquid_assets += account.get('value', 0)
            
            emergency_fund_months = (liquid_assets / monthly_expenses) if monthly_expenses > 0 else 0
            
            # Calculate asset allocation
            total_investable = retirement_capable_assets
            real_estate_value = 0
            if 'assetsBreakdown' in summary and 'real_estate' in summary['assetsBreakdown']:
                for property in summary['assetsBreakdown']['real_estate']:
                    if isinstance(property, dict):
                        real_estate_value += property.get('value', 0)
            
            asset_allocation = {
                'real_estate_pct': (real_estate_value / total_investable * 100) if total_investable > 0 else 0,
                'liquid_pct': (liquid_assets / total_investable * 100) if total_investable > 0 else 0
            }
            
            # Calculate years to goal
            monthly_surplus = summary.get('monthlySurplus', 0)
            current_progress = retirement_capable_assets
            remaining_needed = max(0, retirement_goal - current_progress)
            years_to_goal = (remaining_needed / (monthly_surplus * 12)) if monthly_surplus > 0 else 999
            
            return {
                'net_worth': summary.get('netWorth', 0),
                'total_assets': summary.get('totalAssets', 0),
                'monthly_surplus': monthly_surplus,
                'savings_rate': summary.get('savingsRate', 0),
                'debt_to_income': summary.get('debtToIncomeRatio', 0),
                'retirement_progress': retirement_progress,
                'retirement_goal': retirement_goal,
                'emergency_fund_months': emergency_fund_months,
                'asset_allocation': asset_allocation,
                'age': age,
                'years_to_goal': years_to_goal
            }
            
        except Exception as e:
            logger.error(f"Error getting financial data for scoring: {str(e)}")
            return {'error': f"Failed to retrieve financial data: {str(e)}"}
    
    def _score_net_worth(self, net_worth: float, age: int) -> float:
        """Score net worth based on age-appropriate benchmarks"""
        benchmarks = self.net_worth_benchmarks.get(age, self.net_worth_benchmarks[50])
        
        if net_worth >= benchmarks['p95']:
            return 100.0
        elif net_worth >= benchmarks['p90']:
            return 90.0 + (net_worth - benchmarks['p90']) / (benchmarks['p95'] - benchmarks['p90']) * 10
        elif net_worth >= benchmarks['p75']:
            return 80.0 + (net_worth - benchmarks['p75']) / (benchmarks['p90'] - benchmarks['p75']) * 10
        elif net_worth >= benchmarks['p50']:
            return 60.0 + (net_worth - benchmarks['p50']) / (benchmarks['p75'] - benchmarks['p50']) * 20
        else:
            return max(0, 60.0 * (net_worth / benchmarks['p50']))
    
    def _score_savings_rate(self, savings_rate: float) -> float:
        """Score savings rate"""
        if savings_rate >= 50:
            return 100.0
        elif savings_rate >= 30:
            return 90.0 + (savings_rate - 30) / 20 * 10
        elif savings_rate >= 20:
            return 80.0 + (savings_rate - 20) / 10 * 10
        elif savings_rate >= 15:
            return 70.0 + (savings_rate - 15) / 5 * 10
        elif savings_rate >= 10:
            return 60.0 + (savings_rate - 10) / 5 * 10
        else:
            return max(0, 60.0 * (savings_rate / 10))
    
    def _score_debt_management(self, debt_to_income: float) -> float:
        """Score debt management (lower is better)"""
        if debt_to_income <= 10:
            return 100.0
        elif debt_to_income <= 20:
            return 90.0 - (debt_to_income - 10) / 10 * 10
        elif debt_to_income <= 36:
            return 80.0 - (debt_to_income - 20) / 16 * 20
        elif debt_to_income <= 50:
            return 60.0 - (debt_to_income - 36) / 14 * 30
        else:
            return max(0, 30.0 - (debt_to_income - 50) / 10 * 30)
    
    def _score_retirement_readiness(self, retirement_progress: float, age: int) -> float:
        """Score retirement readiness"""
        # Expected progress targets by age
        expected_targets = {
            25: 5, 30: 15, 35: 30, 40: 50, 45: 70, 50: 85, 54: 95, 55: 100, 60: 110, 65: 120
        }
        
        expected = expected_targets.get(age, 95)  # Default to 95% for age 54
        
        if retirement_progress >= expected:
            return 100.0
        else:
            return max(0, (retirement_progress / expected) * 100)
    
    def _score_liquidity(self, emergency_fund_months: float) -> float:
        """Score emergency fund adequacy"""
        if emergency_fund_months >= 12:
            return 100.0
        elif emergency_fund_months >= 6:
            return 90.0 + (emergency_fund_months - 6) / 6 * 10
        elif emergency_fund_months >= 3:
            return 70.0 + (emergency_fund_months - 3) / 3 * 20
        elif emergency_fund_months >= 1:
            return 40.0 + (emergency_fund_months - 1) / 2 * 30
        else:
            return max(0, 40.0 * emergency_fund_months)
    
    def _score_diversification(self, asset_allocation: Dict) -> float:
        """Score asset diversification"""
        real_estate_pct = asset_allocation.get('real_estate_pct', 0)
        liquid_pct = asset_allocation.get('liquid_pct', 0)
        
        score = 100.0
        
        # Penalize excessive real estate concentration
        if real_estate_pct > 50:
            score -= (real_estate_pct - 50) * 0.5
        elif real_estate_pct > 40:
            score -= (real_estate_pct - 40) * 0.3
        
        # Penalize excessive cash
        if liquid_pct > 20:
            score -= (liquid_pct - 20) * 0.8
        elif liquid_pct > 10:
            score -= (liquid_pct - 10) * 0.5
        
        return max(60, score)  # Minimum score of 60
    
    def _calculate_grade(self, score: float) -> str:
        """Convert numerical score to letter grade"""
        if score >= 97:
            return 'A+'
        elif score >= 93:
            return 'A'
        elif score >= 90:
            return 'A-'
        elif score >= 87:
            return 'B+'
        elif score >= 83:
            return 'B'
        elif score >= 80:
            return 'B-'
        elif score >= 77:
            return 'C+'
        elif score >= 73:
            return 'C'
        elif score >= 70:
            return 'C-'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _calculate_percentile(self, net_worth: float, age: int) -> int:
        """Calculate net worth percentile for age group"""
        benchmarks = self.net_worth_benchmarks.get(age, self.net_worth_benchmarks[50])
        
        if net_worth >= benchmarks['p95']:
            return 95
        elif net_worth >= benchmarks['p90']:
            return 90
        elif net_worth >= benchmarks['p75']:
            return 75
        elif net_worth >= benchmarks['p50']:
            return 50
        else:
            return 25
    
    def _get_savings_rate_percentile(self, savings_rate: float) -> int:
        """Calculate savings rate percentile"""
        if savings_rate >= 50:
            return 99
        elif savings_rate >= 30:
            return 95
        elif savings_rate >= 20:
            return 90
        elif savings_rate >= 15:
            return 75
        elif savings_rate >= 10:
            return 60
        else:
            return 40
    
    def _identify_strengths(self, scores: Dict, financial_data: Dict) -> List[str]:
        """Identify key financial strengths"""
        strengths = []
        
        if scores['net_worth'] >= 90:
            percentile = self._calculate_percentile(financial_data['net_worth'], financial_data['age'])
            strengths.append(f"Exceptional wealth accumulation - {percentile}th percentile for age {financial_data['age']}")
        
        if scores['savings_rate'] >= 90:
            pct = self._get_savings_rate_percentile(financial_data['savings_rate'])
            strengths.append(f"Outstanding savings discipline - {financial_data['savings_rate']:.1f}% rate ({pct}th percentile)")
        
        if scores['debt_management'] >= 90:
            strengths.append(f"Excellent debt management - {financial_data['debt_to_income']:.1f}% DTI ratio")
        
        if scores['retirement_readiness'] >= 90:
            strengths.append(f"Retirement ready - {financial_data['retirement_progress']:.1f}% funded")
        
        if financial_data['years_to_goal'] <= 5:
            strengths.append(f"On track to reach ${financial_data['retirement_goal']:,.0f} goal in {financial_data['years_to_goal']:.1f} years")
        
        return strengths
    
    def _identify_improvements(self, scores: Dict, financial_data: Dict) -> List[str]:
        """Identify areas for improvement"""
        improvements = []
        
        if scores['diversification'] < 80:
            real_estate_pct = financial_data['asset_allocation'].get('real_estate_pct', 0)
            if real_estate_pct > 40:
                improvements.append(f"Consider reducing real estate concentration ({real_estate_pct:.1f}% of portfolio)")
        
        if scores['liquidity'] < 70:
            improvements.append(f"Build emergency fund to 6+ months (currently {financial_data['emergency_fund_months']:.1f} months)")
        
        if scores['debt_management'] < 80:
            improvements.append(f"Focus on debt reduction - DTI ratio of {financial_data['debt_to_income']:.1f}% is above optimal")
        
        if financial_data['savings_rate'] < 20:
            improvements.append("Increase savings rate to 20%+ for accelerated wealth building")
        
        return improvements


# Global instance
financial_health_scorer = FinancialHealthScorer()