from database import engine
from sqlalchemy import text
import sys


def check_users_table():
    # Connect to database
    with engine.connect() as connection:
        try:
            print(f"Python version: {sys.version}")
            print(f"SQLAlchemy version: {engine.dialect.driver}")

            # Get database version
            version_stmt = text("SELECT version()")
            version = connection.execute(version_stmt).scalar()
            print(f"Database version: {version}")

            # Get all columns in users table
            check_stmt = text(
                """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' 
                ORDER BY ordinal_position
            """
            )
            result = connection.execute(check_stmt)
            columns = [row[0] for row in result]

            print("\nUsers table columns:")
            for col in columns:
                print(f"- {col}")

            # Specifically check for role column
            role_check = "role" in columns
            print(f"\nRole column exists: {role_check}")

            # Check if there are any users in the table
            count_stmt = text("SELECT COUNT(*) FROM users")
            count_result = connection.execute(count_stmt).scalar()
            print(f"\nTotal users in table: {count_result}")

            if count_result > 0:
                # Try fetching a user with a direct query
                try:
                    test_query = text("SELECT * FROM users LIMIT 1")
                    user_result = connection.execute(test_query)
                    sample = user_result.mappings().first()
                    print("\nUser columns from direct query:")
                    print(", ".join(sample.keys()))
                except Exception as e:
                    print(f"\nError getting user with direct query: {str(e)}")

                # Try fetching a user by email (similar to the login query)
                try:
                    email_query = text(
                        "SELECT * FROM users WHERE email = :email LIMIT 1"
                    )
                    email_result = connection.execute(
                        email_query, {"email": "test12@example.com"}
                    )
                    email_user = email_result.mappings().first()
                    if email_user:
                        print("\nUser columns from email query:")
                        print(", ".join(email_user.keys()))
                    else:
                        print("\nNo user found with email: test12@example.com")
                except Exception as e:
                    print(f"\nError getting user by email: {str(e)}")

        except Exception as e:
            print(f"Error checking table: {str(e)}")


if __name__ == "__main__":
    check_users_table()
