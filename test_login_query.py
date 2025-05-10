from database import get_db, engine, SessionLocal
from models.user import User
from sqlalchemy.orm import Session
import traceback


def test_login_query():
    """Test the login query that's failing."""
    print("Testing login query...")

    # First try with direct SQL
    try:
        from sqlalchemy import text

        with engine.connect() as conn:
            query = text(
                """
                SELECT users.id AS users_id, 
                       users.name AS users_name, 
                       users.email AS users_email, 
                       users.password AS users_password, 
                       users.phone AS users_phone, 
                       users.role AS users_role, 
                       users.language AS users_language, 
                       users.created_at AS users_created_at, 
                       users.updated_at AS users_updated_at
                FROM users
                WHERE users.email = :email
                LIMIT 1
            """
            )

            result = conn.execute(query, {"email": "test12@example.com"})
            row = result.fetchone()
            if row:
                print(f"Direct SQL query successful!")
                print(f"Found user with id: {row[0]}, role: {row[5]}")
            else:
                print("No users found with email: test12@example.com")
    except Exception as e:
        print(f"Direct SQL query error: {str(e)}")
        print(traceback.format_exc())

    print("\n" + "-" * 50 + "\n")

    # Now try with SQLAlchemy ORM
    try:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == "test12@example.com").first()
            if user:
                print(f"ORM query successful!")
                print(f"Found user with id: {user.id}, role: {user.role}")
            else:
                print("No users found with email: test12@example.com using ORM")
        finally:
            db.close()
    except Exception as e:
        print(f"ORM query error: {str(e)}")
        print(traceback.format_exc())

    print("\nTest complete.")


if __name__ == "__main__":
    test_login_query()
