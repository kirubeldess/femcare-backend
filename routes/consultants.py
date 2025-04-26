import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models.consultant import Consultant
from pydantic_schemas.consultant import ConsultantCreate, ConsultantResponse, ConsultantUpdate

router = APIRouter()

@router.post("/", response_model=ConsultantResponse, status_code=201)
def create_consultant(consultant: ConsultantCreate, db: Session = Depends(get_db)):
    """
    Register a new consultant (therapist, gynecologist, etc.)
    """
    # Check if consultant with this email already exists
    existing_consultant = db.query(Consultant).filter(Consultant.email == consultant.email).first()
    if existing_consultant:
        raise HTTPException(status_code=400, detail="Consultant with this email already exists")
    
    db_consultant = Consultant(
        id=str(uuid.uuid4()),
        name=consultant.name,
        specialty=consultant.specialty,
        bio=consultant.bio,
        phone=consultant.phone,
        email=consultant.email,
        available=consultant.available
    )
    
    db.add(db_consultant)
    db.commit()
    db.refresh(db_consultant)
    return db_consultant

@router.get("/", response_model=List[ConsultantResponse])
def get_consultants(
    skip: int = 0, 
    limit: int = 100, 
    specialty: Optional[str] = None,
    available: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Get all consultants with optional filtering by specialty and availability
    """
    query = db.query(Consultant)
    
    if specialty:
        query = query.filter(Consultant.specialty == specialty)
    
    if available is not None:
        query = query.filter(Consultant.available == available)
    
    return query.offset(skip).limit(limit).all()

@router.get("/{consultant_id}", response_model=ConsultantResponse)
def get_consultant(consultant_id: str, db: Session = Depends(get_db)):
    """
    Get a specific consultant by ID
    """
    consultant = db.query(Consultant).filter(Consultant.id == consultant_id).first()
    if consultant is None:
        raise HTTPException(status_code=404, detail="Consultant not found")
    return consultant

@router.put("/{consultant_id}", response_model=ConsultantResponse)
def update_consultant(consultant_id: str, consultant_update: ConsultantUpdate, db: Session = Depends(get_db)):
    """
    Update a consultant's information
    """
    db_consultant = db.query(Consultant).filter(Consultant.id == consultant_id).first()
    if db_consultant is None:
        raise HTTPException(status_code=404, detail="Consultant not found")
    
    # Update email if provided and different from current
    if consultant_update.email and consultant_update.email != db_consultant.email:
        # Check if new email is already used by another consultant
        existing = db.query(Consultant).filter(Consultant.email == consultant_update.email).first()
        if existing and existing.id != consultant_id:
            raise HTTPException(status_code=400, detail="Email already in use")
    
    # Update fields if they are provided
    update_data = consultant_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_consultant, key, value)
    
    db.commit()
    db.refresh(db_consultant)
    return db_consultant

@router.delete("/{consultant_id}", status_code=204)
def delete_consultant(consultant_id: str, db: Session = Depends(get_db)):
    """
    Delete a consultant
    """
    db_consultant = db.query(Consultant).filter(Consultant.id == consultant_id).first()
    if db_consultant is None:
        raise HTTPException(status_code=404, detail="Consultant not found")
    
    db.delete(db_consultant)
    db.commit()
    return None

@router.get("/specialty/{specialty}", response_model=List[ConsultantResponse])
def get_consultants_by_specialty(specialty: str, available: Optional[bool] = None, db: Session = Depends(get_db)):
    """
    Get all consultants in a specific specialty with optional availability filter
    """
    query = db.query(Consultant).filter(Consultant.specialty == specialty)
    
    if available is not None:
        query = query.filter(Consultant.available == available)
    
    consultants = query.all()
    return consultants

@router.get("/available/", response_model=List[ConsultantResponse])
def get_available_consultants(db: Session = Depends(get_db)):
    """
    Get all consultants that are currently available
    """
    consultants = db.query(Consultant).filter(Consultant.available == True).all()
    return consultants 