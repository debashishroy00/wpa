"""
Financial Snapshots API - Persistent storage implementation
"""
from typing import List, Optional
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, desc, func, extract
from app.db.session import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.services.snapshot_service import SnapshotService
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["snapshots"])


# Test endpoint removed - snapshots functionality is working properly


@router.get("/detailed")
async def get_detailed_snapshots(
    limit: int = 4,
    period: Optional[str] = Query(None, description="Filter by period: monthly, quarterly, yearly"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed snapshots with categorized entries for trending table"""
    try:
        from app.models.snapshot import FinancialSnapshot, SnapshotEntry
        
        snapshot_service = SnapshotService()
        snapshots = snapshot_service.get_snapshots(db, current_user.id, 50)
        
        # Apply period filtering if specified
        if period and snapshots:
            filtered_snapshots = []
            if period == "monthly":
                seen_months = set()
                for snapshot in snapshots:
                    month_key = (snapshot.snapshot_date.year, snapshot.snapshot_date.month)
                    if month_key not in seen_months:
                        filtered_snapshots.append(snapshot)
                        seen_months.add(month_key)
            elif period == "quarterly":
                seen_quarters = set()
                for snapshot in snapshots:
                    quarter = ((snapshot.snapshot_date.month - 1) // 3) + 1
                    quarter_key = (snapshot.snapshot_date.year, quarter)
                    if quarter_key not in seen_quarters:
                        filtered_snapshots.append(snapshot)
                        seen_quarters.add(quarter_key)
            elif period == "yearly":
                seen_years = set()
                for snapshot in snapshots:
                    if snapshot.snapshot_date.year not in seen_years:
                        filtered_snapshots.append(snapshot)
                        seen_years.add(snapshot.snapshot_date.year)
            snapshots = filtered_snapshots
        
        # Get last N snapshots
        last_snapshots = snapshots[-limit:] if len(snapshots) >= limit else snapshots
        
        result = []
        for snapshot in last_snapshots:
            # Get entries for this snapshot
            entries = db.query(SnapshotEntry)\
                .filter(SnapshotEntry.snapshot_id == snapshot.id)\
                .all()
            
            # Categorize entries
            categorized = {
                'real_estate': 0,
                'investments': 0,
                'cash': 0,
                'other_assets': 0,
                'mortgages': 0,
                'other_debt': 0,
                'income': 0,
                'expenses': 0
            }
            
            for entry in entries:
                amount = float(entry.amount or 0)
                category = entry.category.lower()
                subcategory = (entry.subcategory or '').lower()
                
                if category == 'assets':
                    if 'real' in subcategory or 'property' in subcategory or 'estate' in subcategory:
                        categorized['real_estate'] += amount
                    elif 'investment' in subcategory or 'stock' in subcategory or 'bond' in subcategory or '401k' in subcategory or 'ira' in subcategory:
                        categorized['investments'] += amount
                    elif 'cash' in subcategory or 'checking' in subcategory or 'savings' in subcategory:
                        categorized['cash'] += amount
                    else:
                        categorized['other_assets'] += amount
                elif category == 'liabilities':
                    if 'mortgage' in subcategory or 'home' in subcategory:
                        categorized['mortgages'] += amount
                    else:
                        categorized['other_debt'] += amount
                elif category == 'income':
                    categorized['income'] += amount
                elif category == 'expenses':
                    categorized['expenses'] += amount
            
            result.append({
                "id": snapshot.id,
                "snapshot_date": snapshot.snapshot_date.isoformat(),
                "snapshot_name": snapshot.snapshot_name,
                "net_worth": float(snapshot.net_worth or 0),
                "total_assets": float(snapshot.total_assets or 0),
                "total_liabilities": float(snapshot.total_liabilities or 0),
                "monthly_income": float(snapshot.monthly_income or 0),
                "monthly_expenses": float(snapshot.monthly_expenses or 0),
                "categorized": categorized
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch detailed snapshots: {str(e)}")


@router.post("/")
async def create_snapshot(
    name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a financial snapshot with persistent storage"""
    try:
        # Try to use the persistent service first
        snapshot_service = SnapshotService()
        snapshot = snapshot_service.create_snapshot(db, current_user.id, name)
        
        return {
            "id": snapshot.id,
            "user_id": snapshot.user_id,
            "snapshot_name": snapshot.snapshot_name,
            "snapshot_date": snapshot.snapshot_date.isoformat(),
            "net_worth": float(snapshot.net_worth or 0),
            "total_assets": float(snapshot.total_assets or 0),
            "total_liabilities": float(snapshot.total_liabilities or 0),
            "monthly_income": float(snapshot.monthly_income or 0),
            "monthly_expenses": float(snapshot.monthly_expenses or 0),
            "savings_rate": float(snapshot.savings_rate or 0),
            "created_at": snapshot.created_at.isoformat(),
            "entries": [],
            "goals": []
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create snapshot: {str(e)}")


@router.get("/", response_model=List[dict])
async def get_snapshots(
    limit: int = 20,
    period: Optional[str] = Query(None, description="Filter by period: monthly, quarterly, yearly"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's financial snapshots with optional timeline filtering"""
    try:
        snapshot_service = SnapshotService()
        snapshots = snapshot_service.get_snapshots(db, current_user.id, limit)
        
        # Apply period filtering if specified
        if period and snapshots:
            filtered_snapshots = []
            if period == "monthly":
                # Keep one snapshot per month
                seen_months = set()
                for snapshot in snapshots:
                    month_key = (snapshot.snapshot_date.year, snapshot.snapshot_date.month)
                    if month_key not in seen_months:
                        filtered_snapshots.append(snapshot)
                        seen_months.add(month_key)
            elif period == "quarterly":
                # Keep one snapshot per quarter
                seen_quarters = set()
                for snapshot in snapshots:
                    quarter = ((snapshot.snapshot_date.month - 1) // 3) + 1
                    quarter_key = (snapshot.snapshot_date.year, quarter)
                    if quarter_key not in seen_quarters:
                        filtered_snapshots.append(snapshot)
                        seen_quarters.add(quarter_key)
            elif period == "yearly":
                # Keep one snapshot per year
                seen_years = set()
                for snapshot in snapshots:
                    if snapshot.snapshot_date.year not in seen_years:
                        filtered_snapshots.append(snapshot)
                        seen_years.add(snapshot.snapshot_date.year)
            snapshots = filtered_snapshots
        
        # Convert to response format
        return [
            {
                "id": snapshot.id,
                "user_id": snapshot.user_id,
                "snapshot_name": snapshot.snapshot_name,
                "snapshot_date": snapshot.snapshot_date.isoformat(),
                "net_worth": float(snapshot.net_worth or 0),
                "total_assets": float(snapshot.total_assets or 0),
                "total_liabilities": float(snapshot.total_liabilities or 0),
                "monthly_income": float(snapshot.monthly_income or 0),
                "monthly_expenses": float(snapshot.monthly_expenses or 0),
                "savings_rate": float(snapshot.savings_rate or 0),
                "created_at": snapshot.created_at.isoformat(),
                "entries": [],  # TODO: Add entries if needed
                "goals": []     # TODO: Add goals if needed
            }
            for snapshot in snapshots
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch snapshots: {str(e)}")


@router.get("/timeline")
async def get_timeline(
    period: Optional[str] = Query(None, description="Filter by period: monthly, quarterly, yearly"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get timeline data for charts with period filtering"""
    try:
        snapshot_service = SnapshotService()
        timeline_data = snapshot_service.get_timeline_data(db, current_user.id)
        
        # If we have data and period filtering is requested, apply it
        if period and timeline_data['dates']:
            snapshots = snapshot_service.get_snapshots(db, current_user.id, 100)  # Get more for filtering
            filtered_snapshots = []
            
            if period == "monthly":
                seen_months = set()
                for snapshot in snapshots:
                    month_key = (snapshot.snapshot_date.year, snapshot.snapshot_date.month)
                    if month_key not in seen_months:
                        filtered_snapshots.append(snapshot)
                        seen_months.add(month_key)
            elif period == "quarterly":
                seen_quarters = set()
                for snapshot in snapshots:
                    quarter = ((snapshot.snapshot_date.month - 1) // 3) + 1
                    quarter_key = (snapshot.snapshot_date.year, quarter)
                    if quarter_key not in seen_quarters:
                        filtered_snapshots.append(snapshot)
                        seen_quarters.add(quarter_key)
            elif period == "yearly":
                seen_years = set()
                for snapshot in snapshots:
                    if snapshot.snapshot_date.year not in seen_years:
                        filtered_snapshots.append(snapshot)
                        seen_years.add(snapshot.snapshot_date.year)
            
            # Rebuild timeline data from filtered snapshots
            filtered_snapshots.sort(key=lambda x: x.snapshot_date)
            timeline_data = {
                'dates': [s.snapshot_date.isoformat() for s in filtered_snapshots],
                'net_worth': [float(s.net_worth or 0) for s in filtered_snapshots],
                'assets': [float(s.total_assets or 0) for s in filtered_snapshots],
                'liabilities': [float(s.total_liabilities or 0) for s in filtered_snapshots],
                'labels': [s.snapshot_name for s in filtered_snapshots]
            }
        
        return timeline_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch timeline data: {str(e)}")


@router.get("/last-date")
async def get_last_snapshot_date(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check when last snapshot was taken"""
    try:
        snapshot_service = SnapshotService()
        last_date = snapshot_service.get_last_snapshot_date(db, current_user.id)
        
        if last_date:
            days_since = (date.today() - last_date).days
            return {
                "last_snapshot_date": last_date.isoformat(),
                "days_since_last": days_since,
                "can_create_new": True  # No restrictions - allow unlimited snapshots
            }
        else:
            return {
                "last_snapshot_date": None,
                "days_since_last": None,
                "can_create_new": True
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch last snapshot date: {str(e)}")


@router.delete("/{snapshot_id}")
async def delete_snapshot(
    snapshot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a snapshot"""
    try:
        snapshot_service = SnapshotService()
        success = snapshot_service.delete_snapshot(db, snapshot_id, current_user.id)
        
        if success:
            return {"message": "Snapshot deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Snapshot not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))