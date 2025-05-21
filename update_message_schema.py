import uuid
import sys
from sqlalchemy import create_engine, text
from database import get_db
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def update_message_schema(skip_data_migration=False):
    """
    Update the database schema to support the new message request workflow:
    1. Create new tables: message_requests and conversations
    2. Update the messages table to reference conversations
    3. Migrate existing data if possible and if not skipped

    Args:
        skip_data_migration: If True, only create the schema without migrating data
    """
    try:
        # Get a connection
        db = next(get_db())
        connection = db.connection()

        # Step 1: Create message_requests table
        logger.info("Creating message_requests table...")
        connection.execute(
            text(
                """
        CREATE TYPE messagerequeststatustype AS ENUM ('pending', 'accepted', 'rejected');
        
        CREATE TABLE IF NOT EXISTS message_requests (
            id TEXT PRIMARY KEY,
            sender_id TEXT NOT NULL REFERENCES users(id),
            receiver_id TEXT NOT NULL REFERENCES users(id),
            post_id TEXT NOT NULL REFERENCES posts(id),
            initial_message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status messagerequeststatustype DEFAULT 'pending'
        );
        """
            )
        )

        # Step 2: Create conversations table
        logger.info("Creating conversations table...")
        connection.execute(
            text(
                """
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user1_id TEXT NOT NULL REFERENCES users(id),
            user2_id TEXT NOT NULL REFERENCES users(id),
            request_id TEXT NOT NULL REFERENCES message_requests(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
            )
        )

        # Step 3: Create messagestatustype enum if it doesn't exist
        logger.info("Creating messagestatustype enum...")
        try:
            connection.execute(
                text(
                    """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_type WHERE typname = 'messagestatustype'
                ) THEN
                    CREATE TYPE messagestatustype AS ENUM ('sent', 'delivered', 'read');
                END IF;
            END$$;
            """
                )
            )
        except Exception as e:
            logger.warning(f"Error checking/creating enum: {e}")
            # Try direct creation, will fail if it already exists but that's OK
            try:
                connection.execute(
                    text(
                        "CREATE TYPE messagestatustype AS ENUM ('sent', 'delivered', 'read');"
                    )
                )
                logger.info("Created messagestatustype enum")
            except Exception as e2:
                logger.warning(f"Could not create enum directly: {e2}")
                # If we still can't create it, we need to abort
                if "already exists" not in str(e2):
                    raise

        # Step 4: Create new messages table
        logger.info("Creating new messages table...")
        connection.execute(
            text(
                """
        CREATE TABLE IF NOT EXISTS new_messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL REFERENCES conversations(id),
            sender_id TEXT NOT NULL REFERENCES users(id),
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status messagestatustype DEFAULT 'sent'
        );
        """
            )
        )

        # Step 5: Check if old messages table exists and migrate data if possible
        if not skip_data_migration:
            logger.info("Checking for existing messages to migrate...")
            result = connection.execute(
                text(
                    """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'messages'
            );
            """
                )
            )

            old_table_exists = result.scalar()

            if old_table_exists:
                logger.info("Migrating existing messages...")

                # First, create message requests and conversations for existing message pairs
                connection.execute(
                    text(
                        """
                -- Create temporary table to identify unique conversation pairs
                CREATE TEMPORARY TABLE conversation_pairs AS
                SELECT DISTINCT
                    CASE WHEN sender_id < receiver_id THEN sender_id ELSE receiver_id END as user1_id,
                    CASE WHEN sender_id < receiver_id THEN receiver_id ELSE sender_id END as user2_id,
                    post_id
                FROM messages
                ORDER BY user1_id, user2_id;
                """
                    )
                )

                # Get conversation pairs
                pairs = connection.execute(
                    text(
                        """
                SELECT * FROM conversation_pairs;
                """
                    )
                ).fetchall()

                # For each pair, create a message request and conversation
                for pair in pairs:
                    user1_id = pair[0]
                    user2_id = pair[1]
                    post_id = pair[2]

                    # Find the first message between these users
                    first_msg = connection.execute(
                        text(
                            f"""
                    SELECT * FROM messages 
                    WHERE (sender_id = '{user1_id}' AND receiver_id = '{user2_id}')
                       OR (sender_id = '{user2_id}' AND receiver_id = '{user1_id}')
                    ORDER BY timestamp ASC
                    LIMIT 1;
                    """
                        )
                    ).fetchone()

                    if first_msg:
                        # Create a message request
                        request_id = str(uuid.uuid4())
                        connection.execute(
                            text(
                                f"""
                        INSERT INTO message_requests (id, sender_id, receiver_id, post_id, initial_message, status)
                        VALUES ('{request_id}', '{first_msg[1]}', '{first_msg[2]}', 
                                '{first_msg[3] or post_id}', '{first_msg[4]}', 'accepted');
                        """
                            )
                        )

                        # Create a conversation
                        conversation_id = str(uuid.uuid4())
                        connection.execute(
                            text(
                                f"""
                        INSERT INTO conversations (id, user1_id, user2_id, request_id)
                        VALUES ('{conversation_id}', '{user1_id}', '{user2_id}', '{request_id}');
                        """
                            )
                        )

                        # Migrate messages to the new table with explicit cast to messagestatustype
                        connection.execute(
                            text(
                                f"""
                        INSERT INTO new_messages (id, conversation_id, sender_id, content, timestamp, status)
                        SELECT id, '{conversation_id}', sender_id, content, timestamp, 
                               status::text::messagestatustype
                        FROM messages
                        WHERE (sender_id = '{user1_id}' AND receiver_id = '{user2_id}')
                           OR (sender_id = '{user2_id}' AND receiver_id = '{user1_id}');
                        """
                            )
                        )

                # Drop temporary table
                connection.execute(
                    text(
                        """
                DROP TABLE conversation_pairs;
                """
                    )
                )
            else:
                logger.info("No existing messages table found for migration.")
        else:
            logger.info("Skipping data migration as requested.")

        # Rename tables
        logger.info("Finalizing schema changes...")

        # Check if old messages table exists
        result = connection.execute(
            text(
                """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'messages'
        );
        """
            )
        )
        old_table_exists = result.scalar()

        if old_table_exists and not skip_data_migration:
            # If old table exists and we didn't skip migration, rename it
            connection.execute(
                text(
                    """
            ALTER TABLE messages RENAME TO old_messages;
            ALTER TABLE new_messages RENAME TO messages;
            """
                )
            )
            logger.info("Old messages table preserved as 'old_messages'.")
        elif old_table_exists and skip_data_migration:
            # If old table exists but we skipped migration, drop new_messages and leave old table
            connection.execute(
                text(
                    """
            DROP TABLE new_messages;
            """
                )
            )
            logger.info("Kept existing messages table, schema created for reference.")
        else:
            # If no old table, just rename the new one
            connection.execute(
                text(
                    """
            ALTER TABLE new_messages RENAME TO messages;
            """
                )
            )
            logger.info("New schema created without migration (no existing data).")

        # Commit the transaction
        connection.commit()
        logger.info("Message schema update completed successfully.")

    except Exception as e:
        logger.error(f"Error updating message schema: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Check if --skip-migration flag is provided
    skip_migration = "--skip-migration" in sys.argv
    if skip_migration:
        logger.info("Running schema update with data migration skipped")
    update_message_schema(skip_data_migration=skip_migration)
