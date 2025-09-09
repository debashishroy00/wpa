from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.services.snapshot_service import SnapshotService
from app.schemas.snapshot import SnapshotResponse, SnapshotCreate, TimelineData
from datetime import datetime, date

router = APIRouter(tags=["snapshots"])
snapshot_service = SnapshotService()


@router.post("/", response_model=SnapshotResponse)
async def create_snapshot(
    snapshot_data: SnapshotCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new financial snapshot"""
    # Check if last snapshot was recent (within 30 days)
    last_snapshot_date = snapshot_service.get_last_snapshot_date(db, current_user.id)
    if last_snapshot_date:
        days_since_last = (date.today() - last_snapshot_date).days
        if days_since_last < 30:
            raise HTTPException(
                status_code=400,
                detail=f"Last snapshot was {days_since_last} days ago. Wait at least 30 days between snapshots."
            )
    
    try:
        snapshot = snapshot_service.create_snapshot(db, current_user.id, snapshot_data.name)
        return snapshot
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[SnapshotResponse])
async def get_snapshots(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's snapshots"""
    return snapshot_service.get_snapshots(db, current_user.id, limit)


@router.get("/timeline", response_model=TimelineData)
async def get_timeline(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get timeline data for charts"""
    return snapshot_service.get_timeline_data(db, current_user.id)


@router.delete("/{snapshot_id}")
async def delete_snapshot(
    snapshot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a snapshot"""
    success = snapshot_service.delete_snapshot(db, snapshot_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return {"message": "Snapshot deleted successfully"}


@router.get("/last-date")
async def get_last_snapshot_date(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check when last snapshot was taken"""
    last_date = snapshot_service.get_last_snapshot_date(db, current_user.id)
    return {
        "last_snapshot_date": last_date.isoformat() if last_date else None,
        "days_since_last": (date.today() - last_date).days if last_date else None,
        "can_create_new": not last_date or (date.today() - last_date).days >= 30
    }