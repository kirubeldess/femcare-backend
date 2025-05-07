import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models.message import Message, MessageStatus
from models.post import Post
from models.user import User
from pydantic_schemas.message import MessageCreate, MessageResponse, MessageUpdate

router = APIRouter()


@router.post("/", response_model=MessageResponse, status_code=201)
def send_message(
    message: MessageCreate, db: Session = Depends(get_db), sender_id: str = None
):
    """
    Send a new message. In a real app, sender_id would come from the authentication token.
    If post_id is provided, it should be a vent post to allow outreach.
    """
    # Validate sender exists
    if not db.query(User).filter(User.id == sender_id).first():
        raise HTTPException(status_code=404, detail="Sender user not found")

    # Validate receiver exists
    if not db.query(User).filter(User.id == message.receiver_id).first():
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

    # Create message
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


@router.get("/conversations/{user_id}", response_model=List[dict])
def get_conversations(user_id: str, db: Session = Depends(get_db)):
    """
    Get all conversations for a specific user (people they've messaged or who have messaged them)
    """
    # Find all distinct users this user has conversations with
    # This is a bit more complex in SQL and depends on the database, so here's a Python approach
    sent_messages = db.query(Message).filter(Message.sender_id == user_id).all()
    received_messages = db.query(Message).filter(Message.receiver_id == user_id).all()

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
    """
    messages = (
        db.query(Message)
        .filter(
            ((Message.sender_id == user_id) & (Message.receiver_id == partner_id))
            | ((Message.sender_id == partner_id) & (Message.receiver_id == user_id))
        )
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
