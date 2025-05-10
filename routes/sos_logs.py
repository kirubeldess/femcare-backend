# routes/sos_logs.py
import uuid
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from models.sos_log import SOSLog, SOSStatus
from models.user import User
from models.emergency_contact import EmergencyContact, EmergencyType
from pydantic_schemas.sos_log import SOSLogCreate, SOSLogResponse, SOSLogUpdate
from pydantic_schemas.emergency_contact import EmergencyContactResponse
from utils.auth import get_current_user
from utils.sms_helper import send_emergency_sms

router = APIRouter()


@router.post("/", response_model=SOSLogResponse, status_code=201)
async def create_sos_alert(
    sos_log: SOSLogCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Log an SOS button press with the user's current location and send SMS alerts
    to emergency contacts.

    Example request:
    {
        "latitude": 9.0222,
        "longitude": 38.7468
    }
    """
    # Create the SOS log
    db_sos_log = SOSLog(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        latitude=sos_log.latitude,
        longitude=sos_log.longitude,
        status=SOSStatus.sent,
    )

    db.add(db_sos_log)
    db.commit()
    db.refresh(db_sos_log)

    # In a real application, send SMS notification to emergency contacts
    if current_user.emergency_contact:
        # Queue the SMS sending in the background
        google_maps_url = f"https://www.google.com/maps/search/?api=1&query={sos_log.latitude},{sos_log.longitude}"
        message = f"EMERGENCY ALERT: {current_user.name} needs help! Location: {google_maps_url}"

        background_tasks.add_task(
            send_emergency_sms, to=current_user.emergency_contact, message=message
        )

    return db_sos_log


@router.post("/offline", response_model=SOSLogResponse, status_code=201)
async def create_offline_sos_alert(
    sos_log: SOSLogCreate,
    background_tasks: BackgroundTasks,
    timestamp: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Process an SOS alert that was triggered when the user was offline.
    The timestamp is provided by the client once it reconnects to the internet.

    Example request:
    {
        "latitude": 9.0222,
        "longitude": 38.7468,
        "timestamp": "2025-05-01T14:30:00.000Z"
    }
    """
    # Create the SOS log with the provided timestamp
    db_sos_log = SOSLog(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        latitude=sos_log.latitude,
        longitude=sos_log.longitude,
        status=SOSStatus.sent,
    )

    # If timestamp was provided, override the default
    if timestamp:
        from datetime import datetime

        try:
            parsed_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            db_sos_log.timestamp = parsed_time
        except ValueError:
            # If timestamp is invalid, just use the current time (default)
            pass

    db.add(db_sos_log)
    db.commit()
    db.refresh(db_sos_log)

    # Send SMS notification to emergency contacts
    if current_user.emergency_contact:
        google_maps_url = f"https://www.google.com/maps/search/?api=1&query={sos_log.latitude},{sos_log.longitude}"
        message = f"DELAYED EMERGENCY ALERT: {current_user.name} triggered an alert while offline! Location: {google_maps_url}"

        background_tasks.add_task(
            send_emergency_sms, to=current_user.emergency_contact, message=message
        )

    return db_sos_log


@router.patch("/{sos_log_id}", response_model=SOSLogResponse)
def update_sos_status(
    sos_log_id: str,
    sos_update: SOSLogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update the status of an SOS log (e.g., when emergency services respond or resolve the case).
    Only administrators or the original user can update the status.

    Example request:
    {
        "status": "received"
    }
    """
    sos_log = db.query(SOSLog).filter(SOSLog.id == sos_log_id).first()
    if not sos_log:
        raise HTTPException(status_code=404, detail="SOS log not found")

    # Check permissions - only admin or the user who created the alert can update it
    if current_user.role != "admin" and sos_log.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this SOS alert"
        )

    sos_log.status = sos_update.status
    db.commit()
    db.refresh(sos_log)
    return sos_log


@router.get("/user/me", response_model=List[SOSLogResponse])
def get_my_sos_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """
    Get all SOS logs for the current authenticated user.
    """
    sos_logs = (
        db.query(SOSLog)
        .filter(SOSLog.user_id == current_user.id)
        .order_by(SOSLog.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return sos_logs


@router.get("/user/{user_id}", response_model=List[SOSLogResponse])
def get_user_sos_logs(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """
    Get all SOS logs for a specific user. Admin only.
    """
    # Check if the current user is an admin
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to view these SOS logs"
        )

    # Validate user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    sos_logs = (
        db.query(SOSLog)
        .filter(SOSLog.user_id == user_id)
        .order_by(SOSLog.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return sos_logs


@router.get("/active", response_model=List[SOSLogResponse])
def get_active_sos_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """
    Get all active (non-resolved) SOS logs. Admin only.
    """
    # Check if the current user is an admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403, detail="Not authorized to view all SOS logs"
        )

    sos_logs = (
        db.query(SOSLog)
        .filter(SOSLog.status != SOSStatus.resolved)
        .order_by(SOSLog.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return sos_logs


@router.get(
    "/{sos_log_id}/nearby-emergency", response_model=List[EmergencyContactResponse]
)
def get_nearby_emergency_contacts(
    sos_log_id: str,
    type: Optional[EmergencyType] = None,
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get emergency contacts nearest to the location of an SOS log.
    Optionally filter by type of emergency contact.
    """
    sos_log = db.query(SOSLog).filter(SOSLog.id == sos_log_id).first()
    if not sos_log:
        raise HTTPException(status_code=404, detail="SOS log not found")

    # Check permissions - only admin or the user who created the alert can access this
    if current_user.role != "admin" and sos_log.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this SOS information"
        )

    # Create a SQL expression for calculating distance
    from sqlalchemy import func

    # Calculate distance (simplified)
    distance = func.sqrt(
        func.power(EmergencyContact.latitude - sos_log.latitude, 2)
        + func.power(EmergencyContact.longitude - sos_log.longitude, 2)
    )

    query = db.query(EmergencyContact).order_by(distance)

    if type:
        query = query.filter(EmergencyContact.type == type)

    return query.limit(limit).all()
