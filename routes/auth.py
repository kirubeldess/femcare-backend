import uuid
from typing import List
from database import get_db
from fastapi import Depends, HTTPException, Query
import bcrypt
from models.user import User
from pydantic_schemas.user_create import UserCreate
from fastapi import APIRouter
from pydantic_schemas.user_login import UserLogin
from pydantic_schemas.user_response import UserResponse
from sqlalchemy.orm import Session


router = APIRouter()

@router.post('/signup', status_code=201)
def signup_user(user: UserCreate,db:Session=Depends(get_db)):
    #extracting the data that's coming from the req

    # print(user.name)
    # print(user.email)
    # print(user.password)

    #check if the user alr exists in db

    user_db = db.query(User).filter(User.email == user.email).first()

    if user_db:
        raise HTTPException(400,'User already exists')
        
    hashed_pw = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
    
    user_db = User(
        id=str(uuid.uuid4()), 
        email=user.email, 
        password=hashed_pw,
        name=user.name,
        phone=user.phone,
        emergency_contact=user.emergency_contact,
        latitude=user.latitude,
        longitude=user.longitude,
        language=user.language
    )

    #addung the user to the db
    db.add(user_db)
    db.commit()
    db.refresh(user_db)

    return user_db



@router.post('/login')
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    #check if a user with the same email alr exists
    user_db = db.query(User).filter(User.email == user.email).first()

    if not user_db:
        raise HTTPException(400,'User with this email does not exist')
    
    #password matching?
    is_match = bcrypt.checkpw(user.password.encode(), user_db.password)
    if not is_match:
        raise HTTPException(400,'Incorrect password')
    return user_db

@router.get('/users/check')
def check_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return {"users_count": len(users), "users": users}

@router.get('/users', response_model=List[UserResponse])
def get_all_users(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all users with pagination support.
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get('/users/{user_id}', response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    """
    Get a single user by ID.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user