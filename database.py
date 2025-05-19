import os
import time
import logging
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, DisconnectionError

# Configure logging
logger = logging.getLogger(__name__)

# First check for environment variable (Docker setup), otherwise use hardcoded local DB
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://femcare_owner:npg_tkORWx7weSI4@ep-muddy-hill-a4j6d1b9-pooler.us-east-1.aws.neon.tech/femcare?sslmode=require",
)

# Engine configuration with connection pooling and timeout settings
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Test connections before using them
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_timeout=30,  # Wait up to 30 seconds for a connection
    pool_size=10,  # Maximum number of connections to keep
    max_overflow=20,  # Maximum number of connections that can be created beyond pool_size
    connect_args={
        "connect_timeout": 10,  # Connection timeout in seconds
        "keepalives": 1,  # Enable keepalives
        "keepalives_idle": 60,  # Idle time before sending keepalive
        "keepalives_interval": 10,  # Interval between keepalives
        "keepalives_count": 5,  # Number of keepalives before giving up
    },
)


# Add event listener to handle disconnections
@event.listens_for(engine, "connect")
def connect(dbapi_connection, connection_record):
    connection_record.info["pid"] = os.getpid()


@event.listens_for(engine, "checkout")
def checkout(dbapi_connection, connection_record, connection_proxy):
    pid = os.getpid()
    if connection_record.info["pid"] != pid:
        connection_record.connection = connection_proxy.connection = None
        raise DisconnectionError(
            "Connection record belongs to pid %s, "
            "attempting to check out in pid %s" % (connection_record.info["pid"], pid)
        )


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = None
    retry_count = 0
    max_retries = 3

    while retry_count < max_retries:
        try:
            db = SessionLocal()
            # Test the connection
            db.execute(text("SELECT 1"))
            break
        except OperationalError as e:
            retry_count += 1
            logger.warning(
                f"Database connection error (attempt {retry_count}/{max_retries}): {str(e)}"
            )
            if db is not None:
                db.close()

            if retry_count < max_retries:
                # Wait before retrying (exponential backoff)
                time.sleep(2**retry_count)
            else:
                logger.error("Failed to connect to database after multiple attempts")
                raise

    try:
        yield db
    except Exception as e:
        logger.error(f"Error during database operation: {str(e)}")
        raise
    finally:
        if db is not None:
            db.close()
