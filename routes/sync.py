# routes/sync.py
from typing import Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from utils.auth import get_current_user
from utils.offline_sync import process_offline_data
from pydantic import BaseModel, Field

router = APIRouter()


class OfflineData(BaseModel):
    posts: List[Dict[str, Any]] = Field(default_factory=list)
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    consultations: List[Dict[str, Any]] = Field(default_factory=list)
    sos_alerts: List[Dict[str, Any]] = Field(default_factory=list)


class SyncResponse(BaseModel):
    posts: List[Dict[str, Any]] = Field(default_factory=list)
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    consultations: List[Dict[str, Any]] = Field(default_factory=list)
    sos_alerts: List[Dict[str, Any]] = Field(default_factory=list)
    success: bool = True
    message: str = "Sync completed successfully"


@router.post("/", response_model=SyncResponse)
async def sync_offline_data(
    offline_data: OfflineData,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Synchronize data created while offline.

    This endpoint receives batches of offline data from the mobile client,
    processes them, and returns mapping between client-side IDs and new server IDs.

    Example request body:
    ```
    {
        "posts": [
            {
                "client_id": "offline-1234",
                "title": "My offline post",
                "content": "This was written while offline",
                "category": "vent",
                "is_anonymous": true,
                "timestamp": "2025-05-01T14:30:00.000Z"
            }
        ],
        "messages": [...],
        "consultations": [...],
        "sos_alerts": [...]
    }
    ```

    Returns mapping between client IDs and server IDs for each synced item.
    """
    try:
        # Process all offline data
        results = await process_offline_data(
            offline_data.dict(),
            user_id=current_user.id,
            user_language=current_user.language,
            db=db,
        )

        return SyncResponse(
            posts=results["posts"],
            messages=results["messages"],
            consultations=results["consultations"],
            sos_alerts=results["sos_alerts"],
            success=True,
            message="Sync completed successfully",
        )

    except Exception as e:
        return SyncResponse(success=False, message=f"Sync failed: {str(e)}")


@router.get("/status")
async def sync_status(current_user: User = Depends(get_current_user)):
    """
    Get the current server timestamp for synchronization purposes.
    The mobile client can use this to detect time drift.

    Returns:
        Dict with server timestamp and sync status
    """
    from datetime import datetime, timezone

    return {
        "server_time": datetime.now(timezone.utc).isoformat(),
        "sync_enabled": True,
        "user_id": current_user.id,
    }
