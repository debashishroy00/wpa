"""
Enhanced Intent Classification System for Chat Memory
Supports multi-intent detection and priority-based selection
"""
import re
from typing import List, Dict, Tuple, Optional
from enum import Enum
import structlog

logger = structlog.get_logger()


class IntentPriority(Enum):
    """Priority levels for different intents"""
    URGENT = 1      # Debt, emergency issues
    HIGH = 2        # Retirement, goals
    MEDIUM = 3      # Allocation, optimization
    LOW = 4         # General questions


class EnhancedIntentClassifier:
    """Advanced intent classification with multi-intent support"""
    
    def __init__(self):
        self.intent_patterns = {
            'retirement': {
                'patterns': [
                    r'(retire|retirement|fire|future|goal|65|67|age)',
                    r'(401k|403b|ira|roth|pension)',
                    r'(withdraw|distribution|swr|safe\s+withdrawal)',
                    r'(nest\s+egg|retirement\s+fund|golden\s+years)'
                ],
                'priority': IntentPriority.HIGH,
                'keywords': ['retire', 'retirement', 'future', 'goal', '401k', 'pension']
            },
            'allocation': {
                'patterns': [
                    r'(allocation|diversif|portfolio|balance|mix|spread)',
                    r'(asset\s+class|stocks?|bonds?|real\s+estate)',
                    r'(rebalance|redistribute|adjust\s+mix)',
                    r'(concentrated|heavy|too\s+much|overweight)'
                ],
                'priority': IntentPriority.MEDIUM,
                'keywords': ['allocation', 'portfolio', 'balance', 'diversify', 'rebalance']
            },
            'returns': {
                'patterns': [
                    r'(return|growth|performance|yield|profit|gain)',
                    r'(roi|return\s+on\s+investment|appreciation)',
                    r'(expect|projection|forecast|trend)',
                    r'(beating\s+market|outperform|underperform)'
                ],
                'priority': IntentPriority.MEDIUM,
                'keywords': ['return', 'growth', 'performance', 'yield', 'roi']
            },
            'debt': {
                'patterns': [
                    r'(debt|loan|credit|owe|payment|liability)',
                    r'(mortgage|student\s+loan|car\s+loan|personal\s+loan)',
                    r'(payoff|pay\s+off|eliminate|reduce\s+debt)',
                    r'(interest\s+rate|apr|refinance|consolidate)'
                ],
                'priority': IntentPriority.URGENT,
                'keywords': ['debt', 'loan', 'credit', 'mortgage', 'payoff']
            },
            'tax': {
                'patterns': [
                    r'(tax|deduction|irs|withholding|bracket)',
                    r'(roth\s+conversion|backdoor\s+roth|tax\s+loss)',
                    r'(hsa|529|tax\s+advantage|pre\s+tax|after\s+tax)',
                    r'(capital\s+gain|dividend|qualified|ordinary\s+income)'
                ],
                'priority': IntentPriority.MEDIUM,
                'keywords': ['tax', 'deduction', 'roth', 'hsa', '529', 'bracket']
            },
            'real_estate': {
                'patterns': [
                    r'(property|real\s+estate|rental|house|home)',
                    r'(reit|real\s+estate\s+investment)',
                    r'(mortgage|refinance|home\s+equity|property\s+tax)',
                    r'(landlord|tenant|rental\s+income|vacancy)'
                ],
                'priority': IntentPriority.MEDIUM,
                'keywords': ['property', 'real estate', 'rental', 'house', 'reit']
            },
            'emergency': {
                'patterns': [
                    r'(emergency|liquid|cash|reserve|rainy\s+day)',
                    r'(accessible|available|short\s+term|savings)',
                    r'(6\s+months?|emergency\s+fund|liquid\s+assets)',
                    r'(unexpected|crisis|job\s+loss|medical)'
                ],
                'priority': IntentPriority.HIGH,
                'keywords': ['emergency', 'liquid', 'cash', 'reserve', 'accessible']
            },
            'risk': {
                'patterns': [
                    r'(risk|volatil|safe|conservative|aggressive)',
                    r'(risk\s+tolerance|comfort\s+level|sleep\s+at\s+night)',
                    r'(market\s+crash|downturn|recession|bear\s+market)',
                    r'(hedge|protection|insurance|diversification)'
                ],
                'priority': IntentPriority.MEDIUM,
                'keywords': ['risk', 'volatility', 'safe', 'conservative', 'hedge']
            },
            'optimization': {
                'patterns': [
                    r'(optim|improve|better|enhance|maximize)',
                    r'(efficiency|effective|smart|strategic)',
                    r'(best\s+practice|recommendation|advice|suggest)',
                    r'(what\s+should|how\s+can|way\s+to\s+improve)'
                ],
                'priority': IntentPriority.MEDIUM,
                'keywords': ['optimize', 'improve', 'better', 'maximize', 'efficient']
            },
            'cash_flow': {
                'patterns': [
                    r'(cash\s+flow|monthly|budget|income|expense)',
                    r'(spend|spending|cost|living\s+expense)',
                    r'(surplus|deficit|break\s+even|tight)',
                    r'(save\s+more|cut\s+cost|reduce\s+spend)'
                ],
                'priority': IntentPriority.MEDIUM,
                'keywords': ['cash flow', 'budget', 'monthly', 'expense', 'spending']
            },
            'general': {
                'patterns': [
                    r'(help|question|advice|opinion|thought)',
                    r'(what\s+do\s+you\s+think|how\s+does|tell\s+me)',
                    r'(explain|understand|clarify|confused)',
                    r'(overall|general|broad|big\s+picture)'
                ],
                'priority': IntentPriority.LOW,
                'keywords': ['help', 'question', 'advice', 'explain', 'general']
            }
        }
    
    def classify_intents(self, message: str) -> List[str]:
        """Detect multiple intents in a single message"""
        if not message:
            return ['general']
        
        message_lower = message.lower().strip()
        detected_intents = []
        
        # Check each intent pattern
        for intent_name, intent_config in self.intent_patterns.items():
            if self._matches_intent(message_lower, intent_config):
                detected_intents.append(intent_name)
        
        # If no specific intents detected, default to general
        if not detected_intents:
            detected_intents = ['general']
        
        logger.info(f"Detected intents: {detected_intents} for message: '{message[:50]}...'")
        return detected_intents
    
    def _matches_intent(self, message: str, intent_config: Dict) -> bool:
        """Check if message matches intent patterns"""
        patterns = intent_config.get('patterns', [])
        keywords = intent_config.get('keywords', [])
        
        # Check regex patterns
        pattern_matches = 0
        for pattern in patterns:
            if re.search(pattern, message, re.IGNORECASE):
                pattern_matches += 1
        
        # Check keyword presence
        keyword_matches = 0
        for keyword in keywords:
            if keyword.lower() in message:
                keyword_matches += 1
        
        # Intent matches if at least one pattern OR multiple keywords match
        return pattern_matches > 0 or keyword_matches >= 2
    
    def get_primary_intent(self, intents: List[str]) -> str:
        """Determine primary intent from multiple detected intents"""
        if not intents:
            return 'general'
        
        if len(intents) == 1:
            return intents[0]
        
        # Sort by priority (urgent first)
        priority_order = [
            ('debt', IntentPriority.URGENT),
            ('emergency', IntentPriority.URGENT),
            ('retirement', IntentPriority.HIGH),
            ('allocation', IntentPriority.MEDIUM),
            ('optimization', IntentPriority.MEDIUM),
            ('returns', IntentPriority.MEDIUM),
            ('tax', IntentPriority.MEDIUM),
            ('real_estate', IntentPriority.MEDIUM),
            ('cash_flow', IntentPriority.MEDIUM),
            ('risk', IntentPriority.MEDIUM),
            ('general', IntentPriority.LOW)
        ]
        
        # Find highest priority intent that was detected
        for intent_name, priority in priority_order:
            if intent_name in intents:
                logger.info(f"Primary intent selected: {intent_name} (priority: {priority.name})")
                return intent_name
        
        return 'general'
    
    def get_intent_context_weight(self, intent: str) -> float:
        """Get how much financial context weight this intent needs"""
        context_weights = {
            'retirement': 0.8,      # Needs comprehensive data
            'allocation': 0.9,      # Needs detailed portfolio info
            'returns': 0.7,         # Needs performance data
            'debt': 0.6,           # Needs liability info
            'tax': 0.7,            # Needs account details
            'real_estate': 0.8,    # Needs property details
            'emergency': 0.5,      # Needs liquid assets only
            'risk': 0.6,           # Needs portfolio overview
            'optimization': 0.9,   # Needs comprehensive analysis
            'cash_flow': 0.6,      # Needs income/expense data
            'general': 0.5         # Basic overview sufficient
        }
        
        return context_weights.get(intent, 0.5)
    
    def get_intent_response_style(self, intent: str, conversation_turn: int = 1) -> Dict[str, str]:
        """Get response style guidelines for specific intent"""
        base_styles = {
            'retirement': {
                'tone': 'encouraging and forward-looking',
                'focus': 'timeline, savings rate, goal achievement',
                'structure': 'current progress → gaps → actionable steps'
            },
            'allocation': {
                'tone': 'analytical and balanced',
                'focus': 'portfolio balance, diversification, risk',
                'structure': 'current allocation → risks → rebalancing strategy'
            },
            'returns': {
                'tone': 'realistic and data-driven',
                'focus': 'historical performance, realistic expectations',
                'structure': 'current returns → market context → improvement opportunities'
            },
            'debt': {
                'tone': 'urgent but supportive',
                'focus': 'interest costs, payoff strategies, timeline',
                'structure': 'debt analysis → prioritization → payoff plan'
            },
            'tax': {
                'tone': 'precise and strategic',
                'focus': 'tax efficiency, optimization opportunities',
                'structure': 'current tax situation → optimization strategies → implementation'
            },
            'real_estate': {
                'tone': 'balanced and strategic',
                'focus': 'concentration risk, property performance, alternatives',
                'structure': 'current exposure → risks/benefits → diversification options'
            },
            'emergency': {
                'tone': 'practical and reassuring',
                'focus': 'liquidity, accessibility, adequacy',
                'structure': 'current reserves → adequacy assessment → improvement plan'
            },
            'risk': {
                'tone': 'educational and calming',
                'focus': 'risk assessment, mitigation strategies',
                'structure': 'risk analysis → comfort level → appropriate adjustments'
            },
            'optimization': {
                'tone': 'strategic and actionable',
                'focus': 'improvement opportunities, priorities',
                'structure': 'current state → opportunities → prioritized action plan'
            },
            'cash_flow': {
                'tone': 'practical and solution-focused',
                'focus': 'income optimization, expense management',
                'structure': 'current flow → optimization opportunities → implementation'
            },
            'general': {
                'tone': 'helpful and comprehensive',
                'focus': 'overall financial health, broad guidance',
                'structure': 'situation overview → key insights → general recommendations'
            }
        }
        
        style = base_styles.get(intent, base_styles['general']).copy()
        
        # Adjust for conversation progression
        if conversation_turn > 3:
            style['tone'] = f"building on our discussion, {style['tone']}"
            style['structure'] = f"previous context → {style['structure']}"
        
        return style


# Global enhanced intent classifier instance
enhanced_intent_classifier = EnhancedIntentClassifier()