import uuid
from typing import List
from database import get_db
from fastapi import Depends, HTTPException, Query, status
import bcrypt
from models.user import User
from pydantic_schemas.user_create import UserCreate
from fastapi import APIRouter
from pydantic_schemas.user_login import UserLogin
from pydantic_schemas.user_response import UserResponse
from sqlalchemy.orm import Session
from sqlalchemy import text


router = APIRouter()

@router.get('/debug')
def debug_db(db: Session = Depends(get_db)):
    """
    Debug endpoint to test database connectivity
    """
    try:
        # Try to execute a simple query
        result = db.execute(text("SELECT 1 as is_working")).scalar()
        return {"db_working": bool(result == 1)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "type": str(type(e))}

@router.post('/signup', status_code=201, response_model=UserResponse)
def signup_user(user: UserCreate, db: Session = Depends(get_db)):
    
    #Register a new user
    
    try:
        print(f"Starting signup process for email: {user.email}")
        # Check if the user already exists in db
        user_db = db.query(User).filter(User.email == user.email).first()

        if user_db:
            print(f"User with email {user.email} already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists"
            )
            
        print("Hashing password")
        hashed_pw = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
        
        print("Creating new user object")
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

        # Add the user to the db
        print("Adding user to database")
        db.add(user_db)
        print("Committing transaction")
        db.commit()
        print("Refreshing user object")
        db.refresh(user_db)
        print(f"User created successfully with id: {user_db.id}")

        return user_db
    except Exception as e:
        db.rollback()
        # Log the actual error for debugging
        print(f"Error in signup: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating user"
        )

@router.post('/login', response_model=UserResponse)
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    
    #Login a user with email and password
    
    try:
        # Check if a user with the same email already exists
        user_db = db.query(User).filter(User.email == user.email).first()

        if not user_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email does not exist"
            )
        
        # Check if password matches
        is_match = bcrypt.checkpw(user.password.encode(), user_db.password)
        if not is_match:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect password"
            )
        return user_db
    except HTTPException:
        # Re-raise HTTP exceptions as they are already formatted correctly
        raise
    except Exception as e:
        # Log the actual error for debugging
        print(f"Error in login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while logging in"
        )

@router.get('/users/check')
def check_users(db: Session = Depends(get_db)):
    
    #Check how many users are in the database
    
    try:
        users = db.query(User).all()
        return {"users_count": len(users), "users": users}
    except Exception as e:
        print(f"Error checking users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while checking users"
        )

@router.get('/users', response_model=List[UserResponse])
def get_all_users(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db)
):
    
    #Get all users with pagination support.
    
    try:
        users = db.query(User).offset(skip).limit(limit).all()
        return users
    except Exception as e:
        print(f"Error getting users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving users"
        )

@router.get('/users/{user_id}', response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    
    #Get a single user by ID.
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the user"
        )
