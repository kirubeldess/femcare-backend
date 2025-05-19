# FemCare Backend

This is the backend API for the FemCare application. This README provides complete setup instructions for getting the project running from scratch.

## Prerequisites

Before setting up the project, ensure you have the following installed:

1. **Python 3.8+**: Download from [python.org](https://www.python.org/downloads/)
2. **PostgreSQL**: Download from [postgresql.org](https://www.postgresql.org/download/)
3. **Git** (optional): Download from [git-scm.com](https://git-scm.com/downloads)

## Setup Instructions

### 1. Database Setup

1. Install PostgreSQL if you haven't already
2. Create a new database named 'femcare':
   ```
   psql -U postgres
   CREATE DATABASE femcare;
   \q
   ```
3. Note your PostgreSQL credentials (username, password) for the next step

### 2. Configure Database Connection

1. Open `database.py` and update the DATABASE_URL if necessary:
   ```python
   DATABASE_URL = "postgresql://postgres:YourPassword@127.0.0.1:5432/femcare"
   ```
   Replace `YourPassword` with your actual PostgreSQL password.

### 3. Python Environment Setup

1. **Create a virtual environment** (if not already present):
   ```
   python -m venv venv
   ```

2. **Activate the virtual environment**:
   - Windows:
     ```
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     source venv/bin/activate
     ```

3. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

## Running the Application

You can run the application in three ways:

1. **Using Python directly**:
   ```
   python main.py
   ```

2. **Using the run script**:
   ```
   python run.py
   ```

3. **Using Docker (recommended)**:
   ```
   docker-compose up --build
   ```

The API will be available at http://localhost:8000

## Docker Setup

The application is containerized using Docker for easier deployment and consistency across environments.

### Prerequisites for Docker setup
- Docker: Install from [docker.com](https://www.docker.com/get-started)
- Docker Compose: Usually included with Docker Desktop

### Running with Docker

1. **Build and start the containers**:
   ```
   docker-compose up --build
   ```
   The `--build` flag ensures that Docker rebuilds the images if any changes have been made.

2. **Run in detached mode** (in the background):
   ```
   docker-compose up -d
   ```

3. **Stop the containers**:
   ```
   docker-compose down
   ```

4. **View logs**:
   ```
   docker-compose logs -f
   ```

### Note about database persistence
By default, the Docker setup does not include a database service. You'll need to:
- Use your locally installed PostgreSQL database (set up as described above)
- Or uncomment the database service section in `docker-compose.yml` to enable a containerized database
- Ensure you update the database connection string to point to the correct host

## API Documentation

Once the server is running, you can access the API documentation at:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

## Available Endpoints

### Authentication
- POST `/auth/signup` - Register a new user
- POST `/auth/login` - Login a user
- GET `/auth/users/check` - Check registered users (for testing)

## Example API Usage

### User Registration (Signup)

**Endpoint**: POST `/auth/signup`

**Request Body**:
```json
{
  "name": "Test User",
  "email": "user@example.com",
  "password": "securepassword123",
  "emergency_contact": "+251987654321",
  "phone": "+251912345678",    // optional
  "latitude": 9.0222,          // optional
  "longitude": 38.7468,        // optional
  "language": "en"             // optional
}
```

### User Login

**Endpoint**: POST `/auth/login`

**Request Body**:
```json
{
  "email": "user@example.com", 
  "password": "securepassword123"
}
```

## Troubleshooting

1. **Database Connection Issues**:
   - Verify PostgreSQL is running
   - Check that the database credentials in `database.py` are correct
   - Ensure the 'femcare' database exists

2. **Package Installation Issues**:
   - If you encounter errors installing psycopg2, you may need to install PostgreSQL development libraries:
     - Windows: Ensure you installed PostgreSQL with the development components
     - Ubuntu/Debian: `sudo apt-get install libpq-dev python3-dev`
     - macOS: `brew install postgresql`

3. **Port Conflicts**:
   - If port 8000 is already in use, modify the port in `main.py`, `run.py`, and `docker-compose.yml`

4. **Docker Issues**:
   - If you encounter "permission denied" errors when running Docker commands, make sure your user is in the docker group
   - If containers fail to start, check Docker logs with `docker-compose logs`
   - For Windows path issues with volumes, make sure you're using the correct path format in docker-compose.yml

## Recent Feature Enhancements (as of May 2025)

This section highlights significant features and updates recently integrated into the FemCare backend:

### 1. Venting Platform & Moderation (VNT)

*   **Anonymous Vent Posts:** Users can create anonymous text-based posts.
*   **Enhanced Moderation Workflow:**
    *   Vent posts and their comments now undergo a moderation process if potentially inappropriate content (profanity) is detected using an LLM.
    *   Content status can be `pending_approval`, `approved`, or `rejected`.
    *   Admins have dedicated endpoints (`/admin/moderation/*`) to review and approve/reject content.
    *   Users (excluding authors/admins) can only view `approved` vent posts and comments.
*   **Reactions:** Likes and threaded comments are supported on vent posts.

### 2. Community Content & Highlights (CCH)

*   **Admin-Published Content:** A separate module for admins to publish content like blogs, inspirational stories, event announcements, and biographies.
    *   Managed via `/community-content/*` endpoints (admin-only creation).
    *   Uses a distinct `CommunityContentPost` model, which supports an `images` field (list of image URLs) for rich content.
    *   This content is not subject to the user-centric moderation workflow.

### 3. Educational Resources (EDR)

*   **Expanded Resource Types:** The `Resource` model now supports `article`, `video`, `pdf`, and `external_link` types, with fields for `file_url` and richer metadata.
*   **Improved Search & Filtering:** Resources can be searched by keyword and filtered by type.
*   **Bookmarking:** Users can bookmark educational resources for easy access (`/resources/bookmarks/*` and `/resources/users/me/bookmarks`).
*   **Admin Management:** CUD (Create, Update, Delete) operations for resources are restricted to admin users.

### 4. Admin User Management

*   **Enhanced Admin Controls:**
    *   Admins can create other admin users (`POST /admin/users/create-admin`).
    *   Admins can change user roles (`PUT /admin/users/{user_id}/role`).
*   **Initial Admin Setup:** A one-time endpoint (`POST /auth/create-initial-admin`) is available to create the first admin user if no admin exists.

### 5. Admin Notification System

*   **Automated Alerts:** Admins are automatically notified when new vent posts or comments are flagged and require moderation.
*   **Notification Management:**
    *   Admins can list all notifications, filter by read/unread status (`GET /admin/notifications/`).
    *   Admins can mark notifications as read (`PATCH /admin/notifications/{notification_id}/read`).

### 6. General Enhancements & Fixes

*   **Database Schema Updates:** Added `updated_at` timestamps to `Post` and `Comment` models, and `status` to `Comment` for the moderation workflow. Note: Manual database alterations (e.g., `ALTER TABLE`) or migration tools (like Alembic) are necessary to apply these schema changes to existing databases, as `Base.metadata.create_all()` does not modify existing tables.
*   **Pydantic V2 Compatibility:** Updated model validators (e.g., `@root_validator` to `@model_validator(mode='after')`).

This summary covers the main functional areas developed and refined. For detailed API specifications, refer to the `/docs` endpoint when the application is running. 