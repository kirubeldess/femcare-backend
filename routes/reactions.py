import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from fastapi import APIRouter, Depends, HTTPException, status

from database import get_db
from models.post import Post, Like, Comment, ContentStatus
from models.user import User  # Assuming you have a User model
from pydantic_schemas.like import LikeCreate, LikeResponse
from pydantic_schemas.comment import CommentCreate, CommentResponse
from pydantic_schemas.notification import (
    NotificationCreate,
    RelatedContentType as NotificationRelatedContentType,
)  # Added
from models.notification import Notification  # Added
from utils.auth import get_current_user  # For authenticated actions
from utils.moderation import contains_profanity  # Added
import logging  # Added

# Get a logger instance specific to this module
logger = logging.getLogger(__name__)  # Added

router = APIRouter()


# Helper function to get post or raise 404
def get_post_or_404(db: Session, post_id: str):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    return post


# --- Like Endpoints ---


@router.post(
    "/posts/{post_id}/like",
    response_model=LikeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_like(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = get_post_or_404(db, post_id)

    existing_like = (
        db.query(Like)
        .filter(Like.post_id == post_id, Like.user_id == current_user.id)
        .first()
    )
    if existing_like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has already liked this post",
        )

    new_like = Like(id=str(uuid.uuid4()), user_id=current_user.id, post_id=post_id)
    db.add(new_like)
    db.commit()
    db.refresh(new_like)
    return new_like


@router.delete("/posts/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def delete_like(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = get_post_or_404(db, post_id)

    like = (
        db.query(Like)
        .filter(Like.post_id == post_id, Like.user_id == current_user.id)
        .first()
    )
    if not like:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Like not found"
        )

    db.delete(like)
    db.commit()
    return None


@router.get("/posts/{post_id}/likes", response_model=List[LikeResponse])
def get_likes_for_post(post_id: str, db: Session = Depends(get_db)):
    post = get_post_or_404(db, post_id)
    return post.likes


# --- Comment Endpoints ---


@router.post(
    "/posts/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    post_id: str,
    comment_data: CommentCreate,
    current_user: Optional[User] = Depends(
        get_current_user
    ),  # Optional for anonymous comments
    db: Session = Depends(get_db),
):
    post = get_post_or_404(db, post_id)
    # Ensure only comments on approved posts are allowed, or handle differently if desired
    if post.status != ContentStatus.approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot comment on a post that is not yet approved.",
        )

    comment_language = (
        "en"  # Defaulting, consider passing explicitly or deriving from post
    )

    # Profanity check determines initial status for the comment
    is_profane = False
    if await contains_profanity(comment_data.content, language=comment_language):
        is_profane = True
        user_identifier = "anonymous"  # Default for anonymous or no current_user
        if current_user and not comment_data.is_anonymous:
            user_identifier = current_user.email
        elif (
            comment_data.user_id and not comment_data.is_anonymous
        ):  # If admin posts on behalf for a user
            # Potentially fetch user email if needed for log, or use user_id
            user_identifier = f"user_id:{comment_data.user_id}"
        logger.info(
            f"Comment by {user_identifier} on post {post_id} flagged for profanity."
        )

    current_status = (
        ContentStatus.pending_approval if is_profane else ContentStatus.approved
    )

    user_id_to_set = None
    if comment_data.is_anonymous and comment_data.user_id:
        pass
    elif not comment_data.is_anonymous and current_user:
        user_id_to_set = current_user.id
    elif comment_data.user_id:
        user_id_to_set = comment_data.user_id

    if not comment_data.is_anonymous and not user_id_to_set:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User must be authenticated to post non-anonymous comments or provide a user_id",
        )

    new_comment = Comment(
        id=str(uuid.uuid4()),
        user_id=user_id_to_set if not comment_data.is_anonymous else None,
        post_id=post_id,
        parent_comment_id=comment_data.parent_comment_id,
        content=comment_data.content,
        is_anonymous=comment_data.is_anonymous,
        status=current_status,  # Set status based on profanity check
    )
    try:
        db.add(new_comment)
        db.commit()  # Commit comment first

        if current_status == ContentStatus.pending_approval:
            user_identifier_for_message = "anonymous user"
            if new_comment.user_id and not new_comment.is_anonymous:
                # Attempt to get user email for a more descriptive message if user is not anonymous
                comment_author = (
                    db.query(User).filter(User.id == new_comment.user_id).first()
                )
                if comment_author:
                    user_identifier_for_message = f"user {comment_author.email}"
                else:
                    user_identifier_for_message = f"user ID {new_comment.user_id}"  # Fallback if user not found, though unlikely

            notification_message = f"Comment by {user_identifier_for_message} on post {post_id} is pending approval."

            admin_notification = Notification(
                id=str(uuid.uuid4()),  # Notification needs its own ID
                message=notification_message,
                related_content_type=NotificationRelatedContentType.comment.value,  # Use .value for enum
                related_content_id=new_comment.id,
            )
            db.add(admin_notification)
            db.commit()  # Commit notification
            logger.info(
                f"Admin notification created for pending comment {new_comment.id} on post {post_id}"
            )

        db.refresh(new_comment)
        # Similar to posts, client should check status. No custom message field in CommentResponse by default.
        return new_comment  # Pydantic will convert, CommentResponse includes status
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create comment: {str(e)}",
        )


