# Femcare Backend API

A backend API for the Femcare application, Built with FastAPI and PostgreSQL.

## Features

- User authentication and management
- Post sharing (blogs, stories, events, biographies, anonymous venting)
- Messaging and conversations between users
- Communication with professional consultants
- AI consultations for health concerns using Google's Gemini AI
- Educational resources repository
- Emergency contacts database for SOS features
- SOS functionality for emergency situations

## Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL
- **Authentication**: Bcrypt for password hashing
- **AI Integration**: Google Gemini AI for health consultations
- **Documentation**: Swagger UI (automatic via FastAPI)

## API Endpoints

### Authentication
- `POST /auth/signup` - Register a new user
- `POST /auth/login` - User login
- `GET /auth/users` - Get all users
- `GET /auth/users/{user_id}` - Get user by ID

### Posts
- `POST /posts/` - Create a new post
- `GET /posts/` - Get all posts with filters
- `GET /posts/{post_id}` - Get a specific post
- `GET /posts/user/{user_id}` - Get all posts by a user

### Messages
- `POST /messages/` - Send a message
- `GET /messages/conversations/{user_id}` - Get user conversations
- `GET /messages/thread/{user_id}/{partner_id}` - Get message thread between users
- `PATCH /messages/{message_id}` - Update message status
- `GET /messages/vent-outreach/{post_id}` - Get messages related to a vent post

### Consultants
- `POST /consultants/` - Register a new consultant
- `GET /consultants/` - Get all consultants with filters
- `GET /consultants/{consultant_id}` - Get a specific consultant
- `PUT /consultants/{consultant_id}` - Update consultant information
- `GET /consultants/specialty/{specialty}` - Get consultants by specialty

### Consultant Messages
- `POST /consultant-messages/` - Send a message between users and consultants
- `GET /consultant-messages/thread` - Get message thread between user and consultant
- `GET /consultant-messages/user/{user_id}` - Get user's consultant conversations
- `GET /consultant-messages/consultant/{consultant_id}` - Get consultant's conversations

### AI Consultations
- `POST /ai-consultations/{user_id}` - Create a new AI consultation
- `GET /ai-consultations/types` - Get list of available consultation types   legal,health or mental-health
- `GET /ai-consultations/user/{user_id}` - Get a user's AI consultation history
- `PATCH /ai-consultations/{consultation_id}` - Update consultation with AI response
- `GET /ai-consultations/{consultation_id}` - Get a specific AI consultation

### Resources
- `POST /resources/` - Add a new educational resource
- `GET /resources/` - Get all resources with filters
- `GET /resources/{resource_id}` - Get a specific resource
- `PUT /resources/{resource_id}` - Update a resource
- `DELETE /resources/{resource_id}` - Delete a resource

### Emergency Contacts
- `POST /emergency-contacts/` - Add a new emergency contact
- `GET /emergency-contacts/` - Get all emergency contacts
- `GET /emergency-contacts/nearest` - Find nearest emergency contacts
- `GET /emergency-contacts/type/{type}` - Get contacts by type

### SOS
- `POST /sos/` - Create a new SOS alert
- `PATCH /sos/{sos_log_id}` - Update SOS status
- `GET /sos/active` - Get all active SOS alerts
- `GET /sos/user/{user_id}` - Get user's SOS history

## Setup and Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up PostgreSQL database
4. Configure database URL in `database.py`
5. Set up environment variables:
   - Create a `.env` file in the root directory
   - Add your Google API key: `GOOGLE_API_KEY=your_api_key_here`
6. Run the application:
   ```
   fastapi dev main.py
   ```

## AI Health Consultations

The application uses Google's Gemini AI to provide specialized consultations in three areas:

1. **Health Consultations**
   - Users can submit their symptoms for medical information
   - AI provides possible causes, management strategies, and when to seek care
   - Response includes appropriate disclaimers about medical information

2. **Legal Consultations**
   - Users can describe legal issues or questions
   - AI provides general legal information, relevant considerations, and documentation guidance
   - Response clarifies this is not legal advice and suggests appropriate legal professionals

3. **Mental Health Consultations**
   - Users can describe mental health concerns
   - AI provides information, coping strategies, and professional resource guidance
   - Response is compassionate and emphasizes the importance of professional care

All consultations are processed using Google's Gemini 2.0 Flash model and include appropriate disclaimers. 
Users can select their desired consultation type when creating a new consultation request.

Example usage:
```json
// Health consultation
POST /ai-consultations/
{
  "symptoms": "I have a headache and fever for 2 days",
  "consultation_type": "health"
}

// Legal consultation
POST /ai-consultations/
{
  "symptoms": "My landlord won't fix my heating",
  "consultation_type": "legal"
}

// Mental health consultation
POST /ai-consultations/
{
  "symptoms": "I've been feeling anxious and having trouble sleeping",
  "consultation_type": "mental_health"
}
```

## API Documentation

Once the server is running, you can access the auto-generated documentation at:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc 