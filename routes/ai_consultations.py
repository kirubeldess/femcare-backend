import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models.ai_consultation import AIConsultation, ConsultationStatus
from models.user import User
from pydantic_schemas.ai_consultation import ConsultationCreate, ConsultationResponse, ConsultationUpdate

router = APIRouter()

@router.post("/", response_model=ConsultationResponse, status_code=201)
def create_consultation(
    consultation: ConsultationCreate, 
    db: Session = Depends(get_db), 
    user_id: str = None
):
    
    #Create a new AI consultation request. In a real app, user_id would come from the authentication token.
    
    # Validate user exists
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create consultation
    db_consultation = AIConsultation(
        id=str(uuid.uuid4()),
        user_id=user_id,
        symptoms=consultation.symptoms,
        status=ConsultationStatus.pending
    )
    
    db.add(db_consultation)
    db.commit()
    db.refresh(db_consultation)
    
    # In a real application, here you would:
    # 1. Call an AI service to analyze the symptoms
    # 2. Update the consultation with the AI response
    # For now, we'll just return the pending consultation
    
    return db_consultation

@router.patch("/{consultation_id}", response_model=ConsultationResponse)
def update_consultation(
    consultation_id: str, 
    update: ConsultationUpdate, 
    db: Session = Depends(get_db)
):
    
    #Update an AI consultation with the response from the AI service.
    
    consultation = db.query(AIConsultation).filter(AIConsultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    consultation.ai_response = update.ai_response
    consultation.status = update.status
    
    db.commit()
    db.refresh(consultation)
    return consultation

@router.get("/{consultation_id}", response_model=ConsultationResponse)
def get_consultation(consultation_id: str, db: Session = Depends(get_db)):
    
    #Get details for a specific consultation by ID
    
    consultation = db.query(AIConsultation).filter(AIConsultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    return consultation

@router.get("/user/{user_id}", response_model=List[ConsultationResponse])
def get_user_consultations(user_id: str, db: Session = Depends(get_db)):
    
    #Get all AI consultations for a specific user
    
    # Validate user exists
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="User not found")
    
    consultations = db.query(AIConsultation).filter(
        AIConsultation.user_id == user_id
    ).order_by(AIConsultation.timestamp.desc()).all()
    
    return consultations 