import uuid
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models.consultant_message import ConsultantMessage, MessageStatus, EntityType
from models.consultant import Consultant
from models.user import User
from pydantic_schemas.consultant_message import (
    ConsultantMessageCreate,
    ConsultantMessageResponse,
    ConsultantMessageUpdate,
)

router = APIRouter()

# Define status values as constants to avoid enum reference issues
APPROVED_STATUSES = ["sent", "delivered", "read", "accepted"]
REQUEST_STATUS = "requested"
REJECTED_STATUS = "rejected"


@router.post("/", response_model=ConsultantMessageResponse, status_code=201)
def send_message(
    message: ConsultantMessageCreate,
    db: Session = Depends(get_db),
    sender_id: str = None,
    sender_type: str = None,
):
    """
    Send a message between a user and a consultant.
    In a real app, sender_id and sender_type would come from the authentication token.

    Example:
    For a user sending to a consultant:
    - sender_id: "3bc4c93b-4406-4d39-854b-6648476f604b"
    - sender_type: "user"
    - receiver_id: "2ca23e7e-0cd5-4d2f-ba36-4fa7dbcb4d06"
    - receiver_type: "consultant"
    """
    # Validate sender exists
    if sender_type == "user":
        if not db.query(User).filter(User.id == sender_id).first():
            raise HTTPException(status_code=404, detail="Sender user not found")
    elif sender_type == "consultant":
        if not db.query(Consultant).filter(Consultant.id == sender_id).first():
            raise HTTPException(status_code=404, detail="Sender consultant not found")
    else:
        raise HTTPException(status_code=400, detail="Invalid sender type")

    # Validate receiver exists
    if message.receiver_type.value == "user":
        if not db.query(User).filter(User.id == message.receiver_id).first():
            raise HTTPException(status_code=404, detail="Receiver user not found")
    elif message.receiver_type.value == "consultant":
        if (
            not db.query(Consultant)
            .filter(Consultant.id == message.receiver_id)
            .first()
        ):
            raise HTTPException(status_code=404, detail="Receiver consultant not found")
    else:
        raise HTTPException(status_code=400, detail="Invalid receiver type")

    # Create message
    db_message = ConsultantMessage(
        id=str(uuid.uuid4()),
        sender_id=sender_id,
        sender_type=EntityType(sender_type),
        receiver_id=message.receiver_id,
        receiver_type=message.receiver_type,
        content=message.content,
        status=MessageStatus.sent,
    )

    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


@router.get("/thread", response_model=List[ConsultantMessageResponse])
def get_message_thread(user_id: str, consultant_id: str, db: Session = Depends(get_db)):
    """
    Get all messages between a specific user and consultant

    Example:
    - user_id: "3bc4c93b-4406-4d39-854b-6648476f604b"
    - consultant_id: "2ca23e7e-0cd5-4d2f-ba36-4fa7dbcb4d06"
    """
    # Validate both entities exist
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="User not found")

    if not db.query(Consultant).filter(Consultant.id == consultant_id).first():
        raise HTTPException(status_code=404, detail="Consultant not found")

    # Get messages where:
    # 1. User is sender AND Consultant is receiver, OR
    # 2. Consultant is sender AND User is receiver
    messages = (
        db.query(ConsultantMessage)
        .filter(
            (
                (ConsultantMessage.sender_id == user_id)
                & (ConsultantMessage.sender_type == EntityType.user)
                & (ConsultantMessage.receiver_id == consultant_id)
                & (ConsultantMessage.receiver_type == EntityType.consultant)
            )
            | (
                (ConsultantMessage.sender_id == consultant_id)
                & (ConsultantMessage.sender_type == EntityType.consultant)
                & (ConsultantMessage.receiver_id == user_id)
                & (ConsultantMessage.receiver_type == EntityType.user)
            )
        )
        .order_by(ConsultantMessage.timestamp)
        .all()
    )

    return messages


