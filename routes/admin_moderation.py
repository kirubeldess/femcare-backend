# routes/admin_moderation.py
import logging
from typing import List, Union, Literal, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models.user import User
from models.post import (
    Post,
    Comment,
    ContentStatus,
    ContentStatus as ModelContentStatus,
)
from pydantic_schemas.post import PostResponse
from pydantic_schemas.comment import CommentResponse
from utils.auth import get_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/moderation",
    tags=["Admin Moderation"],
    dependencies=[Depends(get_admin_user)],
)


class ContentItemResponse(BaseModel):
    id: str
    content_type: Literal["post", "comment"]
    preview: Optional[str] = None  # e.g., first 100 chars of post/comment content
    status: ModelContentStatus
    user_id: Optional[str] = None
    timestamp: datetime


@router.get("/pending", response_model=List[ContentItemResponse])
def get_pending_content(db: Session = Depends(get_db)):
    """Get all posts and comments pending admin approval."""
    pending_posts = (
        db.query(Post).filter(Post.status == ContentStatus.pending_approval).all()
    )
    pending_comments = (
        db.query(Comment).filter(Comment.status == ContentStatus.pending_approval).all()
    )

    response_items = []
    for post in pending_posts:
        response_items.append(
            ContentItemResponse(
                id=post.id,
                content_type="post",
                preview=post.content[:100] if post.content else "",
                status=post.status,
                user_id=post.user_id,
                timestamp=post.timestamp,
            )
        )
    for comment in pending_comments:
        response_items.append(
            ContentItemResponse(
                id=comment.id,
                content_type="comment",
                preview=comment.content[:100] if comment.content else "",
                status=comment.status,
                user_id=comment.user_id,
                timestamp=comment.timestamp,
            )
        )

    return sorted(response_items, key=lambda item: item.timestamp, reverse=True)


@router.put(
    "/{content_type}/{content_id}/approve",
    response_model=Union[PostResponse, CommentResponse],
)
def approve_content(
    content_type: Literal["post", "comment"] = Path(
        ..., title="The type of content to approve"
    ),
    content_id: str = Path(..., title="The ID of the content to approve"),
    db: Session = Depends(get_db),
):
    """Approve a post or comment that is pending approval."""
    item_to_approve = None
    if content_type == "post":
        item_to_approve = db.query(Post).filter(Post.id == content_id).first()
    elif content_type == "comment":
        item_to_approve = db.query(Comment).filter(Comment.id == content_id).first()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid content type specified.",
        )

    if not item_to_approve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{content_type.capitalize()} not found.",
        )

    if item_to_approve.status != ContentStatus.pending_approval:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{content_type.capitalize()} is not pending approval.",
        )

    item_to_approve.status = ContentStatus.approved
    try:
        db.commit()
        db.refresh(item_to_approve)
        logger.info(f"{content_type.capitalize()} {content_id} approved by admin.")
        return item_to_approve
    except Exception as e:
        db.rollback()
        logger.error(f"Error approving {content_type} {content_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve content: {str(e)}",
        )


@router.put(
    "/{content_type}/{content_id}/reject",
    response_model=Union[PostResponse, CommentResponse],
)
def reject_content(
    content_type: Literal["post", "comment"] = Path(
        ..., title="The type of content to reject"
    ),
    content_id: str = Path(..., title="The ID of the content to reject"),
    db: Session = Depends(get_db),
):
    """Reject a post or comment that is pending approval. Sets status to 'rejected'."""
    item_to_reject = None
    if content_type == "post":
        item_to_reject = db.query(Post).filter(Post.id == content_id).first()
    elif content_type == "comment":
        item_to_reject = db.query(Comment).filter(Comment.id == content_id).first()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid content type specified.",
        )

    if not item_to_reject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{content_type.capitalize()} not found.",
        )

    if item_to_reject.status != ContentStatus.pending_approval:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{content_type.capitalize()} is not pending approval.",
        )

    item_to_reject.status = ContentStatus.rejected
    # Alternatively, one might choose to delete the item: db.delete(item_to_reject)
    try:
        db.commit()
        db.refresh(item_to_reject)
        logger.info(f"{content_type.capitalize()} {content_id} rejected by admin.")
        return item_to_reject
    except Exception as e:
        db.rollback()
        logger.error(f"Error rejecting {content_type} {content_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject content: {str(e)}",
        )
