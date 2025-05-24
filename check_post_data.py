from sqlalchemy import text
from database import engine
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_post_data():
    logger.info("Checking post data...")

    with engine.connect() as connection:
        try:
            # Query to check post data
            query = text(
                """
                SELECT 
                    p.id, 
                    p.title, 
                    p.is_anonymous, 
                    p.user_id, 
                    p.name, 
                    p.email,
                    u.name as user_name,
                    u.email as user_email
                FROM posts p
                LEFT JOIN users u ON p.user_id = u.id
                ORDER BY p.timestamp DESC
                LIMIT 5
            """
            )

            result = connection.execute(query)
            posts = result.fetchall()

            logger.info(f"Found {len(posts)} posts")

            for post in posts:
                logger.info(f"Post ID: {post.id}")
                logger.info(f"Title: {post.title}")
                logger.info(f"Is Anonymous: {post.is_anonymous}")
                logger.info(f"User ID: {post.user_id}")
                logger.info(f"Post Name: {post.name}")
                logger.info(f"Post Email: {post.email}")
                logger.info(f"User Name: {post.user_name}")
                logger.info(f"User Email: {post.user_email}")
                logger.info("-" * 40)

        except Exception as e:
            logger.error(f"Error checking post data: {e}")


if __name__ == "__main__":
    check_post_data()
