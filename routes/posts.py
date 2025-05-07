import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models.post import Post, PostCategory
from pydantic_schemas.post import PostCreate, PostResponse

router = APIRouter()


@router.post("/", response_model=PostResponse, status_code=201)
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    """
    Create a new post using the user_id from the request body.
    Set it to None if the post is anonymous.
    """
    # Convert string category to enum value
    category_value = (
        post.category.value if hasattr(post.category, "value") else post.category
    )

    # Additional validation for title field
    if category_value != "vent" and not post.title:
        raise HTTPException(
            status_code=400,
            detail="Title is required for all post categories except 'vent'",
        )

    # Validate anonymity is only for venting
    if category_value != "vent" and post.is_anonymous:
        raise HTTPException(
            status_code=400,
            detail="Anonymous posts are only allowed for the 'vent' category",
        )

    db_post = Post(
        id=str(uuid.uuid4()),
        user_id=None if post.is_anonymous else post.user_id,
        title=post.title,
        content=post.content,
        category=category_value,
        is_anonymous=post.is_anonymous,
        location=post.location,
        language=post.language,
    )

    try:
        db.add(db_post)
        db.commit()
        db.refresh(db_post)

        # Create a dictionary from the db_post to manually convert enum values to strings
        post_dict = {
            "id": db_post.id,
            "user_id": db_post.user_id,
            "title": db_post.title,
            "content": db_post.content,
            "category": db_post.category.value,  # Convert enum to string value
            "is_anonymous": db_post.is_anonymous,
            "location": db_post.location,
            "language": db_post.language,
            "timestamp": db_post.timestamp,
        }

        # Return the dictionary which will be automatically converted to PostResponse
        return post_dict
    except Exception as e:
        db.rollback()
        print(f"Error creating post: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create post: {str(e)}")


# Helper function to convert Post objects to dictionaries with string enum values
def convert_post_to_dict(post):
    return {
        "id": post.id,
        "user_id": post.user_id,
        "title": post.title,
        "content": post.content,
        "category": post.category.value,  # Convert enum to string value
        "is_anonymous": post.is_anonymous,
        "location": post.location,
        "language": post.language,
        "timestamp": post.timestamp,
    }


@router.get("/", response_model=List[PostResponse])
def get_posts(
    skip: int = 0,
    limit: int = 100,
    category: Optional[PostCategory] = None,
    language: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get all posts with optional filtering by category and language"""
    query = db.query(Post)

    if category:
        query = query.filter(Post.category == category)

    if language:
        query = query.filter(Post.language == language)

    posts = query.order_by(Post.timestamp.desc()).offset(skip).limit(limit).all()
    return [convert_post_to_dict(post) for post in posts]


@router.get("/user/{user_id}", response_model=List[PostResponse])
def get_user_posts(user_id: str, db: Session = Depends(get_db)):
    """Get all posts by a specific user"""
    db_posts = db.query(Post).filter(Post.user_id == user_id).all()
    return [convert_post_to_dict(post) for post in db_posts]


@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: str, db: Session = Depends(get_db)):
    """Get a specific post by ID"""
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return convert_post_to_dict(db_post)
