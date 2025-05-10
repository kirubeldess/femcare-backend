# routes/ai_consultations.py
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models.ai_consultation import AIConsultation
from models.user import User
from pydantic_schemas.ai_consultation import (
    ConsultationCreate,
    ConsultationResponse,
    ConsultationUpdate,
)
from utils.auth import get_current_user
from utils.gemini_helper import get_consultation_response

router = APIRouter()


@router.post("/", response_model=ConsultationResponse, status_code=201)
async def create_consultation(
    consultation: ConsultationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new AI consultation request (health, legal, or mental health).
    Supports multilingual inputs and responses based on the user's language preference.
    """
    # Create consultation record
    db_consultation = AIConsultation(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        consultation_type=consultation.consultation_type.value,
        symptoms=consultation.symptoms,
        status="pending",
    )

    db.add(db_consultation)
    db.commit()
    db.refresh(db_consultation)

    # Call the appropriate AI service with language preference
    ai_response = await get_consultation_response(
        consultation.consultation_type,
        consultation.symptoms,
        language=current_user.language,  # Pass user's language preference
    )

    # Update the consultation with the AI response
    db_consultation.ai_response = ai_response
    db_consultation.status = "completed"

    db.commit()
    db.refresh(db_consultation)

    return db_consultation


# @router.get("/types", response_model=List[str])
# def get_consultation_types():
#     """
#     Get a list of available consultation types
#     """
#     return [t.value for t in SchemaConsultationType]


@router.post("/offline", response_model=ConsultationResponse, status_code=201)
async def process_offline_consultation(
    consultation: ConsultationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Handle consultations that were created while the user was offline.
    This endpoint is called when the device reconnects to the internet.
    """
    # Create consultation with offline flag
    db_consultation = AIConsultation(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        consultation_type=consultation.consultation_type.value,
        symptoms=consultation.symptoms,
        status="pending",
    )

    db.add(db_consultation)
    db.commit()
    db.refresh(db_consultation)

    # Process the consultation
    ai_response = await get_consultation_response(
        consultation.consultation_type,
        consultation.symptoms,
        language=current_user.language,
    )

    # Update with response
    db_consultation.ai_response = ai_response
    db_consultation.status = "completed"

    db.commit()
    db.refresh(db_consultation)

    return db_consultation


@router.patch("/{consultation_id}", response_model=ConsultationResponse)
def update_consultation(
    consultation_id: str,
    update: ConsultationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an AI consultation with the response from the AI service.
    Only administrators can update consultations.
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403, detail="Not authorized to update consultations"
        )

    consultation = (
        db.query(AIConsultation).filter(AIConsultation.id == consultation_id).first()
    )
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    consultation.ai_response = update.ai_response
    consultation.status = (
        update.status.value if hasattr(update.status, "value") else update.status
    )

    db.commit()
    db.refresh(consultation)
    return consultation


@router.get("/{consultation_id}", response_model=ConsultationResponse)
def get_consultation(
    consultation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get details for a specific consultation by ID.
    Users can only access their own consultations, admins can access any.
    """
    consultation = (
        db.query(AIConsultation).filter(AIConsultation.id == consultation_id).first()
    )
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    # Check if the user has permission to access this consultation
    if current_user.role != "admin" and consultation.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this consultation"
        )

    return consultation


@router.get("/user/me", response_model=List[ConsultationResponse])
def get_my_consultations(
    # consultation_type: Optional[ConsultationType] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all AI consultations for the current authenticated user, optionally filtered by type.
    """
    # Build the query
    query = db.query(AIConsultation).filter(AIConsultation.user_id == current_user.id)

    # # Add type filter if provided
    # if consultation_type:
    #     query = query.filter(
    #         AIConsultation.consultation_type == consultation_type.value
    #     )

    # Execute query with ordering
    consultations = query.order_by(AIConsultation.timestamp.desc()).all()

    return consultations


@router.get("/user/{user_id}", response_model=List[ConsultationResponse])
def get_user_consultations(
    user_id: str,
    # consultation_type: Optional[SchemaConsultationType] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all AI consultations for a specific user, optionally filtered by consultation type.
    Admin only, or the user themselves.
    """
    # Check permissions
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to view these consultations"
        )

    # Validate user exists
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="User not found")

    # Build the query
    query = db.query(AIConsultation).filter(AIConsultation.user_id == user_id)

    # # Add type filter if provided
    # if consultation_type:
    #     query = query.filter(
    #         AIConsultation.consultation_type == consultation_type.value
    #     )

    # Execute query with ordering
    consultations = query.order_by(AIConsultation.timestamp.desc()).all()

    return consultations
