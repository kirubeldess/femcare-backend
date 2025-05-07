import uuid
import logging
from database import get_db
from fastapi import Depends, HTTPException
import bcrypt
from models.user import User
from pydantic_schemas.user_create import UserCreate
from fastapi import APIRouter
from pydantic_schemas.user_login import UserLogin
from sqlalchemy.orm import Session


# Get a logger instance specific to this module
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/signup", status_code=201)
def signup_user(user: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Attempting to sign up user with email: {user.email}")
    # extracting the data that's coming from the req

    # print(user.name)
    # print(user.email)
    # print(user.password)

    # check if the user alr exists in db

    user_db = db.query(User).filter(User.email == user.email).first()

    if user_db:
        raise HTTPException(400, "User already exists")

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
        language=user.language,
    )

    # addung the user to the db
    db.add(user_db)
    db.commit()
    db.refresh(user_db)

    return user_db


@router.post("/login")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    # check if a user with the same email alr exists
    user_db = db.query(User).filter(User.email == user.email).first()

    if not user_db:
        raise HTTPException(400, "User with this email does not exist")

    # password matching?
    is_match = bcrypt.checkpw(user.password.encode(), user_db.password)
    if not is_match:
        raise HTTPException(400, "Incorrect password")
    return user_db


@router.get("/users/check")
def check_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return {"users_count": len(users), "users": users}
