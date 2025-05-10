import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# First check for environment variable (Docker setup), otherwise use hardcoded local DB
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:12er56UI90@127.0.0.1:5432/femcare"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
