"""
WealthPath AI - Smart Context Selector
Keyword-based context selection for relevant document retrieval
"""
from typing import Dict, List, Set, Tuple, Optional
import re
import logging

logger = logging.getLogger(__name__)


class SmartContextSelector:
    """Smart context selection based on question keywords"""
    
    def __init__(self):
        # Define keyword mappings for different financial categories
        self.category_keywords = {
            "retirement": {
                "keywords": [
                    "retirement", "retire", "401k", "403b", "ira", "roth", "pension", 
                    "social security", "medicare", "elderly", "senior", "golden years",
                    "withdrawal", "rmd", "required minimum distribution", "nest egg",
                    "retirement savings", "retirement planning", "retirement age"
                ],
                "priority": 1
            },
            "tax": {
                "keywords": [
                    "tax", "taxes", "taxation", "deduction", "deductible", "irs", 
                    "tax return", "tax planning", "tax shelter", "tax advantaged",
                    "tax bracket", "tax liability", "refund", "withholding", "1099",
                    "w2", "capital gains", "tax loss harvesting", "tax strategy"
                ],
                "priority": 1
            },
            "investment": {
                "keywords": [
                    "investment", "invest", "portfolio", "stocks", "bonds", "mutual funds",
                    "etf", "asset allocation", "diversification", "risk", "return",
                    "market", "equity", "fixed income", "growth", "value", "dividend",
                    "rebalancing", "dollar cost averaging", "compound interest"
                ],
                "priority": 1
            },
            "cash": {
                "keywords": [
                    "cash", "savings", "emergency fund", "checking", "savings account",
                    "money market", "cd", "certificate of deposit", "high yield",
                    "liquidity", "cash flow", "bank", "banking", "interest rate"
                ],
                "priority": 2
            },
            "debt": {
                "keywords": [
                    "debt", "loan", "mortgage", "credit card", "student loan", 
                    "personal loan", "auto loan", "line of credit", "heloc",
                    "refinance", "consolidation", "payoff", "interest", "apr",
                    "minimum payment", "debt management", "debt consolidation"
                ],
                "priority": 1
            },
            "budget": {
                "keywords": [
                    "budget", "budgeting", "expenses", "spending", "income",
                    "cash flow", "financial planning", "money management",
                    "cost", "affordability", "lifestyle", "discretionary spending"
                ],
                "priority": 2
            },
            "estate": {
                "keywords": [
                    "estate", "estate planning", "will", "trust", "inheritance",
                    "beneficiary", "heir", "probate", "executor", "power of attorney",
                    "life insurance", "legacy", "wealth transfer", "generation skipping"
                ],
                "priority": 2
            },
            "insurance": {
                "keywords": [
                    "insurance", "life insurance", "disability insurance", 
                    "health insurance", "property insurance", "liability", 
                    "coverage", "premium", "deductible", "claim", "policy",
                    "umbrella insurance", "long term care"
                ],
                "priority": 2
            },
            "goals": {
                "keywords": [
                    "goal", "goals", "financial goal", "target", "objective",
                    "plan", "planning", "future", "timeline", "milestone",
                    "financial planning", "life goals", "financial objectives"
                ],
                "priority": 2
            },
            "family": {
                "keywords": [
                    "family", "children", "kids", "education", "college", "529",
                    "childcare", "dependent", "marriage", "divorce", "spouse",
                    "household", "family planning", "education savings"
                ],
                "priority": 2
            }
        }
        
        # Build reverse keyword lookup for fast matching
        self.keyword_to_categories = {}
        for category, data in self.category_keywords.items():
            for keyword in data["keywords"]:
                if keyword not in self.keyword_to_categories:
                    self.keyword_to_categories[keyword] = []
                self.keyword_to_categories[keyword].append({
                    "category": category,
                    "priority": data["priority"]
                })
    
    def analyze_question(self, question: str) -> Dict[str, any]:
        """Analyze a question and determine relevant categories"""
        question_lower = question.lower()
        
        # Find matching keywords
        matched_categories = {}
        
        for keyword, categories in self.keyword_to_categories.items():
            if keyword in question_lower:
                for cat_info in categories:
                    category = cat_info["category"]
                    priority = cat_info["priority"]
                    
                    if category not in matched_categories:
                        matched_categories[category] = {
                            "score": 0,
                            "priority": priority,
                            "keywords": []
                        }
                    
                    matched_categories[category]["score"] += 1
                    matched_categories[category]["keywords"].append(keyword)
        
        # Sort categories by score and priority
        sorted_categories = sorted(
            matched_categories.items(),
            key=lambda x: (x[1]["priority"], x[1]["score"]),
            reverse=True
        )
        
        return {
            "matched_categories": dict(sorted_categories),
            "primary_category": sorted_categories[0][0] if sorted_categories else None,
            "total_matches": sum(cat["score"] for cat in matched_categories.values())
        }
    
    def get_relevant_document_filters(self, question: str) -> Dict[str, any]:
        """Get document filters based on question analysis"""
        analysis = self.analyze_question(question)
        
        if not analysis["matched_categories"]:
            # No specific categories matched, return general filters
            return {
                "categories": [],
                "limit": 10,
                "boost_general": True,
                "search_strategy": "general"
            }
        
        # Get top categories
        top_categories = list(analysis["matched_categories"].keys())[:3]
        
        return {
            "categories": top_categories,
            "limit": 15,
            "primary_category": analysis["primary_category"],
            "boost_general": False,
            "search_strategy": "targeted",
            "analysis": analysis
        }
    
    def filter_documents_by_relevance(self, documents: List[any], question: str) -> List[any]:
        """Filter documents based on question relevance"""
        if not documents:
            return []
        
        analysis = self.analyze_question(question)
        
        if not analysis["matched_categories"]:
            # No specific matching, return first N documents
            return documents[:10]
        
        relevant_docs = []
        general_docs = []
        
        for doc in documents:
            # Check if document metadata contains relevant categories
            doc_category = getattr(doc, 'category', None) or \
                          (hasattr(doc, 'metadata') and doc.metadata.get('category'))
            
            if doc_category and doc_category in analysis["matched_categories"]:
                relevant_docs.append(doc)
            else:
                general_docs.append(doc)
        
        # Combine relevant docs first, then general docs
        filtered = relevant_docs[:8] + general_docs[:5]
        
        return filtered[:15]
    
    def get_search_terms(self, question: str) -> List[str]:
        """Extract relevant search terms from question"""
        analysis = self.analyze_question(question)
        
        # Start with matched keywords
        search_terms = []
        for cat_data in analysis["matched_categories"].values():
            search_terms.extend(cat_data["keywords"])
        
        # Add important words from the question
        important_words = self._extract_important_words(question)
        search_terms.extend(important_words)
        
        # Remove duplicates and return unique terms
        return list(set(search_terms))
    
    def _extract_important_words(self, text: str) -> List[str]:
        """Extract important words from text (excluding common stop words)"""
        stop_words = {
            'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your',
            'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she',
            'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their',
            'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that',
            'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an',
            'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of',
            'at', 'by', 'for', 'with', 'through', 'during', 'before', 'after', 'above',
            'below', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
            'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
            'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some',
            'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
            'very', 'can', 'will', 'just', 'should', 'now', 'get', 'could', 'would'
        }
        
        # Extract words, remove punctuation, filter stop words
        words = re.findall(r'\b\w+\b', text.lower())
        important_words = [word for word in words 
                          if len(word) > 2 and word not in stop_words]
        
        return important_words[:10]  # Return top 10 important words
    
    def get_category_info(self, category: str) -> Optional[Dict]:
        """Get information about a specific category"""
        return self.category_keywords.get(category)
    
    def get_all_categories(self) -> List[str]:
        """Get all available categories"""
        return list(self.category_keywords.keys())


# Global instance
_context_selector_instance: Optional[SmartContextSelector] = None


def get_context_selector() -> SmartContextSelector:
    """Get the global context selector instance"""
    global _context_selector_instance
    
    if _context_selector_instance is None:
        _context_selector_instance = SmartContextSelector()
    
    return _context_selector_instance