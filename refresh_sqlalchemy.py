from database import engine
from models.base import Base
from models.user import User
from sqlalchemy import inspect


def refresh_metadata():
    """Refresh the SQLAlchemy metadata to recognize any schema changes."""
    print("Refreshing SQLAlchemy metadata...")

    # First, check current state
    inspector = inspect(engine)
    columns = inspector.get_columns("users")
    print("\nCurrent columns in users table according to SQLAlchemy:")
    for col in columns:
        print(f"- {col['name']} ({col['type']})")

    # Check if role exists
    role_exists = any(col["name"] == "role" for col in columns)
    print(f"\nRole column exists according to SQLAlchemy: {role_exists}")

    # Force reflection of the metadata
    Base.metadata.reflect(engine)

    # Check again after reflection
    inspector = inspect(engine)
    columns = inspector.get_columns("users")
    print("\nColumns after metadata refresh:")
    for col in columns:
        print(f"- {col['name']} ({col['type']})")

    # Verify our User model is properly setup
    print("\nUser model attributes:")
    user_model_attrs = [
        attr for attr in dir(User) if not attr.startswith("_") and attr != "metadata"
    ]
    for attr in user_model_attrs:
        print(f"- {attr}")

    print("\nLet's test a simple query:")
    try:
        from sqlalchemy import text

        with engine.connect() as conn:
            result = conn.execute(text("SELECT id, email, role FROM users LIMIT 1"))
            row = result.fetchone()
            if row:
                print(f"Query successful! Found user with role: {row[2]}")
            else:
                print("No users found in database.")
    except Exception as e:
        print(f"Query error: {str(e)}")

    print(
        "\nRefresh complete. Please restart your application for changes to take effect."
    )


if __name__ == "__main__":
    refresh_metadata()
