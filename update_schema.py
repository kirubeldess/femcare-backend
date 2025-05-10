from database import engine
from sqlalchemy import text


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


if __name__ == "__main__":
    add_role_column()
