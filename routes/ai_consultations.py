import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models.ai_consultation import AIConsultation, ConsultationType
from models.user import User
from pydantic_schemas.ai_consultation import ConsultationCreate, ConsultationResponse, ConsultationUpdate, ConsultationType as SchemaConsultationType
from utils.gemini_helper import get_consultation_response

router = APIRouter()

@router.post("/", response_model=ConsultationResponse, status_code=201)
async def create_consultation(
    consultation: ConsultationCreate, 
    db: Session = Depends(get_db), 
    user_id: str = None
):
    """
    Create a new AI consultation request (health, legal, or mental health).
    user_id should come from the authentication token.
    """
    # Validate user exists
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create consultation
    db_consultation = AIConsultation(
        id=str(uuid.uuid4()),
        user_id=user_id,
        consultation_type=consultation.consultation_type.value,
        symptoms=consultation.symptoms,
        status="pending"
    )
    
    db.add(db_consultation)
    db.commit()
    db.refresh(db_consultation)
    
    # Call the appropriate AI service based on consultation type
    ai_response = await get_consultation_response(consultation.consultation_type, consultation.symptoms)
    
    # Update the consultation with the AI response
    db_consultation.ai_response = ai_response
    db_consultation.status = "completed"
    
    db.commit()
    db.refresh(db_consultation)
    
    return db_consultation

@router.get("/types", response_model=List[str])
def get_consultation_types():
    """
    Get a list of available consultation types
    """
    return [t.value for t in SchemaConsultationType]

@router.patch("/{consultation_id}", response_model=ConsultationResponse)
def update_consultation(
    consultation_id: str, 
    update: ConsultationUpdate, 
    db: Session = Depends(get_db)
):
    """
    Update an AI consultation with the response from the AI service.
    """
    consultation = db.query(AIConsultation).filter(AIConsultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    consultation.ai_response = update.ai_response
    consultation.status = update.status.value if hasattr(update.status, 'value') else update.status
    
    db.commit()
    db.refresh(consultation)
    return consultation

@router.get("/{consultation_id}", response_model=ConsultationResponse)
def get_consultation(consultation_id: str, db: Session = Depends(get_db)):
    """
    Get details for a specific consultation by ID
    """
    consultation = db.query(AIConsultation).filter(AIConsultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    return consultation

@router.get("/user/{user_id}", response_model=List[ConsultationResponse])
def get_user_consultations(
    user_id: str, 
    consultation_type: Optional[SchemaConsultationType] = None,
    db: Session = Depends(get_db)
):
    """
    Get all AI consultations for a specific user, optionally filtered by consultation type
    """
    # Validate user exists
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="User not found")
    
    # Build the query
    query = db.query(AIConsultation).filter(AIConsultation.user_id == user_id)
    
    # Add type filter if provided
    if consultation_type:
        query = query.filter(AIConsultation.consultation_type == consultation_type.value)
    
    # Execute query with ordering
    consultations = query.order_by(AIConsultation.timestamp.desc()).all()
    
    return consultations 