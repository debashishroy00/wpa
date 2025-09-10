from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.models.snapshot import FinancialSnapshot, SnapshotEntry, SnapshotGoal
from app.models.financial import FinancialEntry
from app.models.goal import FinancialGoal
from app.models.user import User


class SnapshotService:
    """Service for managing financial snapshots"""

    def create_snapshot(self, db: Session, user_id: int, name: Optional[str] = None) -> FinancialSnapshot:
        """Create a snapshot of current financial state"""
        # Get user for context
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        # Calculate summary metrics
        financial_summary = self._calculate_financial_summary(db, user_id)
        
        # Generate snapshot name if not provided
        if not name:
            name = f"Snapshot {date.today().strftime('%B %Y')}"

        # Create snapshot record
        snapshot = FinancialSnapshot(
            user_id=user_id,
            snapshot_name=name,
            net_worth=financial_summary.get('net_worth', 0),
            total_assets=financial_summary.get('total_assets', 0),
            total_liabilities=financial_summary.get('total_liabilities', 0),
            monthly_income=financial_summary.get('monthly_income', 0),
            monthly_expenses=financial_summary.get('monthly_expenses', 0),
            savings_rate=financial_summary.get('savings_rate', 0),
            age=self._calculate_age(user.profile.date_of_birth) if user.profile and user.profile.date_of_birth else None,
            employment_status=getattr(user.profile, 'occupation', None) if user.profile else "Not specified"
        )
        
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)

        # Copy current financial entries
        self._copy_financial_entries(db, user_id, snapshot.id)
        
        # Copy goal progress
        self._copy_goal_progress(db, user_id, snapshot.id)
        
        return snapshot

    def get_snapshots(self, db: Session, user_id: int, limit: int = 20) -> List[FinancialSnapshot]:
        """Get user's snapshots ordered by date"""
        return db.query(FinancialSnapshot)\
            .filter(FinancialSnapshot.user_id == user_id)\
            .order_by(desc(FinancialSnapshot.snapshot_date))\
            .limit(limit)\
            .all()

    def get_timeline_data(self, db: Session, user_id: int) -> Dict[str, List]:
        """Get data formatted for timeline chart"""
        snapshots = db.query(FinancialSnapshot)\
            .filter(FinancialSnapshot.user_id == user_id)\
            .order_by(FinancialSnapshot.snapshot_date)\
            .all()

        return {
            'dates': [s.snapshot_date.isoformat() for s in snapshots],
            'net_worth': [float(s.net_worth or 0) for s in snapshots],
            'assets': [float(s.total_assets or 0) for s in snapshots],
            'liabilities': [float(s.total_liabilities or 0) for s in snapshots]
        }

    def delete_snapshot(self, db: Session, snapshot_id: int, user_id: int) -> bool:
        """Delete a snapshot (with cascade)"""
        snapshot = db.query(FinancialSnapshot)\
            .filter(FinancialSnapshot.id == snapshot_id, FinancialSnapshot.user_id == user_id)\
            .first()
        
        if not snapshot:
            return False
            
        db.delete(snapshot)
        db.commit()
        return True

    def get_last_snapshot_date(self, db: Session, user_id: int) -> Optional[date]:
        """Check when last snapshot was taken"""
        last_snapshot = db.query(FinancialSnapshot)\
            .filter(FinancialSnapshot.user_id == user_id)\
            .order_by(desc(FinancialSnapshot.created_at))\
            .first()
        
        return last_snapshot.snapshot_date if last_snapshot else None

    def _calculate_financial_summary(self, db: Session, user_id: int) -> Dict[str, float]:
        """Calculate financial metrics from current active entries only"""
        entries = db.query(FinancialEntry)\
            .filter(FinancialEntry.user_id == user_id)\
            .filter(FinancialEntry.is_active == True)\
            .all()

        assets = sum(float(e.amount) for e in entries if e.category.value == 'assets')
        liabilities = sum(float(e.amount) for e in entries if e.category.value == 'liabilities')
        income = sum(float(e.amount) for e in entries if e.category.value == 'income')
        expenses = sum(float(e.amount) for e in entries if e.category.value == 'expenses')
        
        net_worth = assets - liabilities
        savings_rate = ((income - expenses) / income * 100) if income > 0 else 0

        return {
            'net_worth': net_worth,
            'total_assets': assets,
            'total_liabilities': liabilities,
            'monthly_income': income,
            'monthly_expenses': expenses,
            'savings_rate': savings_rate
        }

    def _copy_financial_entries(self, db: Session, user_id: int, snapshot_id: int):
        """Copy current active financial entries to snapshot"""
        entries = db.query(FinancialEntry)\
            .filter(FinancialEntry.user_id == user_id)\
            .filter(FinancialEntry.is_active == True)\
            .all()

        for entry in entries:
            snapshot_entry = SnapshotEntry(
                snapshot_id=snapshot_id,
                category=entry.category.value,
                subcategory=entry.subcategory,
                name=entry.description,  # Use description field
                institution=getattr(entry, 'institution', None),
                account_type=getattr(entry, 'account_type', None),
                amount=entry.amount,
                interest_rate=getattr(entry, 'interest_rate', None)
            )
            db.add(snapshot_entry)
        
        db.commit()

    def _copy_goal_progress(self, db: Session, user_id: int, snapshot_id: int):
        """Copy current goal progress to snapshot"""
        goals = db.query(FinancialGoal)\
            .filter(FinancialGoal.user_id == user_id)\
            .all()

        for goal in goals:
            completion = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
            
            snapshot_goal = SnapshotGoal(
                snapshot_id=snapshot_id,
                goal_name=goal.name,
                target_amount=goal.target_amount,
                current_amount=goal.current_amount,
                target_date=goal.target_date,
                completion_percentage=completion
            )
            db.add(snapshot_goal)
        
        db.commit()

    def _calculate_age(self, birth_date: date) -> int:
        """Calculate age from birth date"""
        today = date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))