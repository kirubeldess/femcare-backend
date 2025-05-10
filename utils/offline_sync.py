# utils/offline_sync.py
"""
Utilities for handling offline data synchronization.
This module provides functions to help mobile clients sync data that was created
while the device was offline.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.post import Post
from models.sos_log import SOSLog
from models.message import Message, MessageStatus
from models.ai_consultation import AIConsultation
from utils.gemini_helper import get_consultation_response

# Get logger
logger = logging.getLogger(__name__)


async def sync_offline_posts(
    posts_data: List[Dict[str, Any]], user_id: str, db: Session
) -> List[Dict[str, Any]]:
    """
    Synchronize posts that were created while the user was offline.

    Args:
        posts_data: List of post data dictionaries
        user_id: The authenticated user's ID
        db: Database session

    Returns:
        List of processed post objects with server IDs
    """
    results = []

    for post_data in posts_data:
        try:
            # Generate a new server ID
            server_id = str(uuid.uuid4())

            # Create the post object
            db_post = Post(
                id=server_id,
                user_id=None if post_data.get("is_anonymous", False) else user_id,
                title=post_data.get("title"),
                content=post_data.get("content"),
                category=post_data.get("category"),
                is_anonymous=post_data.get("is_anonymous", False),
                location=post_data.get("location"),
                language=post_data.get("language", "en"),
            )

            # Set the timestamp if provided
            if "timestamp" in post_data and post_data["timestamp"]:
                try:
                    db_post.timestamp = datetime.fromisoformat(
                        post_data["timestamp"].replace("Z", "+00:00")
                    )
                except ValueError:
                    # If timestamp format is invalid, use current time (default)
                    pass

            # Save to database
            db.add(db_post)
            db.commit()
            db.refresh(db_post)

            # Add to results with client_id for mapping
            results.append(
                {
                    "client_id": post_data.get("client_id"),  # Original ID from client
                    "server_id": server_id,  # New server ID
                    "synced": True,
                }
            )

        except Exception as e:
            logger.error(f"Error syncing offline post: {str(e)}")
            # Add failed result
            results.append(
                {
                    "client_id": post_data.get("client_id"),
                    "synced": False,
                    "error": str(e),
                }
            )

    return results


async def sync_offline_messages(
    messages_data: List[Dict[str, Any]], user_id: str, db: Session
) -> List[Dict[str, Any]]:
    """
    Synchronize messages that were created while the user was offline.

    Args:
        messages_data: List of message data dictionaries
        user_id: The authenticated user's ID
        db: Database session

    Returns:
        List of processed message objects with server IDs
    """
    results = []

    for message_data in messages_data:
        try:
            # Generate a new server ID
            server_id = str(uuid.uuid4())

            # Create the message object
            db_message = Message(
                id=server_id,
                sender_id=user_id,
                receiver_id=message_data.get("receiver_id"),
                post_id=message_data.get("post_id"),
                content=message_data.get("content"),
                status=MessageStatus.sent,
            )

            # Set the timestamp if provided
            if "timestamp" in message_data and message_data["timestamp"]:
                try:
                    db_message.timestamp = datetime.fromisoformat(
                        message_data["timestamp"].replace("Z", "+00:00")
                    )
                except ValueError:
                    # If timestamp format is invalid, use current time (default)
                    pass

            # Save to database
            db.add(db_message)
            db.commit()
            db.refresh(db_message)

            # Add to results with client_id for mapping
            results.append(
                {
                    "client_id": message_data.get(
                        "client_id"
                    ),  # Original ID from client
                    "server_id": server_id,  # New server ID
                    "synced": True,
                }
            )

        except Exception as e:
            logger.error(f"Error syncing offline message: {str(e)}")
            # Add failed result
            results.append(
                {
                    "client_id": message_data.get("client_id"),
                    "synced": False,
                    "error": str(e),
                }
            )

    return results


async def sync_offline_consultations(
    consultations_data: List[Dict[str, Any]],
    user_id: str,
    user_language: str,
    db: Session,
) -> List[Dict[str, Any]]:
    """
    Synchronize AI consultations that were created while the user was offline.

    Args:
        consultations_data: List of consultation data dictionaries
        user_id: The authenticated user's ID
        user_language: The user's preferred language
        db: Database session

    Returns:
        List of processed consultation objects with server IDs
    """
    results = []

    for consultation_data in consultations_data:
        try:
            # Generate a new server ID
            server_id = str(uuid.uuid4())

            # Create the consultation object
            db_consultation = AIConsultation(
                id=server_id,
                user_id=user_id,
                consultation_type=consultation_data.get("consultation_type"),
                symptoms=consultation_data.get("symptoms"),
                status="pending",
            )

            # Set the timestamp if provided
            if "timestamp" in consultation_data and consultation_data["timestamp"]:
                try:
                    db_consultation.timestamp = datetime.fromisoformat(
                        consultation_data["timestamp"].replace("Z", "+00:00")
                    )
                except ValueError:
                    # If timestamp format is invalid, use current time (default)
                    pass

            # Save to database
            db.add(db_consultation)
            db.commit()
            db.refresh(db_consultation)

            # Get AI response
            try:
                ai_response = await get_consultation_response(
                    consultation_data.get("consultation_type"),
                    consultation_data.get("symptoms"),
                    language=user_language,
                )

                # Update with response
                db_consultation.ai_response = ai_response
                db_consultation.status = "completed"

                db.commit()
                db.refresh(db_consultation)

            except Exception as e:
                logger.error(f"Error generating AI response: {str(e)}")
                # Continue with failed AI response but successful sync

            # Add to results with client_id for mapping
            results.append(
                {
                    "client_id": consultation_data.get(
                        "client_id"
                    ),  # Original ID from client
                    "server_id": server_id,  # New server ID
                    "synced": True,
                    "ai_response": db_consultation.ai_response,
                    "status": db_consultation.status,
                }
            )

        except Exception as e:
            logger.error(f"Error syncing offline consultation: {str(e)}")
            # Add failed result
            results.append(
                {
                    "client_id": consultation_data.get("client_id"),
                    "synced": False,
                    "error": str(e),
                }
            )

    return results


# Create a route to batch process offline data
async def process_offline_data(
    offline_data: Dict[str, List[Dict[str, Any]]],
    user_id: str,
    user_language: str,
    db: Session,
) -> Dict[str, Any]:
    """
    Process a batch of offline data from a mobile client.

    Args:
        offline_data: Dictionary with lists of offline data by type
        user_id: The authenticated user's ID
        user_language: The user's preferred language
        db: Database session

    Returns:
        Dictionary with sync results by data type
    """
    results = {"posts": [], "messages": [], "consultations": [], "sos_alerts": []}

    # Process posts
    if "posts" in offline_data and offline_data["posts"]:
        results["posts"] = await sync_offline_posts(offline_data["posts"], user_id, db)

    # Process messages
    if "messages" in offline_data and offline_data["messages"]:
        results["messages"] = await sync_offline_messages(
            offline_data["messages"], user_id, db
        )

    # Process consultations
    if "consultations" in offline_data and offline_data["consultations"]:
        results["consultations"] = await sync_offline_consultations(
            offline_data["consultations"], user_id, user_language, db
        )

    # Process SOS alerts (handled separately for immediate response)

    return results
