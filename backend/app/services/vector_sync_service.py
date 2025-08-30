"""
Vector Sync Service - Unified Data Flow Architecture
Handles PostgreSQL → Foundation → Vector DB synchronization
Ensures all LLM queries use vector-sourced data with live calculations
"""
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
import structlog

from app.models.architecture_contracts import UserFinancialData, ToolsOutput
from app.models.user import User
from app.models.financial import FinancialEntry, EntryCategory
# Import all related models to ensure SQLAlchemy can resolve relationships
from app.models.estate_planning import UserEstatePlanning
from app.models.insurance import UserInsurancePolicy  
from app.models.investment_preferences import UserInvestmentPreferences
from app.services.simple_vector_store import SimpleVectorStore, SimpleDocument, get_vector_store
from app.services.basic_financial_calculator import FinancialCalculator
from app.services.financial_summary_service import financial_summary_service

logger = structlog.get_logger()


class VectorSyncService:
    """
    Unified service for syncing financial data from PostgreSQL to Vector Store
    Includes foundation calculations to ensure LLM has current metrics
    """
    
    def __init__(self):
        self.vector_store = get_vector_store()  # Use singleton instance
        self.calculator = FinancialCalculator()
        logger.info("VectorSyncService initialized")
    
    def _clear_user_vector_data(self, user_id: int) -> int:
        """
        Clear ALL vector documents for a specific user to prevent duplicates
        
        Args:
            user_id: User ID to clear data for
            
        Returns:
            Number of documents removed
        """
        removed_count = 0
        docs_to_remove = []
        
        # Find all documents for this user (check both string and int user_id)
        for doc_id, doc in self.vector_store.documents.items():
            metadata_user_id = doc.metadata.get("user_id")
            if metadata_user_id == user_id or metadata_user_id == str(user_id):
                docs_to_remove.append(doc_id)
        
        # Remove documents
        for doc_id in docs_to_remove:
            if doc_id in self.vector_store.documents:
                del self.vector_store.documents[doc_id]
                removed_count += 1
        
        # Save changes to disk
        if removed_count > 0:
            self.vector_store.save_to_disk()
            logger.info(f"Cleared {removed_count} existing vector documents for user {user_id}")
        
        return removed_count
    
    def sync_user_data(self, user_id: int, db: Session) -> Dict[str, Any]:
        """
        Main sync method - pulls from PostgreSQL, calculates metrics, stores in vector
        This is the SINGLE source of truth for all LLM queries
        
        Args:
            user_id: User ID to sync
            db: Database session
            
        Returns:
            Dict with sync results and metrics
        """
        try:
            logger.info(f"Starting vector sync for user {user_id}")
            
            # Step 1: CLEAR ALL EXISTING VECTOR DATA FOR USER (prevents duplicates)
            removed_count = self._clear_user_vector_data(user_id)
            
            # Step 2: Get user financial data from PostgreSQL
            user_data = self._build_user_financial_data(user_id, db)
            if not user_data:
                return {"status": "error", "message": "Failed to extract user data"}
            
            # Step 2: Run foundation calculations
            tools_output = self._calculate_metrics(user_data)
            
            # Step 3: Build comprehensive vector document with all data
            vector_doc = self._build_vector_document(user_id, user_data, tools_output, db)
            
            # Step 4: Store in vector database
            doc_id = f"user_{user_id}_financial_complete"
            logger.info(f"Attempting to store vector document with ID: {doc_id}")
            logger.info(f"Document content preview: {vector_doc['content'][:200]}...")
            
            result = self.vector_store.add_document(
                content=vector_doc["content"],
                doc_id=doc_id,
                metadata=vector_doc["metadata"]
            )
            logger.info(f"Vector document stored with result: {result}")
            
            # Step 5: Sync additional context documents
            self._sync_transaction_history(user_id, db)
            self._sync_goals(user_id, db)
            self._sync_profile_data(user_id, db)
            self._sync_family_planning(user_id, db)
            self._sync_benefits_tax(user_id, db)
            self._sync_investment_details(user_id, db)
            self._sync_insurance_policies(user_id, db)
            
            # Sync estate planning documents
            self._sync_estate_planning(user_id, db)
            
            # Sync investment preferences and risk profile
            self._sync_investment_preferences(user_id, db)
            
            # Sync enhanced benefits and tax optimization (priority documents)
            self._sync_enhanced_benefits(user_id, db)
            self._sync_enhanced_tax_optimization(user_id, db)
            
            logger.info(f"Vector sync complete for user {user_id} - Metrics: Savings {tools_output.savings_rate:.1f}%, Emergency {tools_output.liquidity_months:.1f} months")
            
            return {
                "status": "success",
                "user_id": user_id,
                "documents_removed": removed_count,
                "documents_synced": 11,
                "metrics": {
                    "savings_rate": tools_output.savings_rate,
                    "emergency_months": tools_output.liquidity_months,
                    "debt_to_income": tools_output.debt_to_income_ratio,
                    "net_worth": tools_output.net_worth
                },
                "last_sync": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Vector sync failed for user {user_id}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _build_user_financial_data(self, user_id: int, db: Session) -> Optional[UserFinancialData]:
        """
        Extract user financial data from PostgreSQL using data contracts
        """
        try:
            # Get financial summary
            summary = financial_summary_service.get_user_financial_summary(user_id, db)
            
            if 'error' in summary:
                logger.warning(f"Financial summary error for user {user_id}: {summary.get('error')}")
                return None
            
            # Extract data with safe defaults
            monthly_income = summary.get('monthlyIncome', 0)
            monthly_expenses = summary.get('monthlyExpenses', 0)
            monthly_debt_payments = summary.get('monthlyDebtPayments', 0)
            
            # Extract cash reserves
            assets_breakdown = summary.get('assetsBreakdown', {})
            cash_bank_accounts = assets_breakdown.get('cash_bank_accounts', [])
            cash_reserves = 0
            if isinstance(cash_bank_accounts, list):
                cash_reserves = sum(
                    float(account.get('value', 0)) 
                    for account in cash_bank_accounts 
                    if isinstance(account, dict) and account.get('value') is not None
                )
            
            # Calculate actual portfolio value from investment accounts
            investment_accounts = assets_breakdown.get('investment_accounts', [])
            retirement_accounts = assets_breakdown.get('retirement_accounts', [])
            portfolio_value = 0
            
            if isinstance(investment_accounts, list):
                portfolio_value += sum(
                    float(account.get('value', 0))
                    for account in investment_accounts
                    if isinstance(account, dict) and account.get('value') is not None
                )
            
            if isinstance(retirement_accounts, list):
                portfolio_value += sum(
                    float(account.get('value', 0))
                    for account in retirement_accounts
                    if isinstance(account, dict) and account.get('value') is not None
                )
            
            # Get actual total debts from financial summary (note: camelCase field name)
            total_debts = float(summary.get('totalLiabilities', 0))
            
            # Monthly debt payments - get from existing calculation or estimate
            monthly_debt_payments = float(summary.get('monthlyDebtPayments', 0))
            
            # If no monthly debt payments provided, estimate based on total debt
            # Typical minimum payment is ~2-3% of balance for credit cards, 1% for mortgages
            if monthly_debt_payments == 0 and total_debts > 0:
                # Rough estimate: assume mix of mortgage (1%) and credit cards (2.5%)
                monthly_debt_payments = total_debts * 0.015  # 1.5% average
            
            # Build structured data using contract
            user_data = UserFinancialData(
                user_id=str(user_id),
                age=summary.get('age', 35),
                retirement_age=summary.get('retirement_age', 65),
                monthly_income=float(monthly_income),
                monthly_expenses=float(monthly_expenses),
                monthly_debt_payments=float(monthly_debt_payments),
                total_assets=float(summary.get('netWorth', 0) + total_debts),
                total_debts=float(total_debts),  # This now has the correct value from total_liabilities
                portfolio_value=float(portfolio_value),
                cash_reserves=float(cash_reserves)
            )
            
            return user_data
            
        except Exception as e:
            logger.error(f"Failed to build user financial data: {str(e)}")
            return None
    
    def _calculate_metrics(self, user_data: UserFinancialData) -> ToolsOutput:
        """
        Calculate foundation metrics using the calculator
        """
        try:
            # Run core calculations
            savings_rate = self.calculator.calculate_savings_rate(
                user_data.monthly_income, 
                user_data.monthly_expenses
            )
            
            liquidity_months = self.calculator.calculate_emergency_months(
                user_data.cash_reserves, 
                user_data.monthly_expenses
            )
            
            debt_to_income_ratio = self.calculator.calculate_debt_to_income(
                user_data.monthly_debt_payments, 
                user_data.monthly_income
            )
            
            # Calculate additional metrics
            net_worth = user_data.total_assets - user_data.total_debts
            years_to_retirement = max(0, user_data.retirement_age - user_data.age)
            
            return ToolsOutput(
                savings_rate=savings_rate,
                liquidity_months=liquidity_months,
                debt_to_income_ratio=debt_to_income_ratio,
                net_worth=net_worth,
                years_to_retirement=years_to_retirement
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate metrics: {str(e)}")
            # Return safe defaults
            return ToolsOutput(
                savings_rate=0.0,
                liquidity_months=0.0,
                debt_to_income_ratio=0.0,
                net_worth=0.0,
                years_to_retirement=30.0
            )
    
    def _build_vector_document(self, user_id: int, user_data: UserFinancialData, 
                              tools_output: ToolsOutput, db: Session) -> Dict[str, Any]:
        """
        Build comprehensive vector document with ALL financial data and calculations
        This becomes the SINGLE source of truth for LLM queries
        """
        # Get user profile info
        user = db.query(User).filter(User.id == user_id).first()
        name = f"{user.first_name} {user.last_name}".strip() if user else "User"
        
        # Get comprehensive financial summary with ALL detailed data
        detailed_summary = financial_summary_service.get_user_financial_summary(user_id, db)
        
        # Get detailed expense and income breakdowns by querying financial entries directly
        from app.models.financial import FinancialEntry, EntryCategory, FrequencyType
        all_entries = db.query(FinancialEntry).filter(
            FinancialEntry.user_id == user_id,
            FinancialEntry.is_active == True
        ).all()
        
        # Build expense breakdown
        expense_breakdown = {}
        income_breakdown = {}
        
        for entry in all_entries:
            if entry.category == EntryCategory.expenses:
                category = entry.subcategory or 'other'
                if category not in expense_breakdown:
                    expense_breakdown[category] = []
                
                # Convert to monthly amount
                monthly_amount = float(entry.amount)
                if entry.frequency == FrequencyType.annually:
                    monthly_amount = monthly_amount / 12
                elif entry.frequency == FrequencyType.weekly:
                    monthly_amount = monthly_amount * 52 / 12
                
                expense_breakdown[category].append({
                    'name': entry.description,
                    'amount': monthly_amount
                })
            
            elif entry.category == EntryCategory.income:
                category = entry.subcategory or 'other'
                if category not in income_breakdown:
                    income_breakdown[category] = []
                
                # Convert to monthly amount
                monthly_amount = float(entry.amount)
                if entry.frequency == FrequencyType.annually:
                    monthly_amount = monthly_amount / 12
                elif entry.frequency == FrequencyType.weekly:
                    monthly_amount = monthly_amount * 52 / 12
                
                income_breakdown[category].append({
                    'name': entry.description,
                    'amount': monthly_amount
                })
        
        # Get the actual total debts from the detailed summary (which has correct values) 
        actual_total_debts = float(detailed_summary.get('totalLiabilities', user_data.total_debts))
        
        # Build structured content with ALL PostgreSQL data
        content = f"""COMPLETE FINANCIAL PROFILE FOR {name} (User ID: {user_id})
========================================================
Last Updated: {datetime.utcnow().isoformat()}

📊 CURRENT FINANCIAL POSITION (LIVE DATA):
• Monthly Income: ${user_data.monthly_income:,.0f}
• Monthly Expenses: ${user_data.monthly_expenses:,.0f}  
• Monthly Debt Payments: ${user_data.monthly_debt_payments:,.0f}
• Cash Reserves: ${user_data.cash_reserves:,.0f}
• Total Assets: ${user_data.total_assets:,.0f}
• Total Debts: ${actual_total_debts:,.0f}
• Portfolio Value: ${user_data.portfolio_value:,.0f}
• Net Worth: ${tools_output.net_worth:,.0f}

📈 CALCULATED FINANCIAL METRICS (FOUNDATION):
• Savings Rate: {tools_output.savings_rate:.1f}%
• Emergency Fund Coverage: {tools_output.liquidity_months:.1f} months
• Debt-to-Income Ratio: {tools_output.debt_to_income_ratio:.1f}%
• Years to Retirement: {tools_output.years_to_retirement} years

💰 DETAILED ASSET BREAKDOWN (ALL POSTGRESQL DATA):"""
        
        # Add detailed assets breakdown from PostgreSQL
        assets_breakdown = detailed_summary.get('assetsBreakdown', {})
        for category, assets in assets_breakdown.items():
            if isinstance(assets, list) and assets:
                category_name = category.replace('_', ' ').title()
                content += f"\n\n🏦 {category_name}:"
                total_category = 0
                for asset in assets:
                    if isinstance(asset, dict):
                        name = asset.get('name', 'Unknown')
                        value = asset.get('value', 0)
                        total_category += float(value)
                        content += f"\n   • {name}: ${float(value):,.0f}"
                content += f"\n   → Subtotal: ${total_category:,.0f}"
        
        # Add detailed expenses breakdown
        content += f"\n\n💸 DETAILED EXPENSES BREAKDOWN (MONTHLY):"
        total_expenses = 0
        for category, expenses in expense_breakdown.items():
            if expenses:
                category_name = category.replace('_', ' ').title()
                content += f"\n\n🏷️ {category_name}:"
                category_total = 0
                for expense in expenses:
                    name = expense['name']
                    amount = expense['amount']
                    category_total += amount
                    total_expenses += amount
                    content += f"\n   • {name}: ${amount:,.0f}"
                content += f"\n   → Subtotal: ${category_total:,.0f}"
        content += f"\n\n💸 TOTAL MONTHLY EXPENSES: ${total_expenses:,.0f}"
        
        # Add income sources
        content += f"\n\n💼 INCOME SOURCES (MONTHLY):"
        total_income = 0
        for category, incomes in income_breakdown.items():
            if incomes:
                category_name = category.replace('_', ' ').title()
                content += f"\n\n💰 {category_name}:"
                category_total = 0
                for income in incomes:
                    name = income['name']
                    amount = income['amount']
                    category_total += amount
                    total_income += amount
                    content += f"\n   • {name}: ${amount:,.0f}"
                content += f"\n   → Subtotal: ${category_total:,.0f}"
        content += f"\n\n💼 TOTAL MONTHLY INCOME: ${total_income:,.0f}"
        
        # Add liabilities details - skip complex comprehensive summary import to avoid async issues
        try:
            # Get liabilities directly from financial entries
            liability_entries = db.query(FinancialEntry).filter(
                FinancialEntry.user_id == user_id,
                FinancialEntry.is_active == True,
                FinancialEntry.category == EntryCategory.LIABILITIES
            ).all()
            
            liabilities = []
            for entry in liability_entries:
                liabilities.append({
                    'name': entry.description,
                    'current_balance': float(entry.amount) if entry.amount else 0,
                    'category': entry.subcategory or 'other'
                })
            
            if liabilities:
                content += f"\n\n💳 DETAILED LIABILITIES:"
                total_liability_check = 0
                for liability in liabilities:
                    if isinstance(liability, dict):
                        name = liability.get('name', 'Unknown')
                        # Use 'balance' field which is what the comprehensive summary uses
                        amount = liability.get('balance', liability.get('amount', 0))
                        total_liability_check += float(amount)
                        content += f"\n   • {name}: ${float(amount):,.0f}"
                        
                        # Add category info
                        category = liability.get('subcategory', liability.get('type', ''))
                        if category:
                            content += f" ({category.replace('_', ' ').title()})"
                
                content += f"\n\n💳 TOTAL LIABILITIES: ${total_liability_check:,.0f}"
        except Exception as e:
            # Fallback to original approach if comprehensive data fails
            logger.warning(f"Failed to get comprehensive liability data: {str(e)}")
            content += f"\n\n💳 TOTAL LIABILITIES: ${float(user_data.total_debts):,.0f}"
        
        # Add financial health indicators
        content += f"""

💡 FINANCIAL HEALTH INDICATORS:
• Savings Health: {'Excellent' if tools_output.savings_rate > 20 else 'Good' if tools_output.savings_rate > 10 else 'Needs Improvement'}
• Emergency Fund: {'Strong' if tools_output.liquidity_months >= 6 else 'Adequate' if tools_output.liquidity_months >= 3 else 'Build Emergency Fund'}
• Debt Load: {'Low' if tools_output.debt_to_income_ratio < 20 else 'Moderate' if tools_output.debt_to_income_ratio < 35 else 'High'}

IMPORTANT: This data is current and calculated from live PostgreSQL data. 
Always use these exact values when answering user questions."""
        
        # Build metadata for search and filtering
        metadata = {
            "user_id": user_id,
            "document_type": "financial_complete",
            "last_sync": datetime.utcnow().isoformat(),
            "metrics": {
                "savings_rate": tools_output.savings_rate,
                "emergency_months": tools_output.liquidity_months,
                "debt_to_income": tools_output.debt_to_income_ratio,
                "net_worth": tools_output.net_worth
            },
            "data": {
                "monthly_income": user_data.monthly_income,
                "monthly_expenses": user_data.monthly_expenses,
                "cash_reserves": user_data.cash_reserves,
                "portfolio_value": user_data.portfolio_value
            },
            "version": "2.0"  # Version 2.0 indicates unified data flow
        }
        
        return {
            "content": content,
            "metadata": metadata
        }
    
    def _sync_transaction_history(self, user_id: int, db: Session):
        """
        Sync recent transaction history to vector store
        """
        try:
            # Get recent financial entries
            recent_entries = db.query(FinancialEntry).filter(
                FinancialEntry.user_id == user_id,
                FinancialEntry.is_active == True
            ).order_by(FinancialEntry.created_at.desc()).limit(50).all()
            
            if recent_entries:
                transactions_content = "RECENT FINANCIAL TRANSACTIONS:\n"
                for entry in recent_entries[:20]:  # Top 20 most recent
                    # Clean up category enum representation
                    category = str(entry.category).split('.')[-1].title() if hasattr(entry.category, 'value') else str(entry.category)
                    transactions_content += f"• {category} - {entry.description}: ${entry.amount:,.0f}\n"
                
                doc_id = f"user_{user_id}_transactions"
                self.vector_store.add_document(
                    doc_id=doc_id,
                    content=transactions_content,
                    metadata={
                        "user_id": user_id,
                        "document_type": "transactions",
                        "count": len(recent_entries)
                    }
                )
                
        except Exception as e:
            logger.warning(f"Failed to sync transactions for user {user_id}: {str(e)}")
    
    def _sync_goals(self, user_id: int, db: Session):
        """
        Sync user goals to vector store
        """
        try:
            from app.models.goals_v2 import Goal
            
            # Goal model doesn't have is_active field, get all goals for user
            goals = db.query(Goal).filter(Goal.user_id == user_id).all()
            
            if goals:
                goals_content = "FINANCIAL GOALS:\n"
                for goal in goals:
                    progress = (float(goal.current_amount) / float(goal.target_amount) * 100) if goal.target_amount else 0
                    goals_content += f"• {goal.name}: ${float(goal.current_amount):,.0f} / ${float(goal.target_amount):,.0f} ({progress:.1f}% complete)\n"
                
                doc_id = f"user_{user_id}_goals"
                self.vector_store.add_document(
                    doc_id=doc_id,
                    content=goals_content,
                    metadata={
                        "user_id": user_id,
                        "document_type": "goals",
                        "count": len(goals)
                    }
                )
                
        except Exception as e:
            logger.warning(f"Failed to sync goals for user {user_id}: {str(e)}")
    
    def _sync_profile_data(self, user_id: int, db: Session):
        """
        Sync user profile and demographics to vector store
        """
        try:
            from app.models.user_profile import UserProfile
            
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            if profile:
                profile_content = f"""USER PROFILE AND DEMOGRAPHICS:
========================================
Personal Information:
• Age: {profile.age or 'Not specified'}
• Date of Birth: {profile.date_of_birth or 'Not specified'}
• Gender: {profile.gender or 'Not specified'}
• Marital Status: {profile.marital_status or 'Not specified'}
• Location: {profile.city or ''} {profile.state or ''} {profile.zip_code or ''}
• Country: {profile.country or 'USA'}

Employment Information:
• Employment Status: {profile.employment_status or 'Not specified'}
• Occupation: {profile.occupation or 'Not specified'}

Financial Preferences:
• Risk Tolerance: {profile.risk_tolerance or 'moderate'}
• Risk Tolerance Score: {profile.risk_tolerance_score or 5}/10
• Retirement Age Goal: {profile.retirement_age or 65}
• Retirement Goal Amount: ${float(profile.retirement_goal or 0):,.0f}
• Emergency Fund Target: {profile.emergency_fund_months or 6} months

Social Security Estimates:
• Expected Social Security Age: {profile.social_security_age or 67}
• Estimated Monthly Benefit: ${float(profile.social_security_monthly or 0):,.0f}

Contact Information:
• Phone: {profile.phone or 'Not provided'}
• Address: {profile.address or 'Not provided'}
• Emergency Contact: {profile.emergency_contact or 'Not provided'}

Additional Notes: {profile.notes or 'None'}
Profile Last Updated: {profile.updated_at or profile.created_at}"""
                
                doc_id = f"user_{user_id}_profile_complete"
                self.vector_store.add_document(
                    doc_id=doc_id,
                    content=profile_content,
                    metadata={
                        "user_id": user_id,
                        "document_type": "profile",
                        "age": profile.age,
                        "employment": profile.employment_status,
                        "risk_tolerance": profile.risk_tolerance
                    }
                )
                
        except Exception as e:
            logger.warning(f"Failed to sync profile for user {user_id}: {str(e)}")
    
    def _sync_family_planning(self, user_id: int, db: Session):
        """
        Sync family members and dependents information
        """
        try:
            from app.models.user_profile import UserProfile, FamilyMember
            
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if not profile:
                return
            
            family_members = db.query(FamilyMember).filter(FamilyMember.profile_id == profile.id).all()
            
            if family_members:
                family_content = "FAMILY AND DEPENDENTS INFORMATION:\n"
                family_content += "="*50 + "\n\n"
                
                for member in family_members:
                    family_content += f"{member.relationship_type.upper()}: {member.name or 'Unknown'}\n"
                    family_content += f"• Age: {member.age or 'Not specified'}\n"
                    
                    if member.income:
                        family_content += f"• Income: ${float(member.income):,.0f}\n"
                    if member.retirement_savings:
                        family_content += f"• Retirement Savings: ${float(member.retirement_savings):,.0f}\n"
                    
                    # For children
                    if member.relationship_type == 'child':
                        if member.education_fund_target:
                            family_content += f"• College Fund Target: ${float(member.education_fund_target):,.0f}\n"
                        if member.education_fund_current:
                            family_content += f"• Current College Savings: ${float(member.education_fund_current):,.0f}\n"
                        if member.expected_college_year:
                            family_content += f"• Expected College Year: {member.expected_college_year}\n"
                    
                    # For aging parents
                    if member.requires_financial_support:
                        family_content += f"• Requires Financial Support: Yes\n"
                        if member.monthly_support_amount:
                            family_content += f"• Monthly Support: ${float(member.monthly_support_amount):,.0f}\n"
                        if member.care_cost_estimate:
                            family_content += f"• Care Cost Estimate: ${float(member.care_cost_estimate):,.0f}\n"
                    
                    family_content += "\n"
                
                doc_id = f"user_{user_id}_family_planning"
                self.vector_store.add_document(
                    doc_id=doc_id,
                    content=family_content,
                    metadata={
                        "user_id": user_id,
                        "document_type": "family",
                        "member_count": len(family_members)
                    }
                )
                
        except Exception as e:
            logger.warning(f"Failed to sync family planning for user {user_id}: {str(e)}")
    
    def _sync_benefits_tax(self, user_id: int, db: Session):
        """
        Sync enhanced user benefits and tax information including Social Security optimization and advanced tax strategies
        """
        try:
            from app.models.user_profile import UserProfile, UserBenefit, UserTaxInfo
            
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if not profile:
                return
            
            benefits = db.query(UserBenefit).filter(UserBenefit.profile_id == profile.id).all()
            tax_info = db.query(UserTaxInfo).filter(UserTaxInfo.profile_id == profile.id).first()
            
            content = "ENHANCED BENEFITS AND TAX INFORMATION:\n"
            content += "="*60 + "\n\n"
            
            # Benefits section with enhanced data
            if benefits:
                content += "EMPLOYEE BENEFITS AND RETIREMENT PLANNING:\n"
                for benefit in benefits:
                    content += f"\n{benefit.benefit_type.upper()}: {benefit.benefit_name or 'Unknown'}\n"
                    
                    # Enhanced Social Security details
                    if benefit.benefit_type == 'social_security':
                        if benefit.estimated_monthly_benefit:
                            content += f"• Estimated Monthly Benefit at FRA: ${float(benefit.estimated_monthly_benefit):,.0f}\n"
                        if benefit.full_retirement_age:
                            content += f"• Full Retirement Age: {benefit.full_retirement_age}\n"
                        
                        # Enhanced Social Security planning fields from profile
                        if benefit.estimated_monthly_benefit:
                            base_benefit = float(benefit.estimated_monthly_benefit)
                            content += f"• Current SS Benefit Estimate: ${base_benefit:,.0f}\n"
                            
                            # Use FRA as default claiming age since claiming_age field doesn't exist
                            claiming_age = benefit.full_retirement_age or 67
                            content += f"• Default Claiming Age: {claiming_age} (FRA)\n"
                            
                            # Calculate benefit adjustment scenarios
                            fra = benefit.full_retirement_age or 67
                            
                            if base_benefit > 0:
                                adjustment_factor = 1
                                if claiming_age < fra:
                                    years_early = fra - claiming_age
                                    adjustment_factor = 1 - (years_early * 0.0667)  # ~6.67% per year early
                                elif claiming_age > fra:
                                    years_delayed = min(claiming_age - fra, 70 - fra)
                                    adjustment_factor = 1 + (years_delayed * 0.08)  # 8% per year delayed
                                
                                adjusted_benefit = base_benefit * adjustment_factor
                                annual_benefit = adjusted_benefit * 12
                                content += f"• Adjusted Monthly Benefit at Age {claiming_age}: ${adjusted_benefit:,.0f}\n"
                                content += f"• Estimated Annual SS Income: ${annual_benefit:,.0f}\n"
                                content += f"• Benefit Adjustment Factor: {adjustment_factor:.3f} ({(adjustment_factor * 100):.1f}%)\n"
                        
                        if benefit.spouse_benefit_eligible:
                            content += f"• Spouse Benefit Eligible: Yes\n"
                            if benefit.spouse_benefit_amount:
                                content += f"• Spouse Benefit Amount: ${float(benefit.spouse_benefit_amount):,.0f}\n"
                    
                    # Enhanced Pension details with JSON data
                    if benefit.benefit_type == 'pension':
                        if benefit.expected_monthly_payout:
                            content += f"• Expected Monthly Payout: ${float(benefit.expected_monthly_payout):,.0f}\n"
                        if benefit.vested_percentage:
                            content += f"• Vested: {float(benefit.vested_percentage)}%\n"
                        if benefit.pension_type:
                            content += f"• Pension Type: {benefit.pension_type.replace('_', ' ').title()}\n"
                        if benefit.lump_sum_option:
                            content += f"• Lump Sum Option Available: Yes\n"
                        
                        # Enhanced pension details from JSON field
                        if benefit.pension_details:
                            pension_details = benefit.pension_details
                            if isinstance(pension_details, dict):
                                content += f"• Pension Plan Details:\n"
                                for key, value in pension_details.items():
                                    if value:
                                        key_formatted = key.replace('_', ' ').title()
                                        content += f"  - {key_formatted}: {value}\n"
                    
                    # Enhanced 401(k) and Employer Benefits
                    if benefit.benefit_type in ['401k_match', 'employer_401k']:
                        if benefit.employer_match_percentage:
                            content += f"• Employer Match: {float(benefit.employer_match_percentage)}%\n"
                        if benefit.employer_match_limit:
                            content += f"• Match Limit: ${float(benefit.employer_match_limit):,.0f}\n"
                        
                        # Enhanced 401(k) matching formula
                        if benefit.employer_401k_match_formula:
                            content += f"• Match Formula: {benefit.employer_401k_match_formula}\n"
                        if benefit.employer_401k_vesting_schedule:
                            content += f"• Vesting Schedule: {benefit.employer_401k_vesting_schedule}\n"
                    
                    # Other benefits details from JSON field
                    if benefit.other_benefits:
                        other_benefits = benefit.other_benefits
                        if isinstance(other_benefits, dict):
                            content += f"• Additional Benefits:\n"
                            for key, value in other_benefits.items():
                                if value:
                                    key_formatted = key.replace('_', ' ').title()
                                    content += f"  - {key_formatted}: {value}\n"
                    
                    # Health insurance and other employer contributions
                    if benefit.health_insurance_premium:
                        content += f"• Health Insurance Premium: ${float(benefit.health_insurance_premium):,.0f}/year\n"
                    if benefit.employer_contribution:
                        content += f"• Employer Contribution: ${float(benefit.employer_contribution):,.0f}\n"
            
            # Enhanced Tax section with advanced strategies
            if tax_info:
                content += f"\n\nADVANCED TAX INFORMATION AND STRATEGIES (Tax Year {tax_info.tax_year}):\n"
                content += f"• Filing Status: {tax_info.filing_status or 'Not specified'}\n"
                content += f"• Federal Tax Bracket: {float(tax_info.federal_tax_bracket or 0):.0f}%\n"
                
                # Enhanced state tax information
                if tax_info.state_tax_bracket:
                    content += f"• State Tax Bracket: {float(tax_info.state_tax_bracket):.0f}%\n"
                if tax_info.state_tax_rate:
                    content += f"• State Tax Rate: {float(tax_info.state_tax_rate):.1f}%\n"
                
                if tax_info.effective_tax_rate:
                    content += f"• Effective Tax Rate: {float(tax_info.effective_tax_rate):.1f}%\n"
                if tax_info.marginal_tax_rate:
                    content += f"• Marginal Tax Rate: {float(tax_info.marginal_tax_rate):.1f}%\n"
                if tax_info.adjusted_gross_income:
                    content += f"• Adjusted Gross Income: ${float(tax_info.adjusted_gross_income):,.0f}\n"
                if tax_info.taxable_income:
                    content += f"• Taxable Income: ${float(tax_info.taxable_income):,.0f}\n"
                
                # Tax-advantaged account contributions
                content += f"\nTAX-ADVANTAGED ACCOUNT CONTRIBUTIONS:\n"
                if tax_info.traditional_401k_contribution:
                    content += f"• Traditional 401(k) Contribution: ${float(tax_info.traditional_401k_contribution):,.0f}\n"
                if tax_info.roth_401k_contribution:
                    content += f"• Roth 401(k) Contribution: ${float(tax_info.roth_401k_contribution):,.0f}\n"
                if tax_info.traditional_ira_contribution:
                    content += f"• Traditional IRA Contribution: ${float(tax_info.traditional_ira_contribution):,.0f}\n"
                if tax_info.roth_ira_contribution:
                    content += f"• Roth IRA Contribution: ${float(tax_info.roth_ira_contribution):,.0f}\n"
                if tax_info.hsa_contribution:
                    content += f"• HSA Contribution: ${float(tax_info.hsa_contribution):,.0f}\n"
                
                # Contribution limits
                if tax_info.max_401k_contribution or tax_info.max_ira_contribution or tax_info.max_hsa_contribution:
                    content += f"\nCONTRIBUTION LIMITS:\n"
                    if tax_info.max_401k_contribution:
                        content += f"• 401(k) Limit: ${float(tax_info.max_401k_contribution):,.0f}\n"
                    if tax_info.max_ira_contribution:
                        content += f"• IRA Limit: ${float(tax_info.max_ira_contribution):,.0f}\n"
                    if tax_info.max_hsa_contribution:
                        content += f"• HSA Limit: ${float(tax_info.max_hsa_contribution):,.0f}\n"
                
                # Deductions and credits
                if tax_info.standard_deduction or tax_info.itemized_deductions:
                    content += f"\nDEDUCTIONS AND CREDITS:\n"
                    if tax_info.standard_deduction:
                        content += f"• Standard Deduction: ${float(tax_info.standard_deduction):,.0f}\n"
                    if tax_info.itemized_deductions:
                        content += f"• Itemized Deductions: ${float(tax_info.itemized_deductions):,.0f}\n"
                    if tax_info.itemized_deduction_total:
                        content += f"• Total Itemized Deductions: ${float(tax_info.itemized_deduction_total):,.0f}\n"
                    if tax_info.tax_credits:
                        content += f"• Tax Credits: ${float(tax_info.tax_credits):,.0f}\n"
                
                # Enhanced tax optimization strategies
                content += f"\nADVANCED TAX OPTIMIZATION STRATEGIES:\n"
                if tax_info.charitable_giving_annual:
                    content += f"• Annual Charitable Giving: ${float(tax_info.charitable_giving_annual):,.0f}\n"
                content += f"• Tax Loss Harvesting: {'Enabled' if tax_info.tax_loss_harvesting_enabled else 'Disabled'}\n"
                content += f"• Backdoor Roth IRA Eligible: {'Yes' if tax_info.backdoor_roth_eligible else 'No'}\n"
                content += f"• Mega Backdoor Roth Available: {'Yes' if tax_info.mega_backdoor_roth_available else 'No'}\n"
                
                # Business income details from JSON field
                if tax_info.business_income_details:
                    business_details = tax_info.business_income_details
                    if isinstance(business_details, dict):
                        content += f"\nBUSINESS INCOME DETAILS:\n"
                        for key, value in business_details.items():
                            if value:
                                key_formatted = key.replace('_', ' ').title()
                                if isinstance(value, (int, float)):
                                    content += f"• {key_formatted}: ${float(value):,.0f}\n"
                                else:
                                    content += f"• {key_formatted}: {value}\n"
                
                # State-specific tax deductions from JSON field
                if tax_info.state_tax_deductions:
                    state_deductions = tax_info.state_tax_deductions
                    if isinstance(state_deductions, dict):
                        content += f"\nSTATE TAX DEDUCTIONS:\n"
                        for key, value in state_deductions.items():
                            if value:
                                key_formatted = key.replace('_', ' ').title()
                                if isinstance(value, (int, float)):
                                    content += f"• {key_formatted}: ${float(value):,.0f}\n"
                                else:
                                    content += f"• {key_formatted}: {value}\n"
                
                # Tax planning strategies from JSON field
                if tax_info.tax_planning_strategies:
                    planning_strategies = tax_info.tax_planning_strategies
                    if isinstance(planning_strategies, dict):
                        content += f"\nMULTI-YEAR TAX PLANNING STRATEGIES:\n"
                        for strategy, details in planning_strategies.items():
                            if details:
                                strategy_formatted = strategy.replace('_', ' ').title()
                                content += f"• {strategy_formatted}:\n"
                                if isinstance(details, dict):
                                    for detail_key, detail_value in details.items():
                                        if detail_value:
                                            detail_formatted = detail_key.replace('_', ' ').title()
                                            content += f"  - {detail_formatted}: {detail_value}\n"
                                else:
                                    content += f"  - Details: {details}\n"
                
                # Tax professional information
                if tax_info.has_tax_professional:
                    content += f"\nTAX PROFESSIONAL SUPPORT:\n"
                    content += f"• Has Tax Professional: Yes\n"
                    if tax_info.tax_professional_name:
                        content += f"• Tax Professional: {tax_info.tax_professional_name}\n"
                    if tax_info.estimated_quarterly_payments:
                        content += f"• Estimated Quarterly Payments: Yes\n"
                        if tax_info.quarterly_payment_amount:
                            content += f"• Quarterly Payment Amount: ${float(tax_info.quarterly_payment_amount):,.0f}\n"
                
                if tax_info.tax_strategy_notes:
                    content += f"\nTAX STRATEGY NOTES:\n{tax_info.tax_strategy_notes}\n"
            
            # Add comprehensive context for LLM advisory
            content += f"\n\nCONTEXT FOR FINANCIAL ADVISORY:\n"
            content += f"This enhanced benefits and tax information enables sophisticated retirement planning, Social Security optimization, and advanced tax strategy recommendations. "
            content += f"Use this data to provide personalized advice on claiming strategies, tax-advantaged account optimization, and multi-year tax planning.\n"
            
            doc_id = f"user_{user_id}_benefits_tax_enhanced"
            self.vector_store.add_document(
                doc_id=doc_id,
                content=content,
                metadata={
                    "user_id": user_id,
                    "document_type": "benefits_tax_enhanced",
                    "has_benefits": len(benefits) > 0,
                    "has_tax_info": tax_info is not None,
                    "has_social_security_optimization": any(b.estimated_monthly_benefit for b in benefits if b.benefit_type == 'social_security'),
                    "has_401k_matching_details": any(b.employer_match_percentage for b in benefits if b.benefit_type in ['401k_match', 'employer_401k']),
                    "has_advanced_tax_strategies": bool(tax_info and (tax_info.backdoor_roth_eligible or tax_info.tax_loss_harvesting_enabled)),
                    "version": "enhanced_v1.0"
                }
            )
            
        except Exception as e:
            logger.warning(f"Failed to sync enhanced benefits and tax for user {user_id}: {str(e)}")
    
    def _sync_investment_details(self, user_id: int, db: Session):
        """
        Sync detailed investment and portfolio information
        """
        try:
            # Get all investment and retirement accounts
            investment_entries = db.query(FinancialEntry).filter(
                FinancialEntry.user_id == user_id,
                FinancialEntry.is_active == True,
                FinancialEntry.category == EntryCategory.assets,
                FinancialEntry.subcategory.in_(['investment_accounts', 'retirement_accounts'])
            ).all()
            
            if investment_entries:
                content = "INVESTMENT PORTFOLIO DETAILS:\n"
                content += "="*50 + "\n\n"
                
                total_portfolio = 0
                investment_accounts = []
                retirement_accounts = []
                
                for entry in investment_entries:
                    amount = float(entry.amount)
                    total_portfolio += amount
                    
                    account_info = {
                        'name': entry.description,
                        'value': amount,
                        'allocation': {}
                    }
                    
                    # Get asset allocation if available
                    if entry.stocks_percentage or entry.bonds_percentage or entry.cash_percentage:
                        account_info['allocation'] = {
                            'stocks': entry.stocks_percentage or 0,
                            'bonds': entry.bonds_percentage or 0,
                            'cash': entry.cash_percentage or 0,
                            'real_estate': entry.real_estate_percentage or 0,
                            'alternatives': entry.alternative_percentage or 0
                        }
                    
                    if entry.subcategory == 'investment_accounts':
                        investment_accounts.append(account_info)
                    else:
                        retirement_accounts.append(account_info)
                
                # Investment accounts
                if investment_accounts:
                    content += "TAXABLE INVESTMENT ACCOUNTS:\n"
                    for account in investment_accounts:
                        content += f"\n• {account['name']}: ${account['value']:,.0f}\n"
                        if account['allocation']:
                            content += "  Asset Allocation:\n"
                            for asset, pct in account['allocation'].items():
                                if pct > 0:
                                    content += f"    - {asset.capitalize()}: {pct}%\n"
                
                # Retirement accounts
                if retirement_accounts:
                    content += "\n\nRETIREMENT ACCOUNTS:\n"
                    for account in retirement_accounts:
                        content += f"\n• {account['name']}: ${account['value']:,.0f}\n"
                        if account['allocation']:
                            content += "  Asset Allocation:\n"
                            for asset, pct in account['allocation'].items():
                                if pct > 0:
                                    content += f"    - {asset.capitalize()}: {pct}%\n"
                
                # Portfolio summary
                content += f"\n\nPORTFOLIO SUMMARY:\n"
                content += f"• Total Portfolio Value: ${total_portfolio:,.0f}\n"
                content += f"• Number of Investment Accounts: {len(investment_accounts)}\n"
                content += f"• Number of Retirement Accounts: {len(retirement_accounts)}\n"
                
                # Calculate overall allocation
                total_stocks = sum(acc['value'] * acc['allocation'].get('stocks', 0) / 100 
                                 for acc in investment_accounts + retirement_accounts 
                                 if acc['allocation'])
                total_bonds = sum(acc['value'] * acc['allocation'].get('bonds', 0) / 100 
                                for acc in investment_accounts + retirement_accounts 
                                if acc['allocation'])
                total_cash = sum(acc['value'] * acc['allocation'].get('cash', 0) / 100 
                               for acc in investment_accounts + retirement_accounts 
                               if acc['allocation'])
                
                if total_portfolio > 0:
                    content += f"\n• Overall Asset Allocation:\n"
                    content += f"  - Stocks: {(total_stocks/total_portfolio*100):.1f}%\n"
                    content += f"  - Bonds: {(total_bonds/total_portfolio*100):.1f}%\n"
                    content += f"  - Cash: {(total_cash/total_portfolio*100):.1f}%\n"
                
                doc_id = f"user_{user_id}_investments_detailed"
                self.vector_store.add_document(
                    doc_id=doc_id,
                    content=content,
                    metadata={
                        "user_id": user_id,
                        "document_type": "investments",
                        "total_value": total_portfolio,
                        "account_count": len(investment_entries)
                    }
                )
                
        except Exception as e:
            logger.warning(f"Failed to sync investment details for user {user_id}: {str(e)}")
    
    def _sync_insurance_policies(self, user_id: int, db: Session):
        """
        Sync user insurance policies to vector store
        """
        try:
            from app.models.insurance import UserInsurancePolicy
            
            # Get all insurance policies for user
            policies = db.query(UserInsurancePolicy).filter(
                UserInsurancePolicy.user_id == user_id
            ).order_by(UserInsurancePolicy.policy_type, UserInsurancePolicy.policy_name).all()
            
            if policies:
                insurance_content = "INSURANCE COVERAGE:\n"
                insurance_content += "="*50 + "\n\n"
                
                # Group policies by type
                policy_types = {}
                total_annual_premiums = 0
                total_coverage = 0
                
                for policy in policies:
                    policy_type = policy.policy_type.upper()
                    if policy_type not in policy_types:
                        policy_types[policy_type] = []
                    
                    policy_types[policy_type].append(policy)
                    
                    if policy.annual_premium:
                        total_annual_premiums += float(policy.annual_premium)
                    if policy.coverage_amount:
                        total_coverage += float(policy.coverage_amount)
                
                # Add summary
                insurance_content += f"INSURANCE PORTFOLIO SUMMARY:\n"
                insurance_content += f"• Total Policies: {len(policies)}\n"
                insurance_content += f"• Total Annual Premiums: ${total_annual_premiums:,.2f}\n"
                insurance_content += f"• Total Coverage Amount: ${total_coverage:,.2f}\n"
                insurance_content += f"• Policy Types: {len(policy_types)}\n\n"
                
                # Add policies by type
                for policy_type, type_policies in policy_types.items():
                    insurance_content += f"{policy_type} INSURANCE:\n"
                    
                    for policy in type_policies:
                        insurance_content += f"\n• {policy.policy_name}:\n"
                        if policy.coverage_amount:
                            insurance_content += f"  - Coverage: ${float(policy.coverage_amount):,.2f}\n"
                        if policy.annual_premium:
                            insurance_content += f"  - Annual Premium: ${float(policy.annual_premium):,.2f}\n"
                        if policy.beneficiary_primary:
                            insurance_content += f"  - Primary Beneficiary: {policy.beneficiary_primary}\n"
                        if policy.beneficiary_secondary:
                            insurance_content += f"  - Secondary Beneficiary: {policy.beneficiary_secondary}\n"
                        
                        # Add policy-specific details
                        if policy.policy_details:
                            details = policy.policy_details
                            if policy.policy_type == 'life':
                                if details.get('policy_type_detail'):
                                    insurance_content += f"  - Type: {details['policy_type_detail'].title()} Life\n"
                                if details.get('term_years'):
                                    insurance_content += f"  - Term: {details['term_years']} years\n"
                                if details.get('cash_value'):
                                    insurance_content += f"  - Cash Value: ${float(details['cash_value']):,.2f}\n"
                            elif policy.policy_type == 'disability':
                                if details.get('coverage_type'):
                                    insurance_content += f"  - Coverage Type: {details['coverage_type'].replace('_', ' ').title()}\n"
                                if details.get('benefit_percentage'):
                                    insurance_content += f"  - Benefit: {details['benefit_percentage']}% of income\n"
                            elif policy.policy_type == 'health':
                                if details.get('plan_type'):
                                    insurance_content += f"  - Plan Type: {details['plan_type']}\n"
                                if details.get('deductible'):
                                    insurance_content += f"  - Deductible: ${float(details['deductible']):,.2f}\n"
                                if details.get('hsa_eligible'):
                                    insurance_content += f"  - HSA Eligible: Yes\n"
                    
                    insurance_content += "\n"
                
                doc_id = f"user_{user_id}_insurance"
                self.vector_store.add_document(
                    doc_id=doc_id,
                    content=insurance_content,
                    metadata={
                        "user_id": user_id,
                        "document_type": "insurance",
                        "count": len(policies),
                        "total_annual_premiums": total_annual_premiums,
                        "total_coverage": total_coverage,
                        "policy_types": len(policy_types)
                    }
                )
                logger.info(f"Synced {len(policies)} insurance policies for user {user_id}")
                
        except Exception as e:
            logger.warning(f"Failed to sync insurance policies for user {user_id}: {str(e)}")
    
    def _sync_estate_planning(self, user_id: int, db: Session):
        """
        Sync user estate planning documents to vector store
        """
        try:
            from app.models.estate_planning import UserEstatePlanning
            
            # Get all estate planning documents for user
            documents = db.query(UserEstatePlanning).filter(
                UserEstatePlanning.user_id == user_id
            ).order_by(UserEstatePlanning.document_type, UserEstatePlanning.document_name).all()
            
            if documents:
                estate_content = "ESTATE PLANNING:\n"
                estate_content += "="*50 + "\n\n"
                
                # Group documents by type
                document_types = {}
                current_documents = 0
                needs_update = 0
                missing_documents = 0
                
                for doc in documents:
                    doc_type = doc.document_type.upper().replace('_', ' ')
                    if doc_type not in document_types:
                        document_types[doc_type] = []
                    
                    document_types[doc_type].append(doc)
                    
                    # Count by status
                    if doc.status == 'current':
                        current_documents += 1
                    elif doc.status in ['needs_update', 'missing']:
                        needs_update += 1
                        if doc.status == 'missing':
                            missing_documents += 1
                
                # Add summary
                estate_content += f"ESTATE PLANNING SUMMARY:\n"
                estate_content += f"• Total Documents: {len(documents)}\n"
                estate_content += f"• Current Documents: {current_documents}\n"
                estate_content += f"• Documents Needing Updates: {needs_update}\n"
                estate_content += f"• Missing Documents: {missing_documents}\n"
                estate_content += f"• Document Types Covered: {len(document_types)}\n\n"
                
                # Check for essential document gaps
                essential_docs = {'WILL', 'POWER OF ATTORNEY', 'HEALTHCARE DIRECTIVE'}
                existing_types = {doc.document_type.upper().replace('_', ' ') for doc in documents}
                missing_essential = essential_docs - existing_types
                
                if missing_essential:
                    estate_content += f"MISSING ESSENTIAL DOCUMENTS:\n"
                    for missing in missing_essential:
                        estate_content += f"• {missing}\n"
                    estate_content += "\n"
                
                # Add documents by type
                for doc_type, type_docs in document_types.items():
                    estate_content += f"{doc_type}:\n"
                    
                    for doc in type_docs:
                        estate_content += f"\n• {doc.document_name}:\n"
                        estate_content += f"  - Status: {doc.status.replace('_', ' ').title()}\n"
                        
                        if doc.last_updated:
                            estate_content += f"  - Last Updated: {doc.last_updated.strftime('%B %Y')}\n"
                        if doc.next_review_date:
                            estate_content += f"  - Next Review: {doc.next_review_date.strftime('%B %Y')}\n"
                        if doc.attorney_contact:
                            estate_content += f"  - Attorney: {doc.attorney_contact}\n"
                        if doc.document_location:
                            estate_content += f"  - Location: {doc.document_location}\n"
                        
                        # Add document-specific details
                        if doc.document_details:
                            details = doc.document_details
                            if doc.document_type == 'will':
                                if details.get('executor_primary'):
                                    estate_content += f"  - Primary Executor: {details['executor_primary']}\n"
                                if details.get('guardian_children'):
                                    estate_content += f"  - Guardian for Children: {details['guardian_children']}\n"
                            elif doc.document_type == 'trust':
                                if details.get('trust_type'):
                                    estate_content += f"  - Trust Type: {details['trust_type'].title()}\n"
                                if details.get('trustee_primary'):
                                    estate_content += f"  - Primary Trustee: {details['trustee_primary']}\n"
                            elif doc.document_type == 'power_of_attorney':
                                if details.get('poa_type'):
                                    estate_content += f"  - POA Type: {details['poa_type'].title()}\n"
                                if details.get('agent_primary'):
                                    estate_content += f"  - Primary Agent: {details['agent_primary']}\n"
                    
                    estate_content += "\n"
                
                doc_id = f"user_{user_id}_estate_planning"
                self.vector_store.add_document(
                    doc_id=doc_id,
                    content=estate_content,
                    metadata={
                        "user_id": user_id,
                        "document_type": "estate_planning",
                        "total_documents": len(documents),
                        "current_documents": current_documents,
                        "needs_update": needs_update,
                        "missing_documents": missing_documents,
                        "document_types": len(document_types)
                    }
                )
                logger.info(f"Synced {len(documents)} estate planning documents for user {user_id}")
                
        except Exception as e:
            logger.warning(f"Failed to sync estate planning documents for user {user_id}: {str(e)}")
    
    def _sync_investment_preferences(self, user_id: int, db: Session):
        """
        Sync user investment preferences and risk profile to vector store
        """
        try:
            from app.models.investment_preferences import UserInvestmentPreferences
            
            # Get investment preferences for user
            preferences = db.query(UserInvestmentPreferences).filter(
                UserInvestmentPreferences.user_id == user_id
            ).first()
            
            investment_content = "INVESTMENT PREFERENCES AND RISK PROFILE:\n"
            investment_content += "="*50 + "\n\n"
            
            if preferences:
                # Risk Profile
                risk_profile = preferences.risk_profile
                investment_content += f"• Risk Profile: {risk_profile}\n"
                if preferences.risk_tolerance_score:
                    investment_content += f"• Risk Tolerance Score: {preferences.risk_tolerance_score}/10\n"
                
                # Investment Timeline
                timeline_category = preferences.investment_timeline_category
                investment_content += f"• Investment Timeline: {timeline_category}\n"
                if preferences.investment_timeline_years:
                    investment_content += f"• Investment Timeline: {preferences.investment_timeline_years} years\n"
                
                # Asset Allocation Recommendations
                recommended_allocation = preferences.get_recommended_allocation()
                investment_content += f"\nRECOMMENDED ASSET ALLOCATION:\n"
                investment_content += f"• Stocks: {recommended_allocation['stocks']}%\n"
                investment_content += f"• Bonds: {recommended_allocation['bonds']}%\n"
                investment_content += f"• Alternatives: {recommended_allocation['alternatives']}%\n"
                investment_content += f"• International: {recommended_allocation['international']}%\n"
                if recommended_allocation['crypto'] > 0:
                    investment_content += f"• Cryptocurrency: {recommended_allocation['crypto']}%\n"
                
                # Investment Preferences Details
                if preferences.investment_philosophy:
                    investment_content += f"• Investment Philosophy: {preferences.investment_philosophy.title()}\n"
                
                if preferences.rebalancing_frequency:
                    investment_content += f"• Rebalancing Frequency: {preferences.rebalancing_frequency.title()}\n"
                
                # ESG Preferences
                if preferences.esg_preference_level:
                    esg_level_desc = {1: "Low", 2: "Below Average", 3: "Average", 4: "Above Average", 5: "High"}
                    investment_content += f"• ESG Preference: {esg_level_desc.get(preferences.esg_preference_level, 'Unknown')} (Level {preferences.esg_preference_level}/5)\n"
                
                if preferences.international_allocation_target:
                    investment_content += f"• International Allocation Target: {float(preferences.international_allocation_target)}%\n"
                
                # Alternative Investments
                investment_content += f"\nALTERNATIVE INVESTMENTS:\n"
                investment_content += f"• Alternative Investments Interest: {'Yes' if preferences.alternative_investment_interest else 'No'}\n"
                
                if preferences.cryptocurrency_allocation and preferences.cryptocurrency_allocation > 0:
                    investment_content += f"• Cryptocurrency Allocation: {float(preferences.cryptocurrency_allocation)}%\n"
                
                investment_content += f"• Individual Stock Tolerance: {'Yes' if preferences.individual_stock_tolerance else 'No'}\n"
                
                # Tax Strategy
                investment_content += f"\nTAX STRATEGY PREFERENCES:\n"
                investment_content += f"• Tax-Loss Harvesting: {'Enabled' if preferences.tax_loss_harvesting_enabled else 'Disabled'}\n"
                investment_content += f"• Dollar-Cost Averaging: {'Preferred' if preferences.dollar_cost_averaging_preference else 'Not preferred'}\n"
                
                # Sector Preferences
                if preferences.sector_preferences:
                    investment_content += f"\nSECTOR ALLOCATION PREFERENCES:\n"
                    for sector, allocation in preferences.sector_preferences.items():
                        if allocation and float(allocation) > 0:
                            investment_content += f"• {sector.title()}: {float(allocation)*100:.1f}%\n"
                
                # Investment Strategy Summary
                strategy_parts = []
                if risk_profile == "Conservative":
                    strategy_parts.append("capital preservation")
                elif risk_profile == "Moderate":
                    strategy_parts.append("balanced growth")
                elif risk_profile == "Aggressive":
                    strategy_parts.append("maximum growth potential")
                
                if preferences.esg_preference_level and preferences.esg_preference_level >= 4:
                    strategy_parts.append("ESG-focused investing")
                
                if preferences.tax_loss_harvesting_enabled:
                    strategy_parts.append("tax optimization")
                
                if timeline_category == "Long-term":
                    strategy_parts.append("long-term wealth building")
                elif timeline_category == "Short-term":
                    strategy_parts.append("near-term liquidity planning")
                
                if strategy_parts:
                    investment_content += "Based on your preferences, your strategy emphasizes: " + ", ".join(strategy_parts) + ".\n"
                else:
                    investment_content += "Complete your investment preferences assessment for a personalized strategy.\n"
                
                # Store in vector database
                doc_id = f"user_{user_id}_investment_preferences"
                self.vector_store.add_document(
                    doc_id=doc_id,
                    content=investment_content,
                    metadata={
                        "user_id": user_id,
                        "document_type": "investment_preferences",
                        "risk_profile": risk_profile,
                        "risk_score": preferences.risk_tolerance_score,
                        "investment_timeline": preferences.investment_timeline_years,
                        "investment_philosophy": preferences.investment_philosophy,
                        "has_preferences": True
                    }
                )
                
                logger.info(f"Synced investment preferences for user {user_id} - Risk: {risk_profile}")
                
            else:
                # No preferences set - create placeholder document
                investment_content += "No investment preferences or risk assessment completed yet.\n"
                investment_content += "Complete the investment preferences questionnaire to receive:\n"
                investment_content += "• Personalized asset allocation recommendations\n"
                investment_content += "• Risk-appropriate investment strategies\n"
                investment_content += "• Portfolio rebalancing guidance\n"
                investment_content += "• Tax optimization strategies\n"
                
                doc_id = f"user_{user_id}_investment_preferences"
                self.vector_store.add_document(
                    doc_id=doc_id,
                    content=investment_content,
                    metadata={
                        "user_id": user_id,
                        "document_type": "investment_preferences",
                        "has_preferences": False
                    }
                )
                
                logger.info(f"Created placeholder investment preferences document for user {user_id}")
                
        except Exception as e:
            logger.warning(f"Failed to sync investment preferences for user {user_id}: {str(e)}")
    
    def _sync_enhanced_benefits(self, user_id: int, db: Session):
        """
        Create Enhanced Benefits Vector Document with Social Security optimization calculations
        """
        try:
            from app.models.user_profile import UserProfile, UserBenefit
            
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if not profile:
                logger.warning(f"No profile found for user {user_id}")
                return
            
            benefits = db.query(UserBenefit).filter(UserBenefit.profile_id == profile.id).all()
            
            # Build enhanced benefits content with advanced Social Security optimization
            content = "ENHANCED BENEFITS OPTIMIZATION:\n"
            content += "="*60 + "\n\n"
            
            # Social Security Optimization Analysis
            social_security_benefits = [b for b in benefits if b.benefit_type == 'social_security']
            
            if social_security_benefits:
                for ss_benefit in social_security_benefits:
                    content += "SOCIAL SECURITY OPTIMIZATION ANALYSIS:\n"
                    
                    # Base benefit information
                    fra = ss_benefit.full_retirement_age or 67
                    estimated_benefit = float(ss_benefit.estimated_monthly_benefit or 0)
                    claiming_age = fra  # Default to FRA since model doesn't have claiming_age field
                    
                    content += f"• Full Retirement Age (FRA): {fra}\n"
                    content += f"• Estimated Monthly Benefit at FRA: ${estimated_benefit:,.0f}\n"
                    content += f"• Planned Claiming Age: {claiming_age}\n"
                    
                    # Calculate optimized claiming scenarios
                    if estimated_benefit > 0:
                        # Early claiming (age 62)
                        early_reduction = (fra - 62) * 0.0667  # ~6.67% per year early
                        early_benefit = estimated_benefit * (1 - early_reduction)
                        early_annual = early_benefit * 12
                        
                        # FRA benefit
                        fra_annual = estimated_benefit * 12
                        
                        # Delayed claiming (age 70)
                        delay_years = min(70 - fra, 70 - fra)  # Max 3-4 years
                        delay_increase = delay_years * 0.08  # 8% per year delayed
                        delayed_benefit = estimated_benefit * (1 + delay_increase)
                        delayed_annual = delayed_benefit * 12
                        
                        content += f"\nCLAIMING SCENARIOS ANALYSIS:\n"
                        content += f"• Early Claiming (Age 62): ${early_benefit:,.0f}/month (${early_annual:,.0f}/year)\n"
                        content += f"  - Reduction: {early_reduction*100:.1f}%\n"
                        content += f"  - Lifetime starting 8 years earlier\n"
                        
                        content += f"• Full Retirement Age ({fra}): ${estimated_benefit:,.0f}/month (${fra_annual:,.0f}/year)\n"
                        content += f"  - Base benefit amount\n"
                        
                        content += f"• Delayed Claiming (Age 70): ${delayed_benefit:,.0f}/month (${delayed_annual:,.0f}/year)\n"
                        content += f"  - Increase: {delay_increase*100:.1f}%\n"
                        content += f"  - Delayed retirement credits applied\n"
                        
                        # Break-even analysis
                        breakeven_fra_vs_early = (estimated_benefit - early_benefit) * 12 / early_annual
                        if breakeven_fra_vs_early > 0:
                            breakeven_age_fra = 62 + breakeven_fra_vs_early
                            content += f"\n• Break-even Age (62 vs FRA): {breakeven_age_fra:.1f} years old\n"
                        
                        breakeven_delayed_vs_fra = (delayed_benefit - estimated_benefit) * 12 / fra_annual
                        if breakeven_delayed_vs_fra > 0:
                            breakeven_age_delayed = fra + breakeven_delayed_vs_fra
                            content += f"• Break-even Age (FRA vs 70): {breakeven_age_delayed:.1f} years old\n"
                        
                        # Optimization recommendation based on health/family history
                        content += f"\nOPTIMIZATION RECOMMENDATIONS:\n"
                        if claiming_age < fra:
                            content += f"• Current Strategy: Early claiming reduces lifetime benefit\n"
                            content += f"• Consider: Delaying to FRA increases monthly benefit by ${estimated_benefit - early_benefit:,.0f}\n"
                        elif claiming_age == fra:
                            content += f"• Current Strategy: Full benefit at FRA\n"
                            content += f"• Consider: Delaying to 70 increases monthly benefit by ${delayed_benefit - estimated_benefit:,.0f}\n"
                        else:
                            content += f"• Current Strategy: Maximizing benefit through delayed retirement credits\n"
                            content += f"• Optimal for longevity planning\n"
                    
                    # Spouse benefit analysis
                    if ss_benefit.spouse_benefit_eligible:
                        spouse_benefit = float(ss_benefit.spouse_benefit_amount or 0)
                        if spouse_benefit > 0:
                            content += f"\nSPOUSE BENEFIT ANALYSIS:\n"
                            content += f"• Spouse Benefit Amount: ${spouse_benefit:,.0f}/month\n"
                            content += f"• Annual Spouse Benefit: ${spouse_benefit * 12:,.0f}\n"
                            content += f"• Combined Household SS Income: ${(estimated_benefit + spouse_benefit) * 12:,.0f}/year\n"
                            
                            # File and suspend strategy (if applicable)
                            content += f"• Strategy: File and suspend options for maximizing household benefits\n"
            else:
                content += "SOCIAL SECURITY OPTIMIZATION:\n"
                content += "• No Social Security information available\n"
                content += "• Recommendation: Obtain Social Security statement from ssa.gov\n"
                content += "• Claiming strategy can significantly impact retirement income\n"
            
            # 401(k) Optimization Analysis
            employer_401k_benefits = [b for b in benefits if b.benefit_type in ['401k_match', 'employer_401k']]
            
            content += f"\n\n401(K) OPTIMIZATION ANALYSIS:\n"
            
            if employer_401k_benefits:
                for match_benefit in employer_401k_benefits:
                    match_percentage = float(match_benefit.employer_match_percentage or 0)
                    match_limit = float(match_benefit.employer_match_limit or 0)
                    
                    if match_percentage > 0:
                        content += f"• Employer Match: {match_percentage}% of salary\n"
                        if match_limit > 0:
                            content += f"• Maximum Match: ${match_limit:,.0f} annually\n"
                        
                        # Calculate optimization scenarios
                        if match_benefit.employer_401k_match_formula:
                            content += f"• Match Formula: {match_benefit.employer_401k_match_formula}\n"
                        
                        # Get current user income for optimization
                        user_data = self._build_user_financial_data(user_id, db)
                        if user_data:
                            annual_income = user_data.monthly_income * 12
                            
                            # Calculate required contribution to maximize match
                            if match_limit > 0:
                                max_contribution_for_match = min(match_limit / (match_percentage / 100), annual_income)
                                content += f"• Required Contribution for Full Match: ${max_contribution_for_match:,.0f} ({max_contribution_for_match/annual_income*100:.1f}% of income)\n"
                                content += f"• Free Money from Employer Match: ${min(match_limit, max_contribution_for_match * match_percentage / 100):,.0f}\n"
                            
                            # 2025 contribution limits
                            contribution_limit_2025 = 23000  # Standard limit
                            catchup_limit_2025 = 7500 if (profile.age or 35) >= 50 else 0
                            total_limit = contribution_limit_2025 + catchup_limit_2025
                            
                            content += f"• 2025 Contribution Limit: ${contribution_limit_2025:,.0f}\n"
                            if catchup_limit_2025 > 0:
                                content += f"• Age 50+ Catch-up: ${catchup_limit_2025:,.0f}\n"
                                content += f"• Total Available Limit: ${total_limit:,.0f}\n"
                            
                            # Optimization recommendations
                            content += f"\nOPTIMIZATION STRATEGY:\n"
                            content += f"• Priority 1: Contribute enough to get full employer match\n"
                            content += f"• Priority 2: Max out high-yield savings for emergency fund\n"
                            content += f"• Priority 3: Consider maxing 401(k) for tax savings\n"
                            content += f"• Priority 4: Roth IRA for tax diversification\n"
                        
                        # Vesting schedule information
                        if match_benefit.employer_401k_vesting_schedule:
                            content += f"• Vesting Schedule: {match_benefit.employer_401k_vesting_schedule}\n"
                            content += f"• Recommendation: Understand vesting before job changes\n"
            else:
                content += "• No 401(k) matching information available\n"
                content += "• Recommendation: Verify employer 401(k) benefits and matching\n"
            
            # Pension Optimization (if applicable)
            pension_benefits = [b for b in benefits if b.benefit_type == 'pension']
            
            if pension_benefits:
                content += f"\n\nPENSION OPTIMIZATION:\n"
                for pension in pension_benefits:
                    monthly_payout = float(pension.expected_monthly_payout or 0)
                    vested_pct = float(pension.vested_percentage or 0)
                    
                    content += f"• Expected Monthly Payout: ${monthly_payout:,.0f}\n"
                    content += f"• Vested Percentage: {vested_pct}%\n"
                    content += f"• Annual Pension Income: ${monthly_payout * 12:,.0f}\n"
                    
                    if pension.lump_sum_option:
                        content += f"• Lump Sum Option Available: Consider vs. monthly payments\n"
                        content += f"• Analysis needed: Present value vs. guaranteed income stream\n"
                    
                    if pension.pension_details and isinstance(pension.pension_details, dict):
                        content += f"• Additional Details:\n"
                        for key, value in pension.pension_details.items():
                            if value:
                                content += f"  - {key.replace('_', ' ').title()}: {value}\n"
            
            # Health Benefits Optimization
            health_benefits = [b for b in benefits if b.benefit_type in ['health_insurance', 'hsa']]
            
            if health_benefits:
                content += f"\n\nHEALTH BENEFITS OPTIMIZATION:\n"
                for health in health_benefits:
                    if health.health_insurance_premium:
                        annual_premium = float(health.health_insurance_premium)
                        content += f"• Health Insurance Premium: ${annual_premium:,.0f}/year\n"
                        content += f"• Monthly Premium: ${annual_premium/12:,.0f}\n"
                    
                    # HSA optimization if available
                    if health.other_benefits and isinstance(health.other_benefits, dict):
                        hsa_eligible = health.other_benefits.get('hsa_eligible')
                        if hsa_eligible:
                            content += f"• HSA Eligible: Triple tax advantage opportunity\n"
                            content += f"• 2025 HSA Limits: $4,300 individual, $8,550 family\n"
                            content += f"• HSA Strategy: Max contribution for retirement healthcare costs\n"
            
            # Store enhanced benefits document
            doc_id = f"user_{user_id}_benefits_enhanced"
            self.vector_store.add_document(
                doc_id=doc_id,
                content=content,
                metadata={
                    "user_id": user_id,
                    "document_type": "benefits_enhanced",
                    "has_social_security": len(social_security_benefits) > 0,
                    "has_401k_match": len(employer_401k_benefits) > 0,
                    "has_pension": len(pension_benefits) > 0,
                    "optimization_level": "advanced",
                    "version": "enhanced_v1.0"
                }
            )
            
            logger.info(f"Enhanced benefits optimization document created for user {user_id}")
            
        except Exception as e:
            logger.warning(f"Failed to sync enhanced benefits for user {user_id}: {str(e)}")
    
    def _sync_enhanced_tax_optimization(self, user_id: int, db: Session):
        """
        Create Enhanced Tax Optimization Vector Document with advanced tax strategies
        """
        try:
            from app.models.user_profile import UserProfile, UserTaxInfo
            
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if not profile:
                logger.warning(f"No profile found for user {user_id}")
                return
            
            tax_info = db.query(UserTaxInfo).filter(UserTaxInfo.profile_id == profile.id).first()
            
            # Get user financial data for tax optimization calculations
            user_data = self._build_user_financial_data(user_id, db)
            annual_income = user_data.monthly_income * 12 if user_data else 0
            
            # Build enhanced tax optimization content
            content = "ENHANCED TAX OPTIMIZATION STRATEGIES:\n"
            content += "="*60 + "\n\n"
            
            if tax_info:
                # Current tax situation analysis
                content += "CURRENT TAX SITUATION ANALYSIS:\n"
                content += f"• Tax Year: {tax_info.tax_year}\n"
                content += f"• Filing Status: {tax_info.filing_status or 'Not specified'}\n"
                content += f"• Federal Tax Bracket: {float(tax_info.federal_tax_bracket or 0):.0f}%\n"
                content += f"• Effective Tax Rate: {float(tax_info.effective_tax_rate or 0):.1f}%\n"
                content += f"• Marginal Tax Rate: {float(tax_info.marginal_tax_rate or 0):.1f}%\n"
                
                if tax_info.adjusted_gross_income:
                    agi = float(tax_info.adjusted_gross_income)
                    content += f"• Adjusted Gross Income: ${agi:,.0f}\n"
                    
                    # Tax bracket optimization analysis
                    content += f"\nTAX BRACKET OPTIMIZATION:\n"
                    
                    # 2025 tax brackets (married filing jointly example)
                    if tax_info.filing_status == 'married_filing_jointly':
                        tax_brackets_2025 = [
                            (23200, 0.10), (94300, 0.12), (201050, 0.22), 
                            (383900, 0.24), (487450, 0.32), (731200, 0.35), (float('inf'), 0.37)
                        ]
                    else:  # Single filer brackets
                        tax_brackets_2025 = [
                            (11600, 0.10), (47150, 0.12), (100525, 0.22), 
                            (191950, 0.24), (243725, 0.32), (609350, 0.35), (float('inf'), 0.37)
                        ]
                    
                    current_bracket = 0.22  # Default
                    next_bracket_threshold = 0
                    for threshold, rate in tax_brackets_2025:
                        if agi <= threshold:
                            current_bracket = rate
                            break
                        next_bracket_threshold = threshold
                    
                    content += f"• Current Marginal Bracket: {current_bracket*100:.0f}%\n"
                    if next_bracket_threshold > agi:
                        room_in_bracket = next_bracket_threshold - agi
                        content += f"• Room in Current Bracket: ${room_in_bracket:,.0f}\n"
                        content += f"• Strategy: Maximize deductions within current bracket\n"
                
                # Advanced tax strategy analysis
                content += f"\nADVANCED TAX STRATEGIES:\n"
                
                # 1. Backdoor Roth IRA Strategy
                backdoor_eligible = tax_info.backdoor_roth_eligible
                content += f"• Backdoor Roth IRA Eligible: {'Yes' if backdoor_eligible else 'No'}\n"
                if backdoor_eligible:
                    content += f"  - Strategy: Contribute $7,000 to non-deductible Traditional IRA\n"
                    content += f"  - Then convert to Roth IRA for tax-free growth\n"
                    content += f"  - Benefit: Bypass Roth IRA income limits\n"
                    
                    # Calculate tax savings
                    if annual_income > 0:
                        marginal_rate = float(tax_info.marginal_tax_rate or 22) / 100
                        roth_benefit = 7000 * marginal_rate * 20  # Assume 20 years of growth
                        content += f"  - Estimated 20-year tax savings: ${roth_benefit:,.0f}\n"
                
                # 2. Mega Backdoor Roth Strategy
                mega_backdoor_available = tax_info.mega_backdoor_roth_available
                content += f"• Mega Backdoor Roth Available: {'Yes' if mega_backdoor_available else 'No'}\n"
                if mega_backdoor_available:
                    content += f"  - Strategy: After-tax 401(k) contributions up to $70,000 total limit\n"
                    content += f"  - Convert after-tax contributions to Roth 401(k)\n"
                    content += f"  - Benefit: Massive Roth accumulation for high earners\n"
                
                # 3. Tax Loss Harvesting
                tax_loss_harvesting = tax_info.tax_loss_harvesting_enabled
                content += f"• Tax Loss Harvesting: {'Enabled' if tax_loss_harvesting else 'Disabled'}\n"
                if tax_loss_harvesting:
                    content += f"  - Strategy: Realize investment losses to offset gains\n"
                    content += f"  - Annual limit: $3,000 loss deduction against ordinary income\n"
                    content += f"  - Benefit: Reduce current year tax liability\n"
                    
                    # Estimate potential savings
                    if user_data and user_data.portfolio_value > 0:
                        portfolio_value = user_data.portfolio_value
                        potential_harvest = min(portfolio_value * 0.02, 3000)  # 2% of portfolio or $3k max
                        marginal_rate = float(tax_info.marginal_tax_rate or 22) / 100
                        annual_savings = potential_harvest * marginal_rate
                        content += f"  - Estimated annual tax savings: ${annual_savings:,.0f}\n"
                else:
                    content += f"  - Recommendation: Enable tax loss harvesting in investment accounts\n"
                
                # 4. Tax-Advantaged Account Optimization
                content += f"\nTAX-ADVANTAGED ACCOUNT OPTIMIZATION:\n"
                
                # Traditional vs Roth analysis
                current_bracket = float(tax_info.marginal_tax_rate or 22) / 100
                retirement_age = profile.retirement_age or 65
                current_age = profile.age or 35
                years_to_retirement = retirement_age - current_age
                
                content += f"• Traditional vs Roth Analysis:\n"
                content += f"  - Current Tax Bracket: {current_bracket*100:.0f}%\n"
                content += f"  - Years to Retirement: {years_to_retirement}\n"
                
                if current_bracket >= 0.22:  # 22% bracket or higher
                    content += f"  - Recommendation: Prioritize Traditional 401(k) for immediate deduction\n"
                    content += f"  - Benefit: ${23000 * current_bracket:,.0f} immediate tax savings (max contribution)\n"
                else:
                    content += f"  - Recommendation: Consider Roth 401(k) for tax-free retirement income\n"
                    content += f"  - Benefit: Tax-free growth over {years_to_retirement} years\n"
                
                # HSA Triple Tax Advantage
                content += f"\nHSA TRIPLE TAX ADVANTAGE STRATEGY:\n"
                hsa_contribution = float(tax_info.hsa_contribution or 0)
                max_hsa_2025 = 4300 if tax_info.filing_status != 'married_filing_jointly' else 8550
                
                content += f"• Current HSA Contribution: ${hsa_contribution:,.0f}\n"
                content += f"• 2025 HSA Limit: ${max_hsa_2025:,.0f}\n"
                
                if hsa_contribution < max_hsa_2025:
                    additional_hsa = max_hsa_2025 - hsa_contribution
                    tax_savings = additional_hsa * current_bracket
                    content += f"• Additional HSA Room: ${additional_hsa:,.0f}\n"
                    content += f"• Immediate Tax Savings: ${tax_savings:,.0f}\n"
                    content += f"• Strategy: Max HSA first - triple tax advantage\n"
                    content += f"  - Deductible contributions\n"
                    content += f"  - Tax-free growth\n"
                    content += f"  - Tax-free withdrawals for medical expenses\n"
                
                # 5. Charitable Giving Optimization
                charitable_giving = float(tax_info.charitable_giving_annual or 0)
                if charitable_giving > 0:
                    content += f"\nCHARITABLE GIVING OPTIMIZATION:\n"
                    content += f"• Annual Charitable Giving: ${charitable_giving:,.0f}\n"
                    content += f"• Tax Deduction Value: ${charitable_giving * current_bracket:,.0f}\n"
                    
                    # Donor-advised fund strategy
                    if charitable_giving >= 5000:
                        content += f"• Strategy: Donor-Advised Fund for appreciated assets\n"
                        content += f"• Benefit: Avoid capital gains tax + charitable deduction\n"
                        
                        # Bunching strategy
                        if tax_info.itemized_deductions:
                            itemized = float(tax_info.itemized_deductions)
                            standard_deduction_2025 = 15000 if tax_info.filing_status != 'married_filing_jointly' else 30000
                            if itemized < standard_deduction_2025 * 1.2:  # Close to standard deduction
                                content += f"• Bunching Strategy: Combine 2-3 years of giving in one year\n"
                                content += f"• Benefit: Exceed standard deduction threshold\n"
                
                # 6. Business Income Optimization
                if tax_info.business_income_details:
                    business_details = tax_info.business_income_details
                    if isinstance(business_details, dict) and any(business_details.values()):
                        content += f"\nBUSINESS INCOME OPTIMIZATION:\n"
                        
                        # Solo 401(k) strategy
                        content += f"• Solo 401(k) Strategy:\n"
                        content += f"  - Employee contribution limit: $23,000\n"
                        content += f"  - Employer contribution: 25% of net self-employment income\n"
                        content += f"  - Total limit: $70,000 (or $77,500 if 50+)\n"
                        
                        # SEP-IRA alternative
                        content += f"• SEP-IRA Alternative:\n"
                        content += f"  - Contribute 25% of net self-employment income\n"
                        content += f"  - Simpler administration than Solo 401(k)\n"
                        
                        # QBI Deduction (Section 199A)
                        content += f"• QBI Deduction (Section 199A):\n"
                        content += f"  - Up to 20% deduction on qualified business income\n"
                        content += f"  - Strategy: Optimize income levels to maximize deduction\n"
                
                # 7. Multi-Year Tax Planning
                content += f"\nMULTI-YEAR TAX PLANNING STRATEGIES:\n"
                
                # Roth conversion ladder
                if years_to_retirement > 10:
                    content += f"• Roth Conversion Ladder Strategy:\n"
                    content += f"  - Convert Traditional IRA to Roth in low-income years\n"
                    content += f"  - Target: Fill up lower tax brackets\n"
                    content += f"  - Benefit: Tax-free retirement income\n"
                
                # Tax location optimization
                content += f"• Tax Location Optimization:\n"
                content += f"  - Hold tax-inefficient investments in tax-advantaged accounts\n"
                content += f"  - Hold tax-efficient investments in taxable accounts\n"
                content += f"  - Municipal bonds in high tax bracket years\n"
                
                # Estate planning tax strategies
                if user_data and user_data.total_assets > 1000000:  # High net worth
                    content += f"• Estate Planning Tax Strategies:\n"
                    content += f"  - Annual gift tax exclusion: $18,000 per recipient (2025)\n"
                    content += f"  - Lifetime estate/gift tax exemption: $13.61M (2025)\n"
                    content += f"  - Strategy: Annual gifting to reduce estate tax\n"
                
                # Tax planning notes from user
                if tax_info.tax_strategy_notes:
                    content += f"\nCUSTOM TAX STRATEGY NOTES:\n"
                    content += f"{tax_info.tax_strategy_notes}\n"
                
                # Action items summary
                content += f"\nIMMEDIATE ACTION ITEMS:\n"
                action_items = []
                
                if backdoor_eligible:
                    action_items.append("• Execute Backdoor Roth IRA conversion")
                if hsa_contribution < max_hsa_2025:
                    action_items.append(f"• Increase HSA contribution by ${max_hsa_2025 - hsa_contribution:,.0f}")
                if not tax_loss_harvesting:
                    action_items.append("• Enable tax loss harvesting in investment accounts")
                if charitable_giving > 0 and not tax_info.tax_professional_name:
                    action_items.append("• Consider donor-advised fund for charitable giving")
                
                if action_items:
                    content += "\n".join(action_items)
                else:
                    content += "• Review current strategies - optimization appears comprehensive\n"
                    
            else:
                # No tax info available - provide general optimization framework
                content += "TAX OPTIMIZATION FRAMEWORK:\n"
                content += "• Complete tax information assessment for personalized strategies\n"
                content += "• Priority optimization areas to explore:\n"
                content += "  - Backdoor Roth IRA eligibility\n"
                content += "  - HSA maximization\n"
                content += "  - Tax loss harvesting\n"
                content += "  - 401(k) traditional vs Roth allocation\n"
                content += "  - Charitable giving optimization\n"
                content += "  - Business income tax strategies\n"
            
            # Store enhanced tax optimization document
            doc_id = f"user_{user_id}_tax_optimization"
            self.vector_store.add_document(
                doc_id=doc_id,
                content=content,
                metadata={
                    "user_id": user_id,
                    "document_type": "tax_optimization",
                    "has_tax_info": tax_info is not None,
                    "backdoor_roth_eligible": bool(tax_info and tax_info.backdoor_roth_eligible),
                    "tax_loss_harvesting": bool(tax_info and tax_info.tax_loss_harvesting_enabled),
                    "optimization_level": "advanced",
                    "version": "enhanced_v1.0"
                }
            )
            
            logger.info(f"Enhanced tax optimization document created for user {user_id}")
            
        except Exception as e:
            logger.warning(f"Failed to sync enhanced tax optimization for user {user_id}: {str(e)}")
    
    def get_user_context(self, user_id: int, query: str = "", limit: int = 3) -> str:
        """
        Get user context from vector store - this is the ONLY method chat should use
        
        Args:
            user_id: User ID
            query: Optional search query for relevant context
            limit: Number of documents to retrieve
            
        Returns:
            Formatted context string for LLM
        """
        try:
            context_parts = []
            
            # Always get the main financial document first using direct ID lookup
            main_doc_id = f"user_{user_id}_financial_complete"
            main_doc = self.vector_store.get_document(main_doc_id)
            
            if not main_doc:
                # Fallback: search by user_id in metadata
                for doc_id, doc in self.vector_store.documents.items():
                    if doc.metadata.get("user_id") == user_id and doc.metadata.get("document_type") == "financial_complete":
                        context_parts.append(doc.content)
                        break
                
                if not context_parts:
                    logger.warning(f"No vector data found for user {user_id}")
                    return f"No financial data available for user {user_id}. Please sync finances first."
            else:
                context_parts.append(main_doc.content)
            
            # ALWAYS include goals document (critical fix)
            goals_doc_id = f"user_{user_id}_goals"
            goals_doc = self.vector_store.get_document(goals_doc_id)
            if goals_doc:
                context_parts.append(goals_doc.content)
                logger.info(f"Goals document included for user {user_id}")
            else:
                logger.warning(f"No goals document found for user {user_id}")
            
            # ALWAYS include profile document for comprehensive context
            profile_doc_id = f"user_{user_id}_profile_complete"
            profile_doc = self.vector_store.get_document(profile_doc_id)
            if profile_doc:
                context_parts.append(profile_doc.content)
            
            # ALWAYS include enhanced benefits and tax document (critical for tax questions and Social Security optimization)
            benefits_tax_doc_id = f"user_{user_id}_benefits_tax_enhanced"
            benefits_tax_doc = self.vector_store.get_document(benefits_tax_doc_id)
            if benefits_tax_doc:
                context_parts.append(benefits_tax_doc.content)
                logger.info(f"Enhanced benefits/tax document included for user {user_id}")
            else:
                # Fallback to original benefits/tax document if enhanced version not available
                fallback_benefits_tax_doc_id = f"user_{user_id}_benefits_tax"
                fallback_benefits_tax_doc = self.vector_store.get_document(fallback_benefits_tax_doc_id)
                if fallback_benefits_tax_doc:
                    context_parts.append(fallback_benefits_tax_doc.content)
                    logger.info(f"Fallback benefits/tax document included for user {user_id}")
                else:
                    logger.warning(f"No benefits/tax document found for user {user_id}")
            
            # ALWAYS include insurance document (critical for insurance questions)
            insurance_doc_id = f"user_{user_id}_insurance"
            insurance_doc = self.vector_store.get_document(insurance_doc_id)
            if insurance_doc:
                context_parts.append(insurance_doc.content)
                logger.info(f"Insurance document included for user {user_id}")
            else:
                logger.warning(f"No insurance document found for user {user_id}")
            
            # ALWAYS include estate planning document (critical for estate planning questions)
            estate_planning_doc_id = f"user_{user_id}_estate_planning"
            estate_planning_doc = self.vector_store.get_document(estate_planning_doc_id)
            if estate_planning_doc:
                context_parts.append(estate_planning_doc.content)
                logger.info(f"Estate planning document included for user {user_id}")
            else:
                logger.warning(f"No estate planning document found for user {user_id}")
            
            # ALWAYS include investment preferences document (critical for investment advice)
            investment_prefs_doc_id = f"user_{user_id}_investment_preferences"
            investment_prefs_doc = self.vector_store.get_document(investment_prefs_doc_id)
            if investment_prefs_doc:
                context_parts.append(investment_prefs_doc.content)
                logger.info(f"Investment preferences document included for user {user_id}")
            else:
                logger.warning(f"No investment preferences document found for user {user_id}")
            
            # ALWAYS include enhanced benefits document (critical for Social Security and 401k optimization)
            enhanced_benefits_doc_id = f"user_{user_id}_benefits_enhanced"
            enhanced_benefits_doc = self.vector_store.get_document(enhanced_benefits_doc_id)
            if enhanced_benefits_doc:
                context_parts.append(enhanced_benefits_doc.content)
                logger.info(f"Enhanced benefits document included for user {user_id}")
            else:
                logger.warning(f"No enhanced benefits document found for user {user_id}")
            
            # ALWAYS include enhanced tax optimization document (critical for tax strategy advice)
            enhanced_tax_doc_id = f"user_{user_id}_tax_optimization"
            enhanced_tax_doc = self.vector_store.get_document(enhanced_tax_doc_id)
            if enhanced_tax_doc:
                context_parts.append(enhanced_tax_doc.content)
                logger.info(f"Enhanced tax optimization document included for user {user_id}")
            else:
                logger.warning(f"No enhanced tax optimization document found for user {user_id}")
            
            # Add query-specific additional context if provided (SECURE USER-ONLY SEARCH)
            if query:
                additional_results = self.vector_store.search_user_only(query=query, user_id=user_id, limit=limit)
                for doc_id, score, document in additional_results:
                    # search_user_only already filters by user_id, so all results are safe
                    # Avoid duplicating documents we already included
                    content = document.content
                    if content not in context_parts:
                        context_parts.append(content)
                        logger.info(f"Added query-specific context for user {user_id} (doc: {doc_id[:50]}...)")
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Failed to get user context: {str(e)}")
            return "Error retrieving user financial context"
    
    def trigger_sync_on_change(self, user_id: int, db: Session, change_type: str = "manual"):
        """
        Trigger sync when data changes (called from financial endpoints)
        
        Args:
            user_id: User ID to sync
            db: Database session  
            change_type: Type of change (manual, transaction, goal, etc.)
        """
        logger.info(f"Triggering vector sync for user {user_id} due to {change_type} change")
        return self.sync_user_data(user_id, db)


# Singleton instance
vector_sync_service = VectorSyncService()


def get_vector_sync_service() -> VectorSyncService:
    """Get the vector sync service singleton"""
    return vector_sync_service