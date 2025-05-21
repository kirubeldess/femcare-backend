import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models.message import Message, MessageStatus
from models.post import Post
from models.user import User
from pydantic_schemas.message import (
    MessageCreate,
    MessageResponse,
    MessageUpdate,
    MessageRequestResponse,
)

router = APIRouter()

# Define status values as constants to avoid enum reference issues
APPROVED_STATUSES = ["sent", "delivered", "read", "accepted"]
REQUEST_STATUS = "requested"
REJECTED_STATUS = "rejected"


@router.post("/", response_model=MessageResponse, status_code=201)
def send_message(
    message: MessageCreate, db: Session = Depends(get_db), sender_id: str = None
):
    """
    Send a new message. In a real app, sender_id would come from the authentication token.
    If post_id is provided, it should be a vent post to allow outreach.

    The system automatically detects if this is an initial message between users:
    - For new conversations starting from a vent post, a message request is created
    - For existing conversations, a regular message is sent
    """
    # Validate sender exists
    if not db.query(User).filter(User.id == sender_id).first():
        raise HTTPException(status_code=404, detail="Sender user not found")

    # Validate receiver exists
    receiver = db.query(User).filter(User.id == message.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver user not found")

    # Validate post_id if provided
    if message.post_id:
        post = db.query(Post).filter(Post.id == message.post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        if post.category.value != "vent":
            raise HTTPException(
                status_code=400, detail="Messages can only be linked to vent posts"
            )

        # Check if post owner is the receiver
        if post.user_id != message.receiver_id:
            raise HTTPException(
                status_code=400, detail="Receiver must be the vent post owner"
            )

    # Check if there's prior communication between these users using string values
    prior_communication = (
        db.query(Message)
        .filter(
            (
                (Message.sender_id == sender_id)
                & (Message.receiver_id == message.receiver_id)
                & (Message.status.in_(APPROVED_STATUSES))
            )
            | (
                (Message.sender_id == message.receiver_id)
                & (Message.receiver_id == sender_id)
                & (Message.status.in_(APPROVED_STATUSES))
            )
        )
        .first()
    )

    # If message has post_id and no prior communication, create a message request
    if message.post_id and not prior_communication:
        # Create message request
        db_message = Message(
            id=str(uuid.uuid4()),
            sender_id=sender_id,
            receiver_id=message.receiver_id,
            post_id=message.post_id,
            content=message.content,
            status=MessageStatus.requested,  # Set status as requested
        )
    else:
        # Regular message or the conversation has been previously approved
        db_message = Message(
            id=str(uuid.uuid4()),
            sender_id=sender_id,
            receiver_id=message.receiver_id,
            post_id=message.post_id,
            content=message.content,
            status=MessageStatus.sent,
        )

    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


@router.get("/requests/{user_id}", response_model=List[MessageResponse])
def get_message_requests(user_id: str, db: Session = Depends(get_db)):
    """
    Get all pending message requests for a user (vent owner)
    """
    requests = (
        db.query(Message)
        .filter(
            (Message.receiver_id == user_id)
            & (Message.status == MessageStatus.requested)
        )
        .order_by(Message.timestamp.desc())
        .all()
    )

    return requests


@router.post("/requests/{request_id}/respond", response_model=MessageResponse)
def respond_to_message_request(
    request_id: str,
    response: MessageUpdate,
    db: Session = Depends(get_db),
    user_id: str = None,
):
    """
    Respond to a message request (accept or reject)
    """
    # Get the message request
    request = db.query(Message).filter(Message.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Message request not found")

    # Verify the receiver is responding
    if request.receiver_id != user_id:
        raise HTTPException(
            status_code=403, detail="Only the message receiver can respond to requests"
        )

    # Verify this is a request message
    if request.status != MessageStatus.requested:
        raise HTTPException(
            status_code=400, detail="This is not a pending message request"
        )

    # Update request status (accept or reject)
    if response.status not in [MessageStatus.accepted, MessageStatus.rejected]:
        raise HTTPException(
            status_code=400, detail="Status must be 'accepted' or 'rejected'"
        )

    request.status = response.status
    db.commit()
    db.refresh(request)
    return request


@router.get("/conversations/{user_id}", response_model=List[dict])
def get_conversations(user_id: str, db: Session = Depends(get_db)):
    """
    Get all conversations for a specific user (people they've messaged or who have messaged them)
    Only includes approved conversations (accepted requests or direct messages)
    """
    # Find all distinct users this user has conversations with
    # Exclude rejected or pending requests
    sent_messages = (
        db.query(Message)
        .filter(
            (Message.sender_id == user_id) & (Message.status.in_(APPROVED_STATUSES))
        )
        .all()
    )

    received_messages = (
        db.query(Message)
        .filter(
            (Message.receiver_id == user_id) & (Message.status.in_(APPROVED_STATUSES))
        )
        .all()
    )

    # Get unique conversation partners
    conversation_partners = set()
    for msg in sent_messages:
        conversation_partners.add(msg.receiver_id)
    for msg in received_messages:
        conversation_partners.add(msg.sender_id)

    # Get last message for each conversation
    conversations = []
    for partner_id in conversation_partners:
        last_message = (
            db.query(Message)
            .filter(
                ((Message.sender_id == user_id) & (Message.receiver_id == partner_id))
                | ((Message.sender_id == partner_id) & (Message.receiver_id == user_id))
            )
            .filter(Message.status.in_(APPROVED_STATUSES))
            .order_by(Message.timestamp.desc())
            .first()
        )

        partner = db.query(User).filter(User.id == partner_id).first()

        conversations.append(
            {
                "partner_id": partner_id,
                "partner_name": partner.name if partner else "Unknown User",
                "last_message": MessageResponse.from_orm(last_message),
                "unread_count": db.query(Message)
                .filter(
                    (Message.sender_id == partner_id)
                    & (Message.receiver_id == user_id)
                    & (Message.status != MessageStatus.read)
                )
                .count(),
            }
        )

    return conversations


@router.get("/thread/{user_id}/{partner_id}", response_model=List[MessageResponse])
def get_message_thread(user_id: str, partner_id: str, db: Session = Depends(get_db)):
    """
    Get all messages between two users
    Only includes messages from approved conversations
    """
    # Check if these users have an approved conversation
    has_conversation = (
        db.query(Message)
        .filter(
            (
                ((Message.sender_id == user_id) & (Message.receiver_id == partner_id))
                | ((Message.sender_id == partner_id) & (Message.receiver_id == user_id))
            )
            & (Message.status.in_(APPROVED_STATUSES))
        )
        .first()
        is not None
    )

    if not has_conversation:
        raise HTTPException(
            status_code=403,
            detail="No approved conversation exists between these users",
        )

    messages = (
        db.query(Message)
        .filter(
            ((Message.sender_id == user_id) & (Message.receiver_id == partner_id))
            | ((Message.sender_id == partner_id) & (Message.receiver_id == user_id))
        )
        .filter(Message.status.in_(APPROVED_STATUSES))
        .order_by(Message.timestamp)
        .all()
    )

    # Mark messages as read if the user is the receiver
    for msg in messages:
        if msg.receiver_id == user_id and msg.status != MessageStatus.read:
            msg.status = MessageStatus.read

    db.commit()
    return messages


@router.patch("/{message_id}", response_model=MessageResponse)
def update_message_status(
    message_id: str, status_update: MessageUpdate, db: Session = Depends(get_db)
):
    """
    Update the status of a message (mark as delivered or read)
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    message.status = status_update.status
    db.commit()
    db.refresh(message)
    return message


@router.get("/can-message/{user_id}/{vent_owner_id}", response_model=dict)
def check_can_message(user_id: str, vent_owner_id: str, db: Session = Depends(get_db)):
    """
    Check if a user can directly message a vent owner or needs to send a request first
    Returns the messaging status and any relevant request info
    """
    # Check if there's prior approved communication
    prior_communication = (
        db.query(Message)
        .filter(
            (
                (
                    (Message.sender_id == user_id)
                    & (Message.receiver_id == vent_owner_id)
                )
                | (
                    (Message.sender_id == vent_owner_id)
                    & (Message.receiver_id == user_id)
                )
            )
            & (Message.status.in_(APPROVED_STATUSES))
        )
        .first()
    )

    # Check if there's a pending request
    pending_request = (
        db.query(Message)
        .filter(
            (Message.sender_id == user_id)
            & (Message.receiver_id == vent_owner_id)
            & (Message.status == MessageStatus.requested)
        )
        .first()
    )

    # Check if there's a rejected request
    rejected_request = (
        db.query(Message)
        .filter(
            (Message.sender_id == user_id)
            & (Message.receiver_id == vent_owner_id)
            & (Message.status == MessageStatus.rejected)
        )
        .first()
    )

    result = {
        "can_message_directly": prior_communication is not None,
        "pending_request": pending_request is not None,
        "request_rejected": rejected_request is not None,
        "request_id": pending_request.id if pending_request else None,
    }

    return result


@router.get("/vent-outreach/{post_id}", response_model=List[MessageResponse])
def get_vent_outreach_messages(post_id: str, db: Session = Depends(get_db)):
    """
    Get all messages related to a specific vent post (for outreach)
    """
    # Verify the post exists and is a vent
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.category.value != "vent":
        raise HTTPException(
            status_code=400, detail="Only vent posts can have outreach messages"
        )

    messages = (
        db.query(Message)
        .filter(Message.post_id == post_id)
        .order_by(Message.timestamp)
        .all()
    )
    return messages
