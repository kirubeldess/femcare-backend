import uuid
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, Security, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from models.message import (
    MessageRequest,
    MessageRequestStatus,
    Conversation,
    Message,
    MessageStatus,
)
from models.post import Post
from models.user import User
from pydantic_schemas.message import (
    MessageRequestCreate,
    MessageRequestResponse,
    MessageRequestUpdate,
    MessageResponse,
    MessageCreate,
    MessageUpdate,
    ConversationResponse,
    ConversationWithMessages,
    NotificationResponse,
)
from utils.auth import get_admin_user
import json
import logging
from datetime import datetime
from models.notification import Notification
from models.notification import NotificationContentType

# Setup logger
logger = logging.getLogger(__name__)

router = APIRouter()


def send_notification(
    db: Session,
    user_id: str,
    message: str,
    related_content_type: NotificationContentType = None,
    related_content_id: str = None,
):
    """
    Store a notification in the database for a user.
    """
    notification = Notification(
        id=str(uuid.uuid4()),
        message=message,
        is_read=False,
        related_content_type=related_content_type,
        related_content_id=related_content_id,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


# Message Request Endpoints


@router.post("/requests", response_model=MessageRequestResponse, status_code=201)
async def create_message_request(
    request: MessageRequestCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    sender_id: str = None,
):
    """
    Create a new message request from a user to a vent post owner.
    This is the initial step in the messaging workflow.
    """
    # Validate sender exists
    if not db.query(User).filter(User.id == sender_id).first():
        raise HTTPException(status_code=404, detail="Sender user not found")

    # Validate receiver exists
    receiver = db.query(User).filter(User.id == request.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver user not found")

    # Validate post exists and is a vent post
    post = db.query(Post).filter(Post.id == request.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.category.value != "vent":
        raise HTTPException(
            status_code=400, detail="Message requests can only be linked to vent posts"
        )

    # Verify the receiver is the post owner
    if post.user_id != request.receiver_id:
        raise HTTPException(
            status_code=400, detail="Receiver must be the vent post owner"
        )

    # Check if a request already exists
    existing_request = (
        db.query(MessageRequest)
        .filter(
            (MessageRequest.sender_id == sender_id)
            & (MessageRequest.receiver_id == request.receiver_id)
            & (MessageRequest.post_id == request.post_id)
            & (MessageRequest.status == MessageRequestStatus.pending)
        )
        .first()
    )

    if existing_request:
        raise HTTPException(
            status_code=400, detail="A pending request already exists for this post"
        )

    # Check if a conversation already exists between these users
    conversation = (
        db.query(Conversation)
        .filter(
            (
                (Conversation.user1_id == sender_id)
                & (Conversation.user2_id == request.receiver_id)
            )
            | (
                (Conversation.user1_id == request.receiver_id)
                & (Conversation.user2_id == sender_id)
            )
        )
        .first()
    )

    if conversation:
        raise HTTPException(
            status_code=400, detail="A conversation already exists between these users"
        )

    # Create message request
    db_request = MessageRequest(
        id=str(uuid.uuid4()),
        sender_id=sender_id,
        receiver_id=request.receiver_id,
        post_id=request.post_id,
        initial_message=request.initial_message,
        status=MessageRequestStatus.pending,
    )

    db.add(db_request)
    db.commit()
    db.refresh(db_request)

    # Store notification for vent owner about new message request
    send_notification(
        db=db,
        user_id=request.receiver_id,
        message=f"Someone wants to talk about your vent post",
        related_content_type=NotificationContentType.post,
        related_content_id=request.post_id,
    )

    return db_request


@router.get("/requests/received/{user_id}", response_model=List[MessageRequestResponse])
def get_received_message_requests(user_id: str, db: Session = Depends(get_db)):
    """
    Get all message requests received by a user (vent post owner)
    """
    requests = (
        db.query(MessageRequest)
        .filter(
            (MessageRequest.receiver_id == user_id)
            & (MessageRequest.status == MessageRequestStatus.pending)
        )
        .order_by(MessageRequest.timestamp.desc())
        .all()
    )

    return requests


@router.get("/requests/sent/{user_id}", response_model=List[MessageRequestResponse])
def get_sent_message_requests(user_id: str, db: Session = Depends(get_db)):
    """
    Get all message requests sent by a user
    """
    requests = (
        db.query(MessageRequest)
        .filter(MessageRequest.sender_id == user_id)
        .order_by(MessageRequest.timestamp.desc())
        .all()
    )

    return requests


@router.post("/requests/{request_id}/respond", response_model=NotificationResponse)
async def respond_to_message_request(
    request_id: str,
    response: MessageRequestUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: str = None,
):
    """
    Respond to a message request (accept or reject)
    """
    # Get the message request
    message_request = (
        db.query(MessageRequest).filter(MessageRequest.id == request_id).first()
    )
    if not message_request:
        raise HTTPException(status_code=404, detail="Message request not found")

    # Verify the receiver is responding
    if message_request.receiver_id != user_id:
        raise HTTPException(
            status_code=403, detail="Only the message receiver can respond to requests"
        )

    # Verify this is a pending request
    if message_request.status != MessageRequestStatus.pending:
        raise HTTPException(
            status_code=400, detail="This request has already been processed"
        )

    # Update request status (accept or reject)
    if response.status not in [
        MessageRequestStatus.accepted,
        MessageRequestStatus.rejected,
    ]:
        raise HTTPException(
            status_code=400, detail="Status must be 'accepted' or 'rejected'"
        )

    message_request.status = response.status
    db.commit()

    # If accepted, create a conversation
    if response.status == MessageRequestStatus.accepted:
        # Create conversation
        conversation = Conversation(
            id=str(uuid.uuid4()),
            user1_id=message_request.sender_id,
            user2_id=message_request.receiver_id,
            request_id=message_request.id,
        )

        db.add(conversation)

        # Add the initial message to the conversation
        initial_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            sender_id=message_request.sender_id,
            content=message_request.initial_message,
            status=MessageStatus.sent,
        )

        db.add(initial_message)
        db.commit()

        # Store notification for sender that their request was accepted
        send_notification(
            db=db,
            user_id=message_request.sender_id,
            message="Your message request was accepted! You can now start chatting.",
            related_content_type=NotificationContentType.post,
            related_content_id=message_request.post_id,
        )

        return {
            "message": "Request accepted, conversation created",
            "type": "success",
            "data": {
                "conversation_id": conversation.id,
                "request_id": request_id,
                "status": response.status,
            },
        }
    else:
        # Store notification for sender that their request was rejected
        send_notification(
            db=db,
            user_id=message_request.sender_id,
            message="Your message request was declined.",
            related_content_type=NotificationContentType.post,
            related_content_id=message_request.post_id,
        )

        return {
            "message": "Request rejected",
            "type": "info",
            "data": {"request_id": request_id, "status": response.status},
        }


# Conversation and Message Endpoints


@router.get("/conversations/{user_id}", response_model=List[ConversationWithMessages])
def get_conversations(user_id: str, db: Session = Depends(get_db)):
    """
    Get all conversations for a user with the most recent message
    """
    conversations = (
        db.query(Conversation)
        .filter((Conversation.user1_id == user_id) | (Conversation.user2_id == user_id))
        .all()
    )

    result = []
    for conversation in conversations:
        # Determine the partner ID
        partner_id = (
            conversation.user1_id
            if conversation.user2_id == user_id
            else conversation.user2_id
        )

        # Get partner name
        partner = db.query(User).filter(User.id == partner_id).first()
        partner_name = partner.name if partner else "Unknown User"

        # Get the most recent message
        last_message = (
            db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .order_by(Message.timestamp.desc())
            .first()
        )

        # Count unread messages
        unread_count = (
            db.query(Message)
            .filter(
                (Message.conversation_id == conversation.id)
                & (Message.sender_id == partner_id)
                & (Message.status != MessageStatus.read)
            )
            .count()
        )

        # Create the response object
        conv_with_messages = ConversationWithMessages(
            **conversation.__dict__,
            partner_name=partner_name,
            unread_count=unread_count,
            messages=[last_message] if last_message else [],
        )

        result.append(conv_with_messages)

    # Sort by most recent message
    result.sort(
        key=lambda x: x.messages[0].timestamp if x.messages else x.created_at,
        reverse=True,
    )

    return result


@router.get(
    "/conversations/{conversation_id}/messages", response_model=List[MessageResponse]
)
def get_conversation_messages(
    conversation_id: str, db: Session = Depends(get_db), user_id: str = None
):
    """
    Get all messages in a conversation
    """
    # Verify the conversation exists
    conversation = (
        db.query(Conversation).filter(Conversation.id == conversation_id).first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify the user is part of the conversation
    if user_id not in [conversation.user1_id, conversation.user2_id]:
        raise HTTPException(
            status_code=403, detail="You are not authorized to view this conversation"
        )

    # Get all messages
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.timestamp)
        .all()
    )

    # Mark messages as read if the user is the receiver
    for msg in messages:
        if msg.sender_id != user_id and msg.status != MessageStatus.read:
            msg.status = MessageStatus.read

    db.commit()

    return messages


@router.post(
    "/conversations/{conversation_id}/messages", response_model=MessageResponse
)
async def send_message(
    conversation_id: str,
    message: MessageCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    sender_id: str = None,
):
    """
    Send a message in an existing conversation
    """
    # Verify the conversation exists
    conversation = (
        db.query(Conversation).filter(Conversation.id == conversation_id).first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify the sender is part of the conversation
    if sender_id not in [conversation.user1_id, conversation.user2_id]:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to send messages in this conversation",
        )

    # Create the message
    db_message = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        sender_id=sender_id,
        content=message.content,
        status=MessageStatus.sent,
    )

    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    # Determine the recipient
    recipient_id = (
        conversation.user1_id
        if sender_id == conversation.user2_id
        else conversation.user2_id
    )

    # Store notification for recipient
    send_notification(
        db=db,
        user_id=recipient_id,
        message="You have a new message",
        related_content_type=NotificationContentType.post,
        related_content_id=conversation.request_id,  # or conversation_id if preferred
    )

    return db_message


