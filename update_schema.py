from database import engine
from sqlalchemy import text
from sqlalchemy import create_engine, Column, TEXT, VARCHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import CreateTable, DropTable
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_role_column():
    # Connect to database
    with engine.connect() as connection:
        try:
            # Check if column exists
            check_stmt = text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='role'"
            )
            result = connection.execute(check_stmt)
            exists = result.fetchone() is not None

            if not exists:
                # Add role column if it doesn't exist
                add_column_stmt = text(
                    "ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'User' NOT NULL"
                )
                connection.execute(add_column_stmt)
                connection.commit()
                print("Column 'role' added successfully to users table.")
            else:
                print("Column 'role' already exists in users table.")
        except Exception as e:
            print(f"Error updating schema: {str(e)}")


def add_user_info_columns_to_posts():
    logger.info("Adding name and email columns to posts table")

    # Add name column
    with engine.connect() as connection:
        try:
            connection.execute(text("ALTER TABLE posts ADD COLUMN name VARCHAR(50);"))
            connection.commit()
            logger.info("Added name column to posts table")
        except Exception as e:
            connection.rollback()
            logger.error(f"Error adding name column: {e}")

    # Add email column (in a separate connection to avoid transaction issues)
    with engine.connect() as connection:
        try:
            connection.execute(text("ALTER TABLE posts ADD COLUMN email VARCHAR(100);"))
            connection.commit()
            logger.info("Added email column to posts table")
        except Exception as e:
            connection.rollback()
            logger.error(f"Error adding email column: {e}")


def update_existing_post_data():
    logger.info("Updating existing posts with user data")

    with engine.connect() as connection:
        try:
            # Update non-anonymous posts with user data
            update_query = text(
                """
                UPDATE posts
                SET name = users.name,
                    email = users.email
                FROM users
                WHERE posts.user_id = users.id
                AND posts.is_anonymous = false
                AND (posts.name IS NULL OR posts.email IS NULL)
            """
            )
            result = connection.execute(update_query)
            connection.commit()
            logger.info(f"Updated {result.rowcount} posts with user data")
        except Exception as e:
            logger.error(f"Error updating existing posts: {e}")


if __name__ == "__main__":
    add_role_column()
    add_user_info_columns_to_posts()
    update_existing_post_data()
    logger.info("Migration completed successfully")