@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
def get_comments_for_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Get all *approved* comments for a post. Allows user to see their own pending/rejected comments on a post."""
    post = get_post_or_404(db, post_id)
    if post.status != ContentStatus.approved:
        # If post itself is not approved, generally no comments should be shown or it's a 404 for the post.
        # Assuming get_post_or_404 would have handled post visibility for non-admins.
        # If user is admin or author of post, they might see the post even if not approved.
        is_post_author = current_user and post.user_id == current_user.id
        is_admin = current_user and current_user.role == "admin"
        if not (is_post_author or is_admin) and post.status != ContentStatus.approved:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found or not yet approved.",
            )

    # Base query for comments on the post
    query = db.query(Comment).filter(
        Comment.post_id == post_id, Comment.parent_comment_id == None
    )

    # Filter by status: show approved, OR if current_user is comment author, show their own regardless of status.
    if current_user:
        query = query.filter(
            or_(
                Comment.status == ContentStatus.approved,
                Comment.user_id
                == current_user.id,  # User can see their own comments (any status)
            )
        )
        # Admins see all statuses
        if current_user.role == "admin":
            query = db.query(Comment).filter(
                Comment.post_id == post_id, Comment.parent_comment_id == None
            )  # Reset filters for admin
    else:  # No current user, only show approved
        query = query.filter(Comment.status == ContentStatus.approved)

    comments = query.order_by(Comment.timestamp.asc()).all()
    return comments


@router.get("/comments/{comment_id}/replies", response_model=List[CommentResponse])
def get_replies_for_comment(
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Get all *approved* replies for a comment. Allows user to see their own pending/rejected replies."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )

    # Check parent comment visibility before showing replies
    can_view_parent = False
    if comment.status == ContentStatus.approved:
        can_view_parent = True
    elif current_user:
        if comment.user_id == current_user.id or current_user.role == "admin":
            can_view_parent = True

    if not can_view_parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent comment not found or not accessible.",
        )

    # Base query for replies
    query = db.query(Comment).filter(Comment.parent_comment_id == comment_id)

    # Filter by status for replies
    if current_user:
        query = query.filter(
            or_(
                Comment.status == ContentStatus.approved,
                Comment.user_id
                == current_user.id,  # User can see their own replies (any status)
            )
        )
        if current_user.role == "admin":  # Admins see all statuses for replies
            query = db.query(Comment).filter(Comment.parent_comment_id == comment_id)
    else:  # No current user, only show approved replies
        query = query.filter(Comment.status == ContentStatus.approved)

    replies = query.order_by(Comment.timestamp.asc()).all()
    return replies


# Optional: Add endpoints to update/delete comments if needed, considering ownership/moderation rules.
# For example:
# @router.put("/comments/{comment_id}", response_model=CommentResponse)
# def update_comment(comment_id: str, comment_data: CommentUpdate, ...):
#     pass

# @router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_comment(comment_id: str, ...):
#     pass
