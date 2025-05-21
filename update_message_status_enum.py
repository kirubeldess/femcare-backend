from sqlalchemy import create_engine, text
from database import get_db
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def update_message_status_enum():
    """
    Update the MessageStatus enum in the database to include the new values:
    'requested', 'accepted', and 'rejected'
    """
    try:
        # Get a connection
        db = next(get_db())
        connection = db.connection()

        # PostgreSQL commands to update the enum
        # First, create a new type with all values
        connection.execute(
            text(
                """
        CREATE TYPE messagestatus_new AS ENUM (
            'requested', 'accepted', 'rejected', 
            'sent', 'delivered', 'read'
        );
        """
            )
        )

        # Update both tables that use this enum
        # First messages table
        connection.execute(
            text(
                """
        ALTER TABLE messages 
        ALTER COLUMN status DROP DEFAULT;
        """
            )
        )

        connection.execute(
            text(
                """
        ALTER TABLE messages 
        ALTER COLUMN status TYPE messagestatus_new 
        USING status::text::messagestatus_new;
        """
            )
        )

        # Then consultant_messages table
        connection.execute(
            text(
                """
        ALTER TABLE consultant_messages 
        ALTER COLUMN status DROP DEFAULT;
        """
            )
        )

        connection.execute(
            text(
                """
        ALTER TABLE consultant_messages 
        ALTER COLUMN status TYPE messagestatus_new 
        USING status::text::messagestatus_new;
        """
            )
        )

        # Now we can drop the old type with CASCADE option
        connection.execute(
            text(
                """
        DROP TYPE messagestatus CASCADE;
        """
            )
        )

        # Rename the new type to the old name
        connection.execute(
            text(
                """
        ALTER TYPE messagestatus_new RENAME TO messagestatus;
        """
            )
        )

        # Restore the defaults for both tables
        connection.execute(
            text(
                """
        ALTER TABLE messages 
        ALTER COLUMN status SET DEFAULT 'sent'::messagestatus;
        """
            )
        )

        connection.execute(
            text(
                """
        ALTER TABLE consultant_messages 
        ALTER COLUMN status SET DEFAULT 'sent'::messagestatus;
        """
            )
        )

        # Commit the transaction
        connection.commit()

        logger.info("Successfully updated MessageStatus enum in the database")

    except Exception as e:
        logger.error(f"Error updating MessageStatus enum: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    update_message_status_enum()
