import logging
from sqlalchemy import text
from database import get_db

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def update_notification_schema():
    """
    Update the notification schema to include:
    1. user_id column (required)
    2. 'message' option in the NotificationContentType enum
    """
    try:
        # Get a database connection
        db = next(get_db())
        connection = db.connection()

        # Check if notifications table exists
        logger.info("Checking if notifications table exists...")
        result = connection.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'notifications'
                );
                """
            )
        )
        table_exists = result.scalar()

        if not table_exists:
            logger.info("Notifications table doesn't exist. Creating new table...")
            # Create the notifications table from scratch
            connection.execute(
                text(
                    """
                    CREATE TYPE notificationcontenttype AS ENUM ('post', 'comment', 'message');
                    
                    CREATE TABLE notifications (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL REFERENCES users(id),
                        message TEXT NOT NULL,
                        is_read BOOLEAN NOT NULL DEFAULT FALSE,
                        timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        related_content_type notificationcontenttype,
                        related_content_id TEXT
                    );
                    
                    CREATE INDEX idx_notifications_user_id ON notifications(user_id);
                    CREATE INDEX idx_notifications_is_read ON notifications(is_read);
                    """
                )
            )
            logger.info("Notifications table created successfully.")
        else:
            logger.info("Notifications table exists. Checking for necessary updates...")

            # Check if user_id column exists
            result = connection.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'notifications' AND column_name = 'user_id'
                    );
                    """
                )
            )
            user_id_exists = result.scalar()

            if not user_id_exists:
                logger.info("Adding user_id column to notifications table...")
                connection.execute(
                    text(
                        """
                        ALTER TABLE notifications 
                        ADD COLUMN user_id TEXT REFERENCES users(id);
                        
                        CREATE INDEX idx_notifications_user_id ON notifications(user_id);
                        """
                    )
                )
                logger.info("user_id column added successfully.")

                # Optionally set all existing notifications to a default user if needed
                # connection.execute(
                #     text(
                #         """
                #         UPDATE notifications SET user_id = 'default_user_id' WHERE user_id IS NULL;
                #         ALTER TABLE notifications ALTER COLUMN user_id SET NOT NULL;
                #         """
                #     )
                # )

            # Check if 'message' enum value exists in notificationcontenttype
            try:
                result = connection.execute(
                    text(
                        """
                        SELECT EXISTS (
                            SELECT 1 FROM pg_enum 
                            WHERE enumlabel = 'message' AND 
                                  enumtypid = (SELECT oid FROM pg_type WHERE typname = 'notificationcontenttype')
                        );
                        """
                    )
                )
                message_type_exists = result.scalar()

                if not message_type_exists:
                    logger.info(
                        "Adding 'message' type to notificationcontenttype enum..."
                    )
                    connection.execute(
                        text(
                            """
                            ALTER TYPE notificationcontenttype ADD VALUE 'message';
                            """
                        )
                    )
                    logger.info("'message' type added to enum successfully.")
            except Exception as e:
                logger.warning(f"Error checking or adding enum value: {e}")
                logger.info("Attempting to create the enum if it doesn't exist...")
                try:
                    connection.execute(
                        text(
                            """
                            DO $$
                            BEGIN
                                IF NOT EXISTS (
                                    SELECT 1 FROM pg_type WHERE typname = 'notificationcontenttype'
                                ) THEN
                                    CREATE TYPE notificationcontenttype AS ENUM ('post', 'comment', 'message');
                                END IF;
                            END$$;
                            """
                        )
                    )
                except Exception as e2:
                    logger.error(f"Failed to create enum: {e2}")

        # Commit all changes
        connection.commit()
        logger.info("Notification schema update completed successfully.")

    except Exception as e:
        logger.error(f"Error updating notification schema: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    update_notification_schema()
