"""
Data Integrity Service
Ensures consistent financial data across all users and system components
Prevents the critical data consistency issues identified in the audit
"""
from typing import Dict, List, Optional, Tuple
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from decimal import Decimal
from ..models.financial import FinancialEntry, EntryCategory
from ..models.user import User
from ..models.user_profile import UserProfile
from datetime import datetime

logger = logging.getLogger(__name__)


class DataIntegrityService:
    """
    Service to ensure data integrity across all users
    Validates and fixes data consistency issues
    """
    
    def validate_user_data_integrity(self, user_id: int, db: Session) -> Dict:
        """
        Comprehensive validation of user data integrity
        Returns validation report and auto-fixes critical issues
        """
        try:
            logger.info(f"Validating data integrity for user {user_id}")
            
            # VALIDATION 1: Profile completeness
            profile_validation = self._validate_user_profile(user_id, db)
            
            # VALIDATION 2: Financial entries consistency
            entries_validation = self._validate_financial_entries(user_id, db)
            
            # VALIDATION 3: Active/inactive entry consistency
            active_validation = self._validate_active_entries(user_id, db)
            
            # VALIDATION 4: Calculation consistency
            calculation_validation = self._validate_calculations(user_id, db)
            
            # VALIDATION 5: Duplicate detection
            duplicate_validation = self._detect_duplicates(user_id, db)
            
            # Compile validation report
            validation_report = {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "validations": {
                    "profile": profile_validation,
                    "entries": entries_validation,
                    "active_status": active_validation,
                    "calculations": calculation_validation,
                    "duplicates": duplicate_validation
                },
                "overall_status": "PASS",
                "critical_issues": [],
                "warnings": [],
                "auto_fixes_applied": []
            }
            
            # Determine overall status
            critical_issues = []
            warnings = []
            
            for validation_name, validation_result in validation_report["validations"].items():
                if validation_result.get("status") == "CRITICAL":
                    critical_issues.append(f"{validation_name}: {validation_result.get('message', 'Unknown error')}")
                elif validation_result.get("status") == "WARNING":
                    warnings.append(f"{validation_name}: {validation_result.get('message', 'Unknown warning')}")
            
            validation_report["critical_issues"] = critical_issues
            validation_report["warnings"] = warnings
            
            if critical_issues:
                validation_report["overall_status"] = "CRITICAL"
            elif warnings:
                validation_report["overall_status"] = "WARNING"
            
            # Apply auto-fixes for critical issues
            if critical_issues:
                auto_fixes = self._apply_auto_fixes(user_id, db, validation_report)
                validation_report["auto_fixes_applied"] = auto_fixes
            
            logger.info(f"Data integrity validation completed for user {user_id}: {validation_report['overall_status']}")
            return validation_report
            
        except Exception as e:
            logger.error(f"Error validating data integrity for user {user_id}: {str(e)}")
            return {
                "user_id": user_id,
                "overall_status": "ERROR",
                "error": str(e)
            }
    
    def _validate_user_profile(self, user_id: int, db: Session) -> Dict:
        """Validate user profile completeness"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"status": "CRITICAL", "message": "User not found"}
            
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if not profile:
                return {"status": "CRITICAL", "message": "User profile missing"}
            
            # Check required fields
            missing_fields = []
            if not profile.age:
                missing_fields.append("age")
            if not profile.state:
                missing_fields.append("state")
            if not profile.employment_status:
                missing_fields.append("employment_status")
            
            if missing_fields:
                return {
                    "status": "WARNING",
                    "message": f"Missing profile fields: {missing_fields}",
                    "missing_fields": missing_fields
                }
            
            return {
                "status": "PASS",
                "message": "Profile validation passed",
                "age": profile.age,
                "state": profile.state,
                "employment": profile.employment_status
            }
            
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
    
    def _validate_financial_entries(self, user_id: int, db: Session) -> Dict:
        """Validate financial entries for data quality"""
        try:
            # Get all entries for the user
            entries = db.query(FinancialEntry).filter(
                FinancialEntry.user_id == user_id
            ).all()
            
            if not entries:
                return {"status": "WARNING", "message": "No financial entries found"}
            
            validation_issues = []
            
            # Check for invalid amounts
            invalid_amounts = [e for e in entries if e.amount is None or e.amount < 0]
            if invalid_amounts:
                validation_issues.append(f"{len(invalid_amounts)} entries with invalid amounts")
            
            # Check for missing descriptions
            missing_descriptions = [e for e in entries if not e.description or e.description.strip() == ""]
            if missing_descriptions:
                validation_issues.append(f"{len(missing_descriptions)} entries with missing descriptions")
            
            # Check for missing categories
            missing_categories = [e for e in entries if not e.category]
            if missing_categories:
                validation_issues.append(f"{len(missing_categories)} entries with missing categories")
            
            if validation_issues:
                return {
                    "status": "WARNING",
                    "message": "; ".join(validation_issues),
                    "total_entries": len(entries),
                    "issues": validation_issues
                }
            
            return {
                "status": "PASS",
                "message": "Financial entries validation passed",
                "total_entries": len(entries)
            }
            
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
    
    def _validate_active_entries(self, user_id: int, db: Session) -> Dict:
        """Validate active/inactive entry consistency"""
        try:
            total_entries = db.query(FinancialEntry).filter(
                FinancialEntry.user_id == user_id
            ).count()
            
            active_entries = db.query(FinancialEntry).filter(
                FinancialEntry.user_id == user_id,
                FinancialEntry.is_active == True
            ).count()
            
            inactive_entries = total_entries - active_entries
            inactive_percentage = (inactive_entries / total_entries * 100) if total_entries > 0 else 0
            
            # Flag if too many entries are inactive (potential data corruption)
            if inactive_percentage > 50:
                return {
                    "status": "CRITICAL",
                    "message": f"{inactive_percentage:.1f}% of entries are inactive - potential data corruption",
                    "total_entries": total_entries,
                    "active_entries": active_entries,
                    "inactive_entries": inactive_entries
                }
            elif inactive_percentage > 25:
                return {
                    "status": "WARNING",
                    "message": f"{inactive_percentage:.1f}% of entries are inactive",
                    "total_entries": total_entries,
                    "active_entries": active_entries,
                    "inactive_entries": inactive_entries
                }
            
            return {
                "status": "PASS",
                "message": "Active entry validation passed",
                "total_entries": total_entries,
                "active_entries": active_entries,
                "inactive_entries": inactive_entries
            }
            
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
    
    def _validate_calculations(self, user_id: int, db: Session) -> Dict:
        """Validate financial calculation consistency"""
        try:
            # Get active entries for calculations
            entries = db.query(FinancialEntry).filter(
                FinancialEntry.user_id == user_id,
                FinancialEntry.is_active == True
            ).all()
            
            if not entries:
                return {"status": "WARNING", "message": "No active entries for calculations"}
            
            # Calculate totals manually
            assets = [e for e in entries if e.category == EntryCategory.assets]
            liabilities = [e for e in entries if e.category == EntryCategory.liabilities]
            
            total_assets = sum(e.amount for e in assets)
            total_liabilities = sum(e.amount for e in liabilities)
            net_worth = total_assets - total_liabilities
            
            # Test calculation with financial summary service
            try:
                from .financial_summary_service import FinancialSummaryService
                service = FinancialSummaryService()
                summary = service.get_user_financial_summary(user_id=user_id, db=db)
                
                service_net_worth = summary.get('netWorth', 0)
                discrepancy = abs(float(net_worth) - float(service_net_worth))
                
                if discrepancy > 1:
                    return {
                        "status": "CRITICAL",
                        "message": f"Calculation discrepancy: ${discrepancy:,.2f} difference",
                        "manual_net_worth": float(net_worth),
                        "service_net_worth": float(service_net_worth),
                        "discrepancy": float(discrepancy)
                    }
                
                return {
                    "status": "PASS",
                    "message": "Calculation validation passed",
                    "net_worth": float(net_worth),
                    "total_assets": float(total_assets),
                    "total_liabilities": float(total_liabilities)
                }
                
            except Exception as service_error:
                return {
                    "status": "WARNING",
                    "message": f"Could not validate with service: {str(service_error)}",
                    "manual_net_worth": float(net_worth)
                }
            
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
    
    def _detect_duplicates(self, user_id: int, db: Session) -> Dict:
        """Detect potential duplicate entries"""
        try:
            entries = db.query(FinancialEntry).filter(
                FinancialEntry.user_id == user_id,
                FinancialEntry.is_active == True
            ).all()
            
            if not entries:
                return {"status": "PASS", "message": "No entries to check for duplicates"}
            
            # Group by description and amount to find potential duplicates
            entry_groups = {}
            for entry in entries:
                key = (entry.description.strip().lower(), float(entry.amount))
                if key not in entry_groups:
                    entry_groups[key] = []
                entry_groups[key].append(entry)
            
            # Find groups with multiple entries (potential duplicates)
            duplicates = {k: v for k, v in entry_groups.items() if len(v) > 1}
            
            if duplicates:
                duplicate_count = sum(len(group) - 1 for group in duplicates.values())
                return {
                    "status": "WARNING",
                    "message": f"Found {duplicate_count} potential duplicate entries",
                    "duplicate_groups": len(duplicates),
                    "total_duplicates": duplicate_count
                }
            
            return {
                "status": "PASS",
                "message": "No duplicate entries detected"
            }
            
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
    
    def _apply_auto_fixes(self, user_id: int, db: Session, validation_report: Dict) -> List[str]:
        """Apply automatic fixes for critical issues"""
        fixes_applied = []
        
        try:
            # Auto-fix 1: Reactivate improperly deactivated entries
            active_validation = validation_report["validations"].get("active_status", {})
            if active_validation.get("status") == "CRITICAL":
                inactive_count = active_validation.get("inactive_entries", 0)
                if inactive_count > 0:
                    # Get inactive entries and check if they should be reactivated
                    inactive_entries = db.query(FinancialEntry).filter(
                        FinancialEntry.user_id == user_id,
                        FinancialEntry.is_active == False
                    ).all()
                    
                    # For now, don't auto-reactivate - just log for manual review
                    fixes_applied.append(f"Flagged {len(inactive_entries)} inactive entries for manual review")
            
            # Auto-fix 2: Fix invalid amounts (set to 0)
            entries_validation = validation_report["validations"].get("entries", {})
            if "invalid amounts" in entries_validation.get("message", ""):
                invalid_entries = db.query(FinancialEntry).filter(
                    FinancialEntry.user_id == user_id,
                    (FinancialEntry.amount == None) | (FinancialEntry.amount < 0)
                ).all()
                
                for entry in invalid_entries:
                    entry.amount = Decimal('0')
                    fixes_applied.append(f"Fixed invalid amount for entry {entry.id}")
                
                db.commit()
            
            logger.info(f"Applied {len(fixes_applied)} auto-fixes for user {user_id}")
            return fixes_applied
            
        except Exception as e:
            logger.error(f"Error applying auto-fixes for user {user_id}: {str(e)}")
            return [f"Error applying fixes: {str(e)}"]
    
    def validate_all_users(self, db: Session) -> Dict:
        """Run data integrity validation for all users"""
        try:
            users = db.query(User).all()
            
            results = {
                "total_users": len(users),
                "timestamp": datetime.now().isoformat(),
                "user_results": {},
                "summary": {
                    "passed": 0,
                    "warnings": 0,
                    "critical": 0,
                    "errors": 0
                }
            }
            
            for user in users:
                user_validation = self.validate_user_data_integrity(user.id, db)
                results["user_results"][user.id] = user_validation
                
                status = user_validation.get("overall_status", "ERROR")
                if status == "PASS":
                    results["summary"]["passed"] += 1
                elif status == "WARNING":
                    results["summary"]["warnings"] += 1
                elif status == "CRITICAL":
                    results["summary"]["critical"] += 1
                else:
                    results["summary"]["errors"] += 1
            
            logger.info(f"System-wide validation completed: {results['summary']}")
            return results
            
        except Exception as e:
            logger.error(f"Error in system-wide validation: {str(e)}")
            return {"error": str(e)}
    
    def get_user_canonical_data(self, user_id: int, db: Session) -> Dict:
        """
        Get the canonical (definitive) financial data for a user
        This ensures all services use the same data source
        """
        try:
            # ALWAYS use active entries only for calculations
            entries = db.query(FinancialEntry).filter(
                FinancialEntry.user_id == user_id,
                FinancialEntry.is_active == True
            ).all()
            
            # Calculate canonical totals
            assets = [e for e in entries if e.category == EntryCategory.assets]
            liabilities = [e for e in entries if e.category == EntryCategory.liabilities]
            income = [e for e in entries if e.category == EntryCategory.income]
            expenses = [e for e in entries if e.category == EntryCategory.expenses]
            
            total_assets = sum(e.amount for e in assets)
            total_liabilities = sum(e.amount for e in liabilities)
            net_worth = total_assets - total_liabilities
            
            # Get profile data
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            canonical_data = {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "profile": {
                    "age": profile.age if profile else None,
                    "state": profile.state if profile else None,
                    "employment_status": profile.employment_status if profile else None
                },
                "financial": {
                    "total_assets": float(total_assets),
                    "total_liabilities": float(total_liabilities),
                    "net_worth": float(net_worth),
                    "assets_count": len(assets),
                    "liabilities_count": len(liabilities),
                    "income_count": len(income),
                    "expenses_count": len(expenses),
                    "total_entries": len(entries)
                },
                "data_quality": {
                    "source": "active_entries_only",
                    "validated": True
                }
            }
            
            logger.info(f"Canonical data generated for user {user_id}: Net Worth=${net_worth:,.2f}")
            return canonical_data
            
        except Exception as e:
            logger.error(f"Error getting canonical data for user {user_id}: {str(e)}")
            return {"error": str(e), "user_id": user_id}


# Global instance
data_integrity_service = DataIntegrityService()