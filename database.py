import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# First check for environment variable (Docker setup), otherwise use hardcoded local DB
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://femcare_owner:npg_tkORWx7weSI4@ep-muddy-hill-a4j6d1b9-pooler.us-east-1.aws.neon.tech/femcare?sslmode=require",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