@router.get("/user/{user_id}", response_model=List[Dict])
def get_user_consultations(user_id: str, db: Session = Depends(get_db)):
    """
    Get all conversations between a user and various consultants

    Example:
    - user_id: "3bc4c93b-4406-4d39-854b-6648476f604b"
    """
    # Validate user exists
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="User not found")

    # Find all consultants this user has spoken with
    consultant_messages = (
        db.query(ConsultantMessage)
        .filter(
            (
                (ConsultantMessage.sender_id == user_id)
                & (ConsultantMessage.sender_type == EntityType.user)
                & (ConsultantMessage.receiver_type == EntityType.consultant)
            )
            | (
                (ConsultantMessage.receiver_id == user_id)
                & (ConsultantMessage.receiver_type == EntityType.user)
                & (ConsultantMessage.sender_type == EntityType.consultant)
            )
        )
        .all()
    )

    # Get unique consultant IDs
    consultant_ids = set()
    for msg in consultant_messages:
        if msg.sender_type == EntityType.consultant:
            consultant_ids.add(msg.sender_id)
        elif msg.receiver_type == EntityType.consultant:
            consultant_ids.add(msg.receiver_id)

    # Get conversation summaries
    conversations = []
    for consultant_id in consultant_ids:
        consultant = db.query(Consultant).filter(Consultant.id == consultant_id).first()
        if not consultant:
            continue

        # Get last message in this conversation
        last_message = (
            db.query(ConsultantMessage)
            .filter(
                (
                    (ConsultantMessage.sender_id == user_id)
                    & (ConsultantMessage.sender_type == EntityType.user)
                    & (ConsultantMessage.receiver_id == consultant_id)
                    & (ConsultantMessage.receiver_type == EntityType.consultant)
                )
                | (
                    (ConsultantMessage.sender_id == consultant_id)
                    & (ConsultantMessage.sender_type == EntityType.consultant)
                    & (ConsultantMessage.receiver_id == user_id)
                    & (ConsultantMessage.receiver_type == EntityType.user)
                )
            )
            .order_by(ConsultantMessage.timestamp.desc())
            .first()
        )

        # Count unread messages
        unread_count = (
            db.query(ConsultantMessage)
            .filter(
                (ConsultantMessage.sender_id == consultant_id)
                & (ConsultantMessage.sender_type == EntityType.consultant)
                & (ConsultantMessage.receiver_id == user_id)
                & (ConsultantMessage.receiver_type == EntityType.user)
                & (ConsultantMessage.status != MessageStatus.read)
            )
            .count()
        )

        conversations.append(
            {
                "consultant_id": consultant_id,
                "consultant_name": consultant.name,
                "specialty": consultant.specialty,
                "last_message": ConsultantMessageResponse.from_orm(last_message),
                "unread_count": unread_count,
            }
        )

    return conversations


@router.get("/consultant/{consultant_id}", response_model=List[Dict])
def get_consultant_clients(consultant_id: str, db: Session = Depends(get_db)):
    """
    Get all conversations between a consultant and various users

    Example:
    - consultant_id: "2ca23e7e-0cd5-4d2f-ba36-4fa7dbcb4d06"
    """
    # Validate consultant exists
    if not db.query(Consultant).filter(Consultant.id == consultant_id).first():
        raise HTTPException(status_code=404, detail="Consultant not found")

    # Find all users this consultant has spoken with
    user_messages = (
        db.query(ConsultantMessage)
        .filter(
            (
                (ConsultantMessage.sender_id == consultant_id)
                & (ConsultantMessage.sender_type == EntityType.consultant)
                & (ConsultantMessage.receiver_type == EntityType.user)
            )
            | (
                (ConsultantMessage.receiver_id == consultant_id)
                & (ConsultantMessage.receiver_type == EntityType.consultant)
                & (ConsultantMessage.sender_type == EntityType.user)
            )
        )
        .all()
    )

    # Get unique user IDs
    user_ids = set()
    for msg in user_messages:
        if msg.sender_type == EntityType.user:
            user_ids.add(msg.sender_id)
        elif msg.receiver_type == EntityType.user:
            user_ids.add(msg.receiver_id)

    # Get conversation summaries
    conversations = []
    for user_id in user_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            continue

        # Get last message in this conversation
        last_message = (
            db.query(ConsultantMessage)
            .filter(
                (
                    (ConsultantMessage.sender_id == consultant_id)
                    & (ConsultantMessage.sender_type == EntityType.consultant)
                    & (ConsultantMessage.receiver_id == user_id)
                    & (ConsultantMessage.receiver_type == EntityType.user)
                )
                | (
                    (ConsultantMessage.sender_id == user_id)
                    & (ConsultantMessage.sender_type == EntityType.user)
                    & (ConsultantMessage.receiver_id == consultant_id)
                    & (ConsultantMessage.receiver_type == EntityType.consultant)
                )
            )
            .order_by(ConsultantMessage.timestamp.desc())
            .first()
        )

        # Count unread messages
        unread_count = (
            db.query(ConsultantMessage)
            .filter(
                (ConsultantMessage.sender_id == user_id)
                & (ConsultantMessage.sender_type == EntityType.user)
                & (ConsultantMessage.receiver_id == consultant_id)
                & (ConsultantMessage.receiver_type == EntityType.consultant)
                & (ConsultantMessage.status != MessageStatus.read)
            )
            .count()
        )

        conversations.append(
            {
                "user_id": user_id,
                "user_name": user.name,
                "last_message": ConsultantMessageResponse.from_orm(last_message),
                "unread_count": unread_count,
            }
        )

    return conversations


@router.patch("/{message_id}", response_model=ConsultantMessageResponse)
def update_message_status(
    message_id: str,
    status_update: ConsultantMessageUpdate,
    db: Session = Depends(get_db),
):
    """
    Update the status of a message (mark as delivered or read)
    """
    message = (
        db.query(ConsultantMessage).filter(ConsultantMessage.id == message_id).first()
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    message.status = status_update.status
    db.commit()
    db.refresh(message)
    return message
