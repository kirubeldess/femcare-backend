import uuid
from typing import List, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.community_content_post import (
    CommunityContentPost,
    CCHPostCategory as ModelCCHPostCategory,
)
from models.user import User
from pydantic_schemas.community_content_post import (
    CCHPostCreate,
    CCHPostResponse,
    CCHPostCategory as SchemaCCHPostCategory,
)
from utils.auth import get_current_user
from utils.moderation import contains_profanity

# Get logger
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=CCHPostResponse, status_code=status.HTTP_201_CREATED)
async def create_cch_post(
    post_data: CCHPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new Community Content & Highlight post (e.g., blog, story, event, biography).
    This endpoint is restricted to admin users.
    The category is validated by Pydantic against CCHPostCategory enum.
    Title is required by CCHPostCreate schema.
    """
    # Check if user is admin
    if current_user.role != "admin":
        logger.warning(
            f"Non-admin user {current_user.id} attempted to create a community content post"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can create community content posts",
        )

    # Moderation check
    post_language = post_data.language if post_data.language else "en"
    if await contains_profanity(
        post_data.title, language=post_language
    ) or await contains_profanity(post_data.content, language=post_language):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content contains inappropriate language and cannot be created.",
        )

    # Convert Pydantic HttpUrl objects to strings for JSON storage if images are present
    image_urls_to_store = (
        [str(url) for url in post_data.images] if post_data.images else None
    )

    db_cch_post = CommunityContentPost(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        title=post_data.title,
        content=post_data.content,
        category=ModelCCHPostCategory(post_data.category.value),
        images=image_urls_to_store,
        location=post_data.location,
        language=post_data.language,
    )

    try:
        db.add(db_cch_post)
        db.commit()
        db.refresh(db_cch_post)
        return db_cch_post
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create community content post: {str(e)}",
        )


@router.get("/", response_model=List[CCHPostResponse])
def get_all_cch_posts(
    skip: int = 0,
    limit: int = 100,
    category: Optional[SchemaCCHPostCategory] = None,
    language: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Get all Community Content & Highlight posts.
    Can be filtered by a specific CCH category and/or language.
    """
    query = db.query(CommunityContentPost)

    if category:
        query = query.filter(
            CommunityContentPost.category == ModelCCHPostCategory(category.value)
        )

    if language:
        query = query.filter(CommunityContentPost.language == language)

    cch_posts = (
        query.order_by(CommunityContentPost.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return cch_posts


@router.get("/{post_id}", response_model=CCHPostResponse)
def get_cch_post(post_id: str, db: Session = Depends(get_db)):
    """
    Get a specific Community Content & Highlight post by ID.
    """
    db_cch_post = (
        db.query(CommunityContentPost)
        .filter(CommunityContentPost.id == post_id)
        .first()
    )
    if db_cch_post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community content post not found.",
        )
    return db_cch_post


# Future: Add PUT and DELETE endpoints for CCH posts, restricted to admins.
# @router.put("/{post_id}", response_model=PostResponse)
# async def update_cch_post(post_id: str, post_update: PostUpdate, ...): pass

# @router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_cch_post(post_id: str, ...): pass
