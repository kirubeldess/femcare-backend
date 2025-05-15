# routes/auth.py
import uuid
import logging
from datetime import timedelta
from typing import Optional

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from pydantic_schemas.user_create import UserCreate
from pydantic_schemas.user_login import UserLogin
from pydantic_schemas.user_response import UserResponse
from pydantic_schemas.token import Token
from utils.auth import (
    create_access_token,
    get_current_user,
    get_admin_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

# Get a logger instance specific to this module
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/create-initial-admin",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
    summary="Create Initial Admin Account (One-Time Use)",
)
def create_initial_admin(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Create the first admin user. This endpoint is intended for one-time use during initial setup.
    If an admin user already exists, this endpoint will return an error.
    """
    logger.info(
        f"Attempting to create initial admin account with email: {user_data.email}"
    )

    # Check if any admin user already exists
    existing_admin = db.query(User).filter(User.role == "admin").first()
    if existing_admin:
        logger.warning(
            f"Attempt to use initial admin creation endpoint when an admin ({existing_admin.email}) already exists."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Initial admin account already exists. This endpoint is disabled.",
        )

    # Check if the user email itself already exists (even as non-admin)
    existing_user_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {user_data.email} already exists.",
        )

    hashed_password = bcrypt.hashpw(
        user_data.password.encode("utf-8"), bcrypt.gensalt()
    )

    initial_admin_user = User(
        id=str(uuid.uuid4()),
        name=user_data.name,
        email=user_data.email,
        password=hashed_password,
        phone=user_data.phone,
        language=user_data.language,
        role="admin",  # Explicitly set role to admin
    )

    try:
        db.add(initial_admin_user)
        db.commit()
        db.refresh(initial_admin_user)
        logger.info(
            f"Initial admin user {initial_admin_user.email} created successfully."
        )
        return initial_admin_user
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating initial admin user {user_data.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create initial admin user: {str(e)}",
        )


@router.post("/signup", response_model=UserResponse, status_code=201)
def signup_user(user: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Attempting to sign up user with email: {user.email}")

    # Check if the user already exists in the database
    user_db = db.query(User).filter(User.email == user.email).first()
    if user_db:
        raise HTTPException(status_code=400, detail="User already exists")

    # Hash the password
    hashed_pw = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())

    # Create a new user
    user_db = User(
        id=str(uuid.uuid4()),
        email=user.email,
        password=hashed_pw,
        name=user.name,
        phone=user.phone,
        language=user.language,
    )

    # Add the user to the database
    db.add(user_db)
    db.commit()
    db.refresh(user_db)

    # Return user data without password
    return UserResponse.from_orm(user_db)


# @router.post("/login", response_model=Token)
# def login_user(user: UserLogin, db: Session = Depends(get_db)):
#     # Check if a user with the same email already exists
#     user_db = db.query(User).filter(User.email == user.email).first()
#     if not user_db:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect email or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     # Check if password matches
#     is_match = bcrypt.checkpw(user.password.encode(), user_db.password)
#     if not is_match:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect email or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     # Create access token
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"sub": user_db.id, "role": user_db.role},
#         expires_delta=access_token_expires,
#     )

#     return {"access_token": access_token, "token_type": "bearer"}


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not bcrypt.checkpw(form_data.password.encode(), user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id, "role": user.role}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current user's information
    """
    return current_user


@router.get("/users/check")
def check_users(
    db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)
):
    """
    Admin only endpoint to check all users in the system
    """
    users = db.query(User).all()
    return {
        "users_count": len(users),
        "users": [UserResponse.from_orm(user) for user in users],
    }
