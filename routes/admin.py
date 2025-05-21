# routes/admin.py
import logging
import uuid  # Added for ID generation
import bcrypt  # Added for password hashing
from fastapi import APIRouter, Depends, HTTPException, status, Body  # Added Body
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models.user import User
from pydantic_schemas.user_response import UserResponse
from pydantic_schemas.user_create import UserCreate  # Added for creating admin
from utils.auth import get_current_user

# Get a logger instance specific to this module
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],  # Changed tag to "Admin" for consistency with main.py
)


# Helper function to verify admin role
def verify_admin(user: User):
    if user.role != "admin":
        logger.warning(f"Non-admin user {user.id} attempted to access admin endpoint")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this operation",
        )


@router.post(
    "/users/create-admin",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_admin_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new user with admin privileges. Only accessible by other admins.
    """
    # Verify admin privileges
    verify_admin(current_user)

    logger.info(
        f"Admin {current_user.email} attempting to create new admin user with email: {user_data.email}"
    )

    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {user_data.email} already exists.",
        )

    hashed_password = bcrypt.hashpw(
        user_data.password.encode("utf-8"), bcrypt.gensalt()
    )

    new_admin_user = User(
        id=str(uuid.uuid4()),
        name=user_data.name,
        email=user_data.email,
        password=hashed_password,
        phone=user_data.phone,
        language=user_data.language,
        role="admin",  # Explicitly set role to admin
    )

    try:
        db.add(new_admin_user)
        db.commit()
        db.refresh(new_admin_user)
        logger.info(
            f"Admin user {new_admin_user.email} created successfully by {current_user.email}"
        )
        return new_admin_user
    except Exception as e:
        db.rollback()
        logger.error(
            f"Error creating admin user {user_data.email} by {current_user.email}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create admin user: {str(e)}",
        )


@router.put("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: str,
    new_role: str = Body(
        ..., embed=True, pattern="^(admin|User)$"
    ),  # Allow 'admin' or 'User'
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a user's role (e.g., promote to admin or demote to User).
    Admins cannot change their own role using this endpoint if they are the only admin.
    """
    # Verify admin privileges
    verify_admin(current_user)

    logger.info(
        f"Admin {current_user.email} attempting to change role of user {user_id} to {new_role}"
    )

    user_to_update = db.query(User).filter(User.id == user_id).first()
    if not user_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Prevent admin from changing their own role if they are the sole admin
    if (
        user_to_update.id == current_user.id
        and user_to_update.role == "admin"
        and new_role != "admin"
    ):
        admin_count = db.query(User).filter(User.role == "admin").count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change the role of the only admin. Promote another user to admin first.",
            )

    if user_to_update.role == new_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User {user_id} already has the role '{new_role}'.",
        )

    user_to_update.role = new_role
    try:
        db.commit()
        db.refresh(user_to_update)
        logger.info(
            f"Role of user {user_id} changed to {new_role} by {current_user.email}"
        )
        return user_to_update
    except Exception as e:
        db.rollback()
        logger.error(
            f"Error changing role for user {user_id} by {current_user.email}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user role: {str(e)}",
        )


@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Get all users in the system
    """
    # Verify admin privileges
    verify_admin(current_user)

    logger.info("Admin requesting all users")
    users = db.query(User).all()
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific user by ID
    """
    # Verify admin privileges
    verify_admin(current_user)

    logger.info(f"Admin requesting user with ID: {user_id}")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a user by ID.
    Admins cannot delete themselves.
    """
    # Verify admin privileges
    verify_admin(current_user)

    logger.info(
        f"Admin {current_user.email} attempting to delete user with ID: {user_id}"
    )

    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins cannot delete their own account.",
        )

    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if not user_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Optional: Check if deleting the only admin if the user_to_delete is an admin
    # This is more complex if other admins exist. Simpler to just prevent self-deletion.
    # if user_to_delete.role == "admin":
    #     admin_count = db.query(User).filter(User.role == "admin").count()
    #     if admin_count <= 1:
    #         raise HTTPException(
    #             status_code=status.HTTP_403_FORBIDDEN,
    #             detail="Cannot delete the only admin account."
    #         )

    try:
        db.delete(user_to_delete)
        db.commit()
        logger.info(
            f"User {user_id} deleted successfully by admin {current_user.email}"
        )
        return None
    except Exception as e:
        db.rollback()
        logger.error(
            f"Error deleting user {user_id} by admin {current_user.email}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}",
        )
