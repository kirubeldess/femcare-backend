import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import get_db
from models.resource import Resource, ResourceTypeEnum as ModelResourceTypeEnum
from pydantic_schemas.resource import (
    ResourceCreate,
    ResourceResponse,
    ResourceUpdate,
    ResourceCategory as SchemaResourceCategory,
    ResourceType as SchemaResourceType,
)
from utils.auth import get_admin_user, get_current_user
from models.user import User
from models.user_bookmarked_resource import UserBookmarkedResource
from pydantic_schemas.user_bookmarked_resource import (
    BookmarkResponse,
    UserBookmarkListItemResponse,
)
from sqlalchemy.exc import IntegrityError

router = APIRouter()


@router.post("/", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
def create_resource(
    resource: ResourceCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """Create a new educational resource. Admin access required."""
    db_resource = Resource(
        id=str(uuid.uuid4()),
        title=resource.title,
        content=resource.content,
        category=resource.category.value,
        subcategory=resource.subcategory,
        author=resource.author,
        language=resource.language,
        resource_type=ModelResourceTypeEnum(resource.resource_type.value),
        file_url=resource.file_url,
    )
    try:
        db.add(db_resource)
        db.commit()
        db.refresh(db_resource)
        return db_resource
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create resource: {str(e)}",
        )


@router.get("/", response_model=List[ResourceResponse])
def get_resources(
    skip: int = 0,
    limit: int = 100,
    category: Optional[SchemaResourceCategory] = None,
    subcategory: Optional[str] = None,
    language: Optional[str] = None,
    resource_type: Optional[SchemaResourceType] = None,
    search_keyword: Optional[str] = Query(None, min_length=1, max_length=100),
    db: Session = Depends(get_db),
):
    """Get all resources with optional filtering and keyword search."""
    query = db.query(Resource)

    if category:
        query = query.filter(Resource.category == category.value)
    if subcategory:
        query = query.filter(Resource.subcategory.ilike(f"%{subcategory}%"))
    if language:
        query = query.filter(Resource.language == language)
    if resource_type:
        query = query.filter(
            Resource.resource_type == ModelResourceTypeEnum(resource_type.value)
        )

    if search_keyword:
        search_term = f"%{search_keyword}%"
        query = query.filter(
            or_(
                Resource.title.ilike(search_term),
                Resource.content.ilike(search_term),
                Resource.category.ilike(search_term),
                Resource.subcategory.ilike(search_term),
            )
        )

    resources = (
        query.order_by(Resource.timestamp.desc()).offset(skip).limit(limit).all()
    )
    return resources


@router.get("/{resource_id}", response_model=ResourceResponse)
def get_resource(resource_id: str, db: Session = Depends(get_db)):
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )
    return resource


@router.put("/{resource_id}", response_model=ResourceResponse)
def update_resource(
    resource_id: str,
    resource_update: ResourceUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """Update a resource's information. Admin access required."""
    db_resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if db_resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )

    update_data = resource_update.dict(exclude_unset=True)

    if "category" in update_data and update_data["category"] is not None:
        update_data["category"] = update_data["category"].value
    if "resource_type" in update_data and update_data["resource_type"] is not None:
        update_data["resource_type"] = ModelResourceTypeEnum(
            update_data["resource_type"].value
        )

    for key, value in update_data.items():
        setattr(db_resource, key, value)

    try:
        db.commit()
        db.refresh(db_resource)
        return db_resource
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update resource: {str(e)}",
        )


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resource(
    resource_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """Delete a resource. Admin access required."""
    db_resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if db_resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )

    try:
        db.delete(db_resource)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete resource: {str(e)}",
        )


# The specific category and language endpoints might need review or can be covered by the main GET / endpoint filters
# For example, /category/{category} is now covered by GET /?category=...
# Removing them for now to simplify, unless specific use case is confirmed.

# @router.get("/category/{category}", response_model=List[ResourceResponse])
# def get_resources_by_category(
#     category: SchemaResourceCategory,
#     language: Optional[str] = None,
#     db: Session = Depends(get_db)
# ): ...

# @router.get("/language/{language}", response_model=List[ResourceResponse])
# def get_resources_by_language(language: str, db: Session = Depends(get_db)): ...

# --- Bookmark Endpoints ---


@router.post(
    "/bookmarks/{resource_id}",
    response_model=BookmarkResponse,
    status_code=status.HTTP_201_CREATED,
)
async def bookmark_resource(
    resource_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bookmark a resource for the current user."""
    # Check if resource exists
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )

    existing_bookmark = (
        db.query(UserBookmarkedResource)
        .filter(
            UserBookmarkedResource.user_id == current_user.id,
            UserBookmarkedResource.resource_id == resource_id,
        )
        .first()
    )

    if existing_bookmark:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resource already bookmarked",
        )

    new_bookmark = UserBookmarkedResource(
        id=str(uuid.uuid4()), user_id=current_user.id, resource_id=resource_id
    )
    try:
        db.add(new_bookmark)
        db.commit()
        db.refresh(new_bookmark)
        return new_bookmark
    except IntegrityError:  # Catching the unique constraint violation explicitly
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resource already bookmarked (concurrent request or race condition)",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not bookmark resource: {str(e)}",
        )


@router.delete("/bookmarks/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unbookmark_resource(
    resource_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Unbookmark a resource for the current user."""
    bookmark = (
        db.query(UserBookmarkedResource)
        .filter(
            UserBookmarkedResource.user_id == current_user.id,
            UserBookmarkedResource.resource_id == resource_id,
        )
        .first()
    )

    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found for this resource",
        )

    try:
        db.delete(bookmark)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not unbookmark resource: {str(e)}",
        )


@router.get("/users/me/bookmarks", response_model=List[UserBookmarkListItemResponse])
async def get_my_bookmarked_resources(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Get all resources bookmarked by the current user."""
    bookmarks = (
        db.query(UserBookmarkedResource)
        .filter(UserBookmarkedResource.user_id == current_user.id)
        .all()
    )

    # Prepare response: For each bookmark, fetch the associated resource details
    # This approach avoids a complex join directly in one query if not strictly needed,
    # but can lead to N+1 problem if not careful. For bookmarks, eager loading on UserBookmarkedResource.resource might be better.
    # For now, let's manually construct. For production, consider optimizing.

    response_items = []
    for bm in bookmarks:
        # Assuming bm.resource relationship is loaded or we fetch it (could be N+1 if not eager loaded)
        # If bm.resource is not automatically populated due to session state or eager loading, fetch explicitly:
        # resource_details = db.query(Resource).filter(Resource.id == bm.resource_id).first()
        # if not resource_details: continue # Should not happen if DB is consistent

        # If relationships are set up correctly and session is active, bm.resource should work.
        if (
            bm.resource
        ):  # Check if resource is available (it should be due to ForeignKey)
            response_items.append(
                UserBookmarkListItemResponse(
                    bookmark_id=bm.id,
                    bookmarked_at=bm.timestamp,
                    resource=ResourceResponse.from_orm(bm.resource),
                )
            )
    return response_items
