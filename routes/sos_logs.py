import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.sos_log import SOSLog, SOSStatus
from models.user import User
from models.emergency_contact import EmergencyContact, EmergencyType
from pydantic_schemas.sos_log import SOSLogCreate, SOSLogResponse, SOSLogUpdate
from pydantic_schemas.emergency_contact import EmergencyContactResponse

router = APIRouter()

@router.post("/", response_model=SOSLogResponse, status_code=201)
def create_sos_log(
    sos_log: SOSLogCreate, 
    db: Session = Depends(get_db),
    user_id: str = None
):
    """
    Log an SOS button press with the user's current location.
    In a real app, the user_id would come from the authentication token.
    
    Example request:
    {
        "latitude": 9.0222,
        "longitude": 38.7468
    }
    """
    # Validate user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create the SOS log
    db_sos_log = SOSLog(
        id=str(uuid.uuid4()),
        user_id=user_id,
        latitude=sos_log.latitude,
        longitude=sos_log.longitude,
        status=SOSStatus.sent
    )
    
    db.add(db_sos_log)
    db.commit()
    db.refresh(db_sos_log)
    
    # In a real application, you would trigger notification to emergency services here
    
    return db_sos_log

@router.patch("/{sos_log_id}", response_model=SOSLogResponse)
def update_sos_status(
    sos_log_id: str, 
    sos_update: SOSLogUpdate, 
    db: Session = Depends(get_db)
):
    """
    Update the status of an SOS log (e.g., when emergency services respond or resolve the case).
    
    Example request:
    {
        "status": "received"
    }
    """
    sos_log = db.query(SOSLog).filter(SOSLog.id == sos_log_id).first()
    if not sos_log:
        raise HTTPException(status_code=404, detail="SOS log not found")
    
    sos_log.status = sos_update.status
    db.commit()
    db.refresh(sos_log)
    return sos_log

@router.get("/user/{user_id}", response_model=List[SOSLogResponse])
def get_user_sos_logs(
    user_id: str, 
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all SOS logs for a specific user.
    """
    # Validate user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    sos_logs = db.query(SOSLog).filter(
        SOSLog.user_id == user_id
    ).order_by(SOSLog.timestamp.desc()).offset(skip).limit(limit).all()
    
    return sos_logs

@router.get("/active", response_model=List[SOSLogResponse])
def get_active_sos_logs(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all active (non-resolved) SOS logs.
    """
    sos_logs = db.query(SOSLog).filter(
        SOSLog.status != SOSStatus.resolved
    ).order_by(SOSLog.timestamp.desc()).offset(skip).limit(limit).all()
    
    return sos_logs

@router.get("/{sos_log_id}/nearby_emergency", response_model=List[EmergencyContactResponse])
def get_nearby_emergency_contacts(
    sos_log_id: str,
    type: Optional[EmergencyType] = None,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Get emergency contacts nearest to the location of an SOS log.
    Optionally filter by type of emergency contact.
    """
    sos_log = db.query(SOSLog).filter(SOSLog.id == sos_log_id).first()
    if not sos_log:
        raise HTTPException(status_code=404, detail="SOS log not found")
    
    # Create a SQL expression for calculating distance
    from sqlalchemy import func
    
    # Calculate distance (simplified)
    distance = func.sqrt(
        func.power(EmergencyContact.latitude - sos_log.latitude, 2) + 
        func.power(EmergencyContact.longitude - sos_log.longitude, 2)
    )
    
    query = db.query(EmergencyContact).order_by(distance)
    
    if type:
        query = query.filter(EmergencyContact.type == type)
    
    return query.limit(limit).all() 