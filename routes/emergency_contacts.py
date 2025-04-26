import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models.emergency_contact import EmergencyContact, EmergencyType
from pydantic_schemas.emergency_contact import EmergencyContactCreate, EmergencyContactResponse, EmergencyContactUpdate

router = APIRouter()

@router.post("/", response_model=EmergencyContactResponse, status_code=201)
def create_emergency_contact(emergency_contact: EmergencyContactCreate, db: Session = Depends(get_db)):
    """
    Create a new emergency contact (hospital, police station, or health center).
    """
    db_emergency_contact = EmergencyContact(
        id=str(uuid.uuid4()),
        name=emergency_contact.name,
        type=emergency_contact.type,
        latitude=emergency_contact.latitude,
        longitude=emergency_contact.longitude,
        phone=emergency_contact.phone,
        region=emergency_contact.region
    )
    
    db.add(db_emergency_contact)
    db.commit()
    db.refresh(db_emergency_contact)
    return db_emergency_contact

@router.get("/", response_model=List[EmergencyContactResponse])
def get_emergency_contacts(
    skip: int = 0, 
    limit: int = 100, 
    type: Optional[EmergencyType] = None,
    region: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all emergency contacts with optional filtering by type and region.
    """
    query = db.query(EmergencyContact)
    
    if type:
        query = query.filter(EmergencyContact.type == type)
    
    if region:
        query = query.filter(EmergencyContact.region == region)
    
    return query.offset(skip).limit(limit).all()

@router.get("/{emergency_contact_id}", response_model=EmergencyContactResponse)
def get_emergency_contact(emergency_contact_id: str, db: Session = Depends(get_db)):
    """
    Get a specific emergency contact by ID.
    """
    emergency_contact = db.query(EmergencyContact).filter(EmergencyContact.id == emergency_contact_id).first()
    if emergency_contact is None:
        raise HTTPException(status_code=404, detail="Emergency contact not found")
    return emergency_contact

@router.put("/{emergency_contact_id}", response_model=EmergencyContactResponse)
def update_emergency_contact(
    emergency_contact_id: str, 
    emergency_contact_update: EmergencyContactUpdate, 
    db: Session = Depends(get_db)
):
    """
    Update an emergency contact's information.
    """
    db_emergency_contact = db.query(EmergencyContact).filter(EmergencyContact.id == emergency_contact_id).first()
    if db_emergency_contact is None:
        raise HTTPException(status_code=404, detail="Emergency contact not found")
    
    # Update fields if they are provided
    update_data = emergency_contact_update.dict(exclude_unset=True)
    
    # Convert enum to value if it exists
    if 'type' in update_data and update_data['type'] is not None:
        update_data['type'] = update_data['type'].value
    
    for key, value in update_data.items():
        setattr(db_emergency_contact, key, value)
    
    db.commit()
    db.refresh(db_emergency_contact)
    return db_emergency_contact

@router.delete("/{emergency_contact_id}", status_code=204)
def delete_emergency_contact(emergency_contact_id: str, db: Session = Depends(get_db)):
    """
    Delete an emergency contact.
    """
    db_emergency_contact = db.query(EmergencyContact).filter(EmergencyContact.id == emergency_contact_id).first()
    if db_emergency_contact is None:
        raise HTTPException(status_code=404, detail="Emergency contact not found")
    
    db.delete(db_emergency_contact)
    db.commit()
    return None

@router.get("/type/{type}", response_model=List[EmergencyContactResponse])
def get_emergency_contacts_by_type(
    type: EmergencyType, 
    region: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all emergency contacts of a specific type with optional region filter.
    """
    query = db.query(EmergencyContact).filter(EmergencyContact.type == type)
    
    if region:
        query = query.filter(EmergencyContact.region == region)
    
    emergency_contacts = query.all()
    return emergency_contacts

@router.get("/region/{region}", response_model=List[EmergencyContactResponse])
def get_emergency_contacts_by_region(
    region: str, 
    type: Optional[EmergencyType] = None,
    db: Session = Depends(get_db)
):
    """
    Get all emergency contacts in a specific region with optional type filter.
    """
    query = db.query(EmergencyContact).filter(EmergencyContact.region == region)
    
    if type:
        query = query.filter(EmergencyContact.type == type)
    
    emergency_contacts = query.all()
    return emergency_contacts

@router.get("/nearest", response_model=List[EmergencyContactResponse])
def get_nearest_emergency_contacts(
    latitude: float,
    longitude: float,
    type: Optional[EmergencyType] = None,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Get emergency contacts nearest to a specific location.
    Uses a simplified distance calculation (not exact but good for relative distances).
    
    For more accurate distance calculation, you'd typically use PostGIS or a dedicated geospatial library.
    """
    # Create a SQL expression for calculating distance
    # This is a simplified version using Euclidean distance, not actual geographical distance
    from sqlalchemy import func
    
    # Cast latitude and longitude to Decimal for comparison
    lat = func.cast(latitude, EmergencyContact.latitude.type)
    lon = func.cast(longitude, EmergencyContact.longitude.type)
    
    # Calculate distance (simplified)
    distance = func.sqrt(
        func.power(EmergencyContact.latitude - lat, 2) + 
        func.power(EmergencyContact.longitude - lon, 2)
    )
    
    query = db.query(EmergencyContact).order_by(distance)
    
    if type:
        query = query.filter(EmergencyContact.type == type)
    
    return query.limit(limit).all() 