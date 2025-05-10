# FemCare Backend

This is the backend API for the FemCare application. FemCare is a mobile platform dedicated to improving the health, safety, and overall well-being of women in Ethiopia through technology, community, and personalized support.

## Key Features

- **Secure Authentication**: JWT-based authentication with role-based access control
- **Posts & Venting System**: Anonymous or identified sharing of experiences
- **AI-Powered Consultations**: Health, legal, and mental health consultations in multiple languages
- **Emergency SOS System**: Location-based emergency alerts with SMS notifications
- **Offline Support**: Synchronization for content created while offline
- **Professional Consultants**: Access to verified health professionals
- **Multilingual Support**: Available in English, Amharic, and Afaan Oromo

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

### 2. Configure Environment Variables

1. Copy the `.env.example` file to `.env`:
   ```
   cp .env.example .env
   ```

2. Update the `.env` file with your actual credentials:
   ```
   # Database Connection
   DATABASE_URL=postgresql://postgres:YourPassword@127.0.0.1:5432/femcare

   # JWT Authentication
   JWT_SECRET_KEY=your_secure_secret_key_change_in_production
   
   # Google Gemini API (for AI consultations)
   GOOGLE_API_KEY=your_google_api_key_here
   
   # Twilio Configuration (for emergency SMS)
   TWILIO_ACCOUNT_SID=your_twilio_account_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
   TWILIO_PHONE_NUMBER=+12345678901
   ```

### 3. Python Environment Setup

1. **Create a virtual environment**:
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

You can run the application in two ways:

1. **Development mode with auto-reload**:
   ```
   python run.py
   ```

2. **Production mode**:
   ```
   python main.py
   ```

The API will be available at http://localhost:8080

## API Documentation

Once the server is running, you can access the API documentation at:
- http://localhost:8080/docs (Swagger UI)
- http://localhost:8080/redoc (ReDoc)

## Available Endpoints

### Authentication
- POST `/auth/signup` - Register a new user
- POST `/auth/login` - Login a user and receive JWT token
- GET `/auth/me` - Get current user profile
- POST `/auth/token` - OAuth2 compatible token endpoint

### Posts & Venting
- POST `/posts` - Create a new post/vent
- GET `/posts` - Get all posts
- GET `/posts/user/{user_id}` - Get posts by a specific user

### AI Consultations
- POST `/ai-consultations` - Request an AI consultation
- GET `/ai-consultations/user/me` - Get current user's consultations
- POST `/ai-consultations/offline` - Process offline consultations

### Emergency SOS
- POST `/sos` - Trigger an SOS alert
- POST `/sos/offline` - Process offline SOS alerts
- GET `/sos/user/me` - Get current user's SOS history

### Offline Synchronization
- POST `/sync` - Synchronize offline data
- GET `/sync/status` - Get server time for sync coordination

## Docker Deployment

You can also run the application using Docker:

1. **Build the Docker image**:
   ```
   docker build -t femcare-backend .
   ```

2. **Run the container**:
   ```
   docker run -p 8080:8080 --env-file .env femcare-backend
   ```

Alternatively, use Docker Compose:
```
docker-compose up
```

## Troubleshooting

1. **Database Connection Issues**:
   - Verify PostgreSQL is running
   - Check that the database credentials in `.env` are correct
   - Ensure the 'femcare' database exists

2. **JWT Authentication Issues**:
   - Ensure the JWT_SECRET_KEY is set in your `.env` file
   - Check the token expiration time if getting "token expired" errors

3. **AI Consultation Issues**:
   - Verify your Google Gemini API key is valid
   - Check the request format matches the API documentation

## Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request