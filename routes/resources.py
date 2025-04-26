import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models.resource import Resource
from pydantic_schemas.resource import ResourceCreate, ResourceResponse, ResourceUpdate, ResourceCategory

router = APIRouter()

@router.post("/", response_model=ResourceResponse, status_code=201)
def create_resource(resource: ResourceCreate, db: Session = Depends(get_db)):
    """
    Create a new educational resource.
    """
    db_resource = Resource(
        id=str(uuid.uuid4()),
        title=resource.title,
        content=resource.content,
        category=resource.category.value,
        subcategory=resource.subcategory,
        author=resource.author,
        language=resource.language
    )
    
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    return db_resource

@router.get("/", response_model=List[ResourceResponse])
def get_resources(
    skip: int = 0, 
    limit: int = 100, 
    category: Optional[ResourceCategory] = None,
    subcategory: Optional[str] = None,
    language: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all resources with optional filtering by category, subcategory, and language.
    """
    query = db.query(Resource)
    
    if category:
        query = query.filter(Resource.category == category.value)
    
    if subcategory:
        query = query.filter(Resource.subcategory == subcategory)
    
    if language:
        query = query.filter(Resource.language == language)
    
    return query.order_by(Resource.timestamp.desc()).offset(skip).limit(limit).all()

@router.get("/{resource_id}", response_model=ResourceResponse)
def get_resource(resource_id: str, db: Session = Depends(get_db)):
    """
    Get a specific resource by ID.
    """
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource

@router.put("/{resource_id}", response_model=ResourceResponse)
def update_resource(resource_id: str, resource_update: ResourceUpdate, db: Session = Depends(get_db)):
    """
    Update a resource's information.
    """
    db_resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if db_resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    # Update fields if they are provided
    update_data = resource_update.dict(exclude_unset=True)
    
    # Convert enum to string value if it exists
    if 'category' in update_data and update_data['category'] is not None:
        update_data['category'] = update_data['category'].value
    
    for key, value in update_data.items():
        setattr(db_resource, key, value)
    
    db.commit()
    db.refresh(db_resource)
    return db_resource

@router.delete("/{resource_id}", status_code=204)
def delete_resource(resource_id: str, db: Session = Depends(get_db)):
    """
    Delete a resource.
    """
    db_resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if db_resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    db.delete(db_resource)
    db.commit()
    return None

@router.get("/category/{category}", response_model=List[ResourceResponse])
def get_resources_by_category(
    category: ResourceCategory, 
    language: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all resources in a specific category with optional language filter.
    """
    query = db.query(Resource).filter(Resource.category == category.value)
    
    if language:
        query = query.filter(Resource.language == language)
    
    return query.order_by(Resource.timestamp.desc()).all()

@router.get("/language/{language}", response_model=List[ResourceResponse])
def get_resources_by_language(language: str, db: Session = Depends(get_db)):
    """
    Get all resources in a specific language.
    """
    resources = db.query(Resource).filter(Resource.language == language).order_by(Resource.timestamp.desc()).all()
    return resources 