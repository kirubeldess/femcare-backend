import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from database import get_db
from models.post import Post, PostCategory as ModelPostCategory, ContentStatus
from models.user import User
from pydantic_schemas.post import (
    PostCreate,
    PostResponse,
    PostCategory as SchemaPostCategory,
)
from pydantic_schemas.notification import (
    NotificationCreate,
    RelatedContentType as NotificationRelatedContentType,
)
from models.notification import Notification
from utils.moderation import contains_profanity
from utils.auth import get_current_user
import logging

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_vent_post(
    post: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new vent post. Content will be pending approval if profanity is detected."""
    if post.category != SchemaPostCategory.vent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint is only for creating 'vent' posts. Use /community-content/ for other types.",
        )

    post_language = post.language if post.language else "en"
    title_to_check = post.title if post.title else ""

    # Profanity check determines initial status
    is_profane = False
    if await contains_profanity(
        title_to_check, language=post_language
    ) or await contains_profanity(post.content, language=post_language):
        is_profane = True
        logger.info(
            f"Vent post by user {current_user.email if not post.is_anonymous else 'anonymous'} flagged for profanity."
        )

    current_status = (
        ContentStatus.pending_approval if is_profane else ContentStatus.approved
    )

    db_post_user_id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    actual_is_anonymous = post.is_anonymous if post.is_anonymous is not None else False

    if actual_is_anonymous:
        db_post_user_id = current_user.id  # Store user_id even for anonymous posts
    else:
        db_post_user_id = current_user.id
        name = current_user.name
        email = current_user.email
        actual_is_anonymous = False

    db_post = Post(
        id=str(uuid.uuid4()),
        user_id=db_post_user_id,
        title=post.title,
        content=post.content,
        category=ModelPostCategory.vent,
        is_anonymous=actual_is_anonymous,
        name=name,
        email=email,
        status=current_status,
        location=post.location,
        language=post.language,
    )

    try:
        db.add(db_post)
        db.commit()

        if current_status == ContentStatus.pending_approval:
            # Construct a meaningful message for the notification
            title_for_message = (
                db_post.title
                if db_post.title and not db_post.is_anonymous
                else "Untitled Vent Post"
            )
            user_info_for_message = (
                f" by user {current_user.email}"
                if not db_post.is_anonymous and current_user
                else " (anonymous)"
            )
            if db_post.is_anonymous:
                notification_message = f"An anonymous vent post is pending approval."
            else:
                notification_message = f"Vent post titled '{title_for_message}'{user_info_for_message} is pending approval."

            # Ensure db_post.id is available and correct type for Notification model
            admin_notification = Notification(
                id=str(uuid.uuid4()),  # Notification needs its own ID
                message=notification_message,
                related_content_type=NotificationRelatedContentType.post.value,  # Use .value for enums going to SQLAlchemy model if it expects string
                related_content_id=db_post.id,
            )
            db.add(admin_notification)
            db.commit()  # Commit the notification
            logger.info(
                f"Admin notification created for pending vent post {db_post.id}"
            )

        db.refresh(db_post)
        # response_message is not used, PostResponse is returned directly
        return db_post
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create vent post: {str(e)}",
        )


@router.get("/", response_model=List[PostResponse])
def get_vent_posts(
    skip: int = 0,
    limit: int = 100,
    language: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all *approved* 'vent' posts with optional filtering by language."""
    query = db.query(Post).filter(
        Post.category == ModelPostCategory.vent, Post.status == ContentStatus.approved
    )

    if language:
        query = query.filter(Post.language == language)

    posts = query.order_by(Post.timestamp.desc()).offset(skip).limit(limit).all()
    return posts  # Pydantic conversion handles response structure


@router.get("/user/{user_id}", response_model=List[PostResponse])
def get_user_posts(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all posts by a specific user (includes all categories they authored and all statuses if they are viewing their own).
    If an admin views another user's posts, they see all statuses.
    Other users viewing someone else's posts would ideally only see approved (not implemented here yet).
    """
    query = db.query(Post).filter(Post.user_id == user_id)
    # If current user is not the user_id being queried and not an admin, only show approved posts
    if current_user.id != user_id and current_user.role != "admin":
        query = query.filter(Post.status == ContentStatus.approved)

    db_posts = query.order_by(Post.timestamp.desc()).all()
    return db_posts


@router.get("/{post_id}", response_model=PostResponse)
def get_vent_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Get a specific 'vent' post by ID. Only returns if approved, or if user is author/admin."""
    db_post = (
        db.query(Post)
        .filter(Post.id == post_id, Post.category == ModelPostCategory.vent)
        .first()
    )

    if not db_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vent post not found or not a vent type.",
        )

    # Check status for visibility
    if db_post.status != ContentStatus.approved:
        # Allow author or admin to see their non-approved posts
        is_author = current_user and db_post.user_id == current_user.id
        is_admin = current_user and current_user.role == "admin"
        if not (is_author or is_admin):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vent post not found or not yet approved.",
            )

    return db_post