@router.patch("/messages/{message_id}", response_model=MessageResponse)
def update_message_status(
    message_id: str,
    status_update: MessageUpdate,
    db: Session = Depends(get_db),
    user_id: str = None,
):
    """
    Update the status of a message (mark as delivered or read)
    """
    # Get the message
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Get the conversation
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == message.conversation_id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify the user is part of the conversation
    if user_id not in [conversation.user1_id, conversation.user2_id]:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to update messages in this conversation",
        )

    # Only the recipient can update the status
    if message.sender_id == user_id:
        raise HTTPException(
            status_code=400, detail="You cannot update the status of your own messages"
        )

    # Update the status
    message.status = status_update.status
    db.commit()
    db.refresh(message)

    return message


# Admin-only endpoints


@router.delete("/requests/{request_id}", status_code=204)
def delete_message_request(
    request_id: str,
    db: Session = Depends(get_db),
    admin_user: dict = Security(get_admin_user),
):
    """
    Delete a message request. Admin-only endpoint.
    """
    request = db.query(MessageRequest).filter(MessageRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Message request not found")

    # Check if there's a conversation linked to this request
    conversation = (
        db.query(Conversation).filter(Conversation.request_id == request_id).first()
    )
    if conversation:
        raise HTTPException(
            status_code=400, detail="Cannot delete request with an active conversation"
        )

    db.delete(request)
    db.commit()

    return {"status": "success", "detail": "Message request deleted"}


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    admin_user: dict = Security(get_admin_user),
):
    """
    Delete a conversation and all its messages. Admin-only endpoint.
    """
    conversation = (
        db.query(Conversation).filter(Conversation.id == conversation_id).first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Delete all messages in the conversation
    db.query(Message).filter(Message.conversation_id == conversation_id).delete()

    # Delete the conversation
    db.delete(conversation)
    db.commit()

    return {"status": "success", "detail": "Conversation and all messages deleted"}


@router.delete("/messages/{message_id}", status_code=204)
def delete_message(
    message_id: str,
    db: Session = Depends(get_db),
    admin_user: dict = Security(get_admin_user),
):
    """
    Delete a specific message. Admin-only endpoint.
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    db.delete(message)
    db.commit()

    return {"status": "success", "detail": "Message deleted"}


@router.delete("/user/{user_id}/all", status_code=204)
def delete_user_data(
    user_id: str,
    db: Session = Depends(get_db),
    admin_user: dict = Security(get_admin_user),
):
    """
    Delete all message requests, conversations, and messages for a user.
    Admin-only endpoint, useful for GDPR compliance.
    """
    # Delete all messages in conversations where user is a participant
    conversations = (
        db.query(Conversation)
        .filter((Conversation.user1_id == user_id) | (Conversation.user2_id == user_id))
        .all()
    )

    for conversation in conversations:
        # Delete all messages in the conversation
        db.query(Message).filter(Message.conversation_id == conversation.id).delete()

        # Delete the conversation
        db.delete(conversation)

    # Delete all message requests sent or received by the user
    db.query(MessageRequest).filter(
        (MessageRequest.sender_id == user_id) | (MessageRequest.receiver_id == user_id)
    ).delete()

    db.commit()

    return {
        "status": "success",
        "detail": f"All messaging data deleted for user {user_id}",
    }
