# Consultant Invitation System

This document explains how the consultant invitation system works in the FemCare backend.

## Overview

The consultant invitation system allows administrators to invite healthcare professionals to join the platform as consultants. The system:

1. Sends an invitation email with a signup link
2. Automatically assigns the consultant role when the invited person signs up
3. Creates a basic consultant profile that can be completed later

## Flow

### 1. Admin Sends Invitation

An admin user sends an invitation to a potential consultant by providing their email address and a signup link. The system:

- Checks if the email is already registered
- Sends an invitation email with a signup link that includes a role parameter
- The signup link should point to the mobile app's signup page

Example API call:

```json
POST /consultants/send-invite
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "email": "doctor@example.com",
  "signup_link": "https://femcare-app.com/signup?email=doctor@example.com&role=consultant"
}
```

### 2. Consultant Receives Email

The consultant receives an email with:

- An invitation message
- A link to the mobile app signup page
- The link contains parameters to pre-fill the email and assign the consultant role

### 3. Consultant Signs Up

When the consultant clicks the link and completes the signup form:

1. The mobile app includes the `role=consultant` parameter in the signup request
2. The backend creates a new user with the consultant role
3. The backend also creates a basic consultant profile that can be completed later

Example API call from the mobile app:

```json
POST /auth/signup?role=consultant
Content-Type: application/json

{
  "name": "Dr. Jane Smith",
  "email": "doctor@example.com",
  "password": "secure_password",
  "phone": "1234567890",
  "language": "en"
}
```

### 4. Consultant Completes Profile

After signing up, the consultant can log in to the mobile app and complete their profile by updating:

- Specialty
- Bio
- Availability
- Other professional information

## API Endpoints

### Send Invitation

```
POST /consultants/send-invite
```

**Request Body:**
```json
{
  "email": "doctor@example.com",
  "signup_link": "https://femcare-app.com/signup?email=doctor@example.com&role=consultant"
}
```

**Response:**
```json
{
  "message": "Invitation sent successfully"
}
```

### Signup with Role

```
POST /auth/signup?role=consultant
```

**Request Body:**
```json
{
  "name": "Dr. Jane Smith",
  "email": "doctor@example.com",
  "password": "secure_password",
  "phone": "1234567890",
  "language": "en"
}
```

**Response:**
```json
{
  "id": "uuid-string",
  "name": "Dr. Jane Smith",
  "email": "doctor@example.com",
  "phone": "1234567890",
  "role": "consultant",
  "language": "en"
}
```

## Implementation Notes

- The invitation system uses the existing email service
- The consultant role is assigned during signup using a query parameter
- A basic consultant profile is created automatically
- Only admin users can send invitations

## Mobile App Integration

The mobile app should:

1. Provide an admin interface to invite consultants
2. Handle the signup link with pre-filled email and role parameters
3. Redirect consultants to complete their profile after signup
4. Show different interfaces based on user role 