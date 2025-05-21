# routes/ai_consultations.py
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models.ai_consultation import AIConsultation
from models.ai_consultation_message import AIConsultationMessage
from models.user import User
from pydantic_schemas.ai_consultation import (
    ConsultationCreate,
    ConsultationResponse,
    ConsultationUpdate,
)
from pydantic_schemas.ai_consultation_message import (
    MessageCreate,
    MessageResponse,
    MessageList,
)
from utils.auth import get_current_user
from utils.gemini_helper import get_consultation_response, get_chat_response
from datetime import datetime
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post("/chat/start", status_code=201)
async def start_chat_session(
    initial_message: MessageCreate,
    consultation_type: Optional[str] = Query(
        default="health",
        description="Type of consultation: health, legal, or mental_health",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start a new chat session with the AI assistant.
    Creates a new consultation and records the initial message from the user.
    Returns the consultation details with the AI's first response.
    """
    # Create a new consultation (session)
    chat_session = AIConsultation(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        symptoms=initial_message.message,  # Use the initial message as the symptoms field
        status="completed",  # Mark as completed immediately as we'll generate a response
    )

    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)

    # Add the user's initial message to the messages table
    user_message = AIConsultationMessage(
        id=str(uuid.uuid4()),
        consultation_id=chat_session.id,
        sender="user",
        content=initial_message.message,
    )

    db.add(user_message)
    db.commit()

    # Get AI response using the appropriate consultation handler
    ai_response = await get_consultation_response(
        consultation_type,
        initial_message.message,
        language=(
            current_user.language if hasattr(current_user, "language") else "english"
        ),
    )

    # Save the AI response to the consultation
    chat_session.ai_response = ai_response
    db.commit()
    db.refresh(chat_session)

    # Also save the AI response as a message
    ai_message = AIConsultationMessage(
        id=str(uuid.uuid4()),
        consultation_id=chat_session.id,
        sender="ai",
        content=ai_response,
    )

    db.add(ai_message)
    db.commit()

    # Get the latest version of the session
    fresh_session = (
        db.query(AIConsultation).filter(AIConsultation.id == chat_session.id).first()
    )

    # Create a response dictionary with all necessary fields
    response_data = {
        "id": fresh_session.id,
        "user_id": fresh_session.user_id,
        "conversation_id": fresh_session.conversation_id,
        "previous_consultation_id": fresh_session.previous_consultation_id,
        "symptoms": fresh_session.symptoms,
        "language": (
            fresh_session.language if hasattr(fresh_session, "language") else "english"
        ),
        "ai_response": fresh_session.ai_response,
        "contains_sensitive_issue": (
            fresh_session.contains_sensitive_issue
            if hasattr(fresh_session, "contains_sensitive_issue")
            else False
        ),
        "created_at": str(
            datetime.now()
        ),  # Convert to string to avoid serialization issues
        "status": fresh_session.status,
    }

    return JSONResponse(content=response_data)


@router.post("/chat/{session_id}/message", response_model=MessageResponse)
async def send_chat_message(
    session_id: str,
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a message in an existing chat session and get an AI response.
    """
    # Check if session exists and user has access
    chat_session = (
        db.query(AIConsultation).filter(AIConsultation.id == session_id).first()
    )
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # Check user permission
    if chat_session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=403, detail="Not authorized to access this chat session"
        )

    # Create and save user message
    user_message = AIConsultationMessage(
        id=str(uuid.uuid4()),
        consultation_id=session_id,
        sender="user",
        content=message.message,
    )

    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # Get chat history for context
    chat_history = (
        db.query(AIConsultationMessage)
        .filter(AIConsultationMessage.consultation_id == session_id)
        .order_by(AIConsultationMessage.timestamp)
        .all()
    )

    # Format messages for the AI
    formatted_messages = [
        {"sender": msg.sender, "content": msg.content} for msg in chat_history
    ]

    # Get language preference
    language = current_user.language if hasattr(current_user, "language") else "english"

    # Get AI response using the chat handler
    ai_response_text = await get_chat_response(formatted_messages, language=language)

    # Save AI response message
    ai_message = AIConsultationMessage(
        id=str(uuid.uuid4()),
        consultation_id=session_id,
        sender="ai",
        content=ai_response_text,
    )

    db.add(ai_message)
    db.commit()
    db.refresh(ai_message)

    return ai_message


@router.get("/chat/{session_id}/messages", response_model=List[MessageResponse])
async def get_chat_messages(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all messages for a specific chat session.
    Returns the messages in chronological order.
    """
    # Check if session exists and user has access
    chat_session = (
        db.query(AIConsultation).filter(AIConsultation.id == session_id).first()
    )
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # Check user permission
    if chat_session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=403, detail="Not authorized to access this chat session"
        )

    # Get all messages for this session
    messages = (
        db.query(AIConsultationMessage)
        .filter(AIConsultationMessage.consultation_id == session_id)
        .order_by(AIConsultationMessage.timestamp)
        .all()
    )

    return messages


@router.get("/chat/sessions", response_model=List[ConsultationResponse])
def get_user_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all chat sessions for the current user.
    """
    # Build the query
    query = db.query(AIConsultation).filter(AIConsultation.user_id == current_user.id)

    # Execute query with ordering (most recent first)
    sessions = query.order_by(AIConsultation.timestamp.desc()).all()

    return sessions


@router.post("/chat/continue/{previous_session_id}", status_code=201)
async def continue_chat_session(
    previous_session_id: str,
    initial_message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Continue a previous chat session by creating a new linked session with the context.
    """
    # Check if the previous session exists
    previous_session = (
        db.query(AIConsultation)
        .filter(AIConsultation.id == previous_session_id)
        .first()
    )
    if not previous_session:
        raise HTTPException(status_code=404, detail="Previous chat session not found")

    # Check user permission
    if previous_session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=403, detail="Not authorized to access the previous chat session"
        )

    # Get the conversation ID or create a new one if it doesn't exist
    conversation_id = previous_session.conversation_id or previous_session.id

    # Create a new session linked to the previous one
    new_session = AIConsultation(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        conversation_id=conversation_id,
        previous_consultation_id=previous_session_id,
        symptoms=initial_message.message,
        status="completed",
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    # Record the user's initial message
    user_message = AIConsultationMessage(
        id=str(uuid.uuid4()),
        consultation_id=new_session.id,
        sender="user",
        content=initial_message.message,
    )

    db.add(user_message)
    db.commit()

    # Get message history from previous session
    previous_messages = (
        db.query(AIConsultationMessage)
        .filter(AIConsultationMessage.consultation_id == previous_session_id)
        .order_by(AIConsultationMessage.timestamp)
        .all()
    )

    # Format previous messages for context
    formatted_messages = [
        {"sender": msg.sender, "content": msg.content} for msg in previous_messages
    ]

    # Add the new message
    formatted_messages.append({"sender": "user", "content": initial_message.message})

    # Get language preference
    language = current_user.language if hasattr(current_user, "language") else "english"

    # Get AI response using the chat handler (with full context)
    ai_response_text = await get_chat_response(formatted_messages, language=language)

    # Save AI response to the consultation
    new_session.ai_response = ai_response_text
    db.commit()
    db.refresh(new_session)

    # Save AI response as message
    ai_message = AIConsultationMessage(
        id=str(uuid.uuid4()),
        consultation_id=new_session.id,
        sender="ai",
        content=ai_response_text,
    )

    db.add(ai_message)
    db.commit()

    # Get the latest version of the session
    fresh_session = (
        db.query(AIConsultation).filter(AIConsultation.id == new_session.id).first()
    )

    # Create a response dictionary with all necessary fields
    response_data = {
        "id": fresh_session.id,
        "user_id": fresh_session.user_id,
        "conversation_id": fresh_session.conversation_id,
        "previous_consultation_id": fresh_session.previous_consultation_id,
        "symptoms": fresh_session.symptoms,
        "language": (
            fresh_session.language if hasattr(fresh_session, "language") else "english"
        ),
        "ai_response": fresh_session.ai_response,
        "contains_sensitive_issue": (
            fresh_session.contains_sensitive_issue
            if hasattr(fresh_session, "contains_sensitive_issue")
            else False
        ),
        "created_at": str(
            datetime.now()
        ),  # Convert to string to avoid serialization issues
        "status": fresh_session.status,
    }

    return JSONResponse(content=response_data)


# Keep the original endpoints for backward compatibility
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all AI consultations for the current authenticated user
    """
    # Build the query
    query = db.query(AIConsultation).filter(AIConsultation.user_id == current_user.id)

    # Execute query with ordering
    consultations = query.order_by(AIConsultation.timestamp.desc()).all()

    return consultations


@router.get("/user/{user_id}", response_model=List[ConsultationResponse])
def get_user_consultations(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all AI consultations for a specific user.
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

    # Execute query with ordering
    consultations = query.order_by(AIConsultation.timestamp.desc()).all()

    return consultations


@router.post("/{consultation_id}/message", response_model=MessageResponse)
async def send_message(
    consultation_id: str,
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a message in an AI consultation chat and get an AI response.
    The backend will:
    - Save the user message
    - Call the LLM service with chat history as context
    - Save and return the AI's reply
    """
    # Check if consultation exists and user has access
    consultation = (
        db.query(AIConsultation).filter(AIConsultation.id == consultation_id).first()
    )
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    # Check user permission
    if consultation.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=403, detail="Not authorized to access this consultation"
        )

    # Create and save user message
    user_message = AIConsultationMessage(
        id=str(uuid.uuid4()),
        consultation_id=consultation_id,
        sender="user",
        content=message.message,
    )

    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # Get chat history for context
    chat_history = (
        db.query(AIConsultationMessage)
        .filter(AIConsultationMessage.consultation_id == consultation_id)
        .order_by(AIConsultationMessage.timestamp)
        .all()
    )

    # Format messages for the AI
    formatted_messages = [
        {"sender": msg.sender, "content": msg.content} for msg in chat_history
    ]

    # Get language preference (default to user's setting)
    language = current_user.language if hasattr(current_user, "language") else "english"

    # Get AI response using the LLM
    ai_response_text = await get_chat_response(formatted_messages, language=language)

    # Save AI response message
    ai_message = AIConsultationMessage(
        id=str(uuid.uuid4()),
        consultation_id=consultation_id,
        sender="ai",
        content=ai_response_text,
    )

    db.add(ai_message)
    db.commit()
    db.refresh(ai_message)

    return ai_message


@router.get("/{consultation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    consultation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all messages for a specific AI consultation chat.
    Returns the messages in chronological order.
    """
    # Check if consultation exists and user has access
    consultation = (
        db.query(AIConsultation).filter(AIConsultation.id == consultation_id).first()
    )
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    # Check user permission
    if consultation.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=403, detail="Not authorized to access this consultation"
        )

    # Get all messages for this consultation
    messages = (
        db.query(AIConsultationMessage)
        .filter(AIConsultationMessage.consultation_id == consultation_id)
        .order_by(AIConsultationMessage.timestamp)
        .all()
    )

    return messages
