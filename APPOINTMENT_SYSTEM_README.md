# FemCare Appointment System Integration Guide

## Overview

The FemCare Appointment System allows users to book consultation sessions with health professionals. The system manages consultant availability, appointment booking, and automated email reminders.

## API Endpoints

### Consultant Availability

- **GET** `/appointments/availability/consultant/{consultant_id}`
  - Get all available time slots for a specific consultant
  - Query parameters:
    - `from_date`: Filter slots after this date (optional)
    - `to_date`: Filter slots before this date (optional)
  - Protected: Requires authentication

- **POST** `/appointments/availability`
  - Create availability slots (for consultants/admins only)
  - Protected: Requires authentication with consultant/admin role

### Appointments

- **POST** `/appointments/`
  - Book an appointment
  - Protected: Requires authentication

- **GET** `/appointments/`
  - Get all appointments for the current user
  - Query parameters:
    - `status`: Filter by status (pending/confirmed/cancelled/completed)
  - Protected: Requires authentication

- **PUT** `/appointments/{appointment_id}/cancel`
  - Cancel an appointment
  - Protected: Requires user who booked or consultant/admin

## Data Models

### Appointment

```json
{
  "id": "string",
  "user_id": "string",
  "consultant_id": "string",
  "start_time": "2023-01-01T10:00:00",
  "end_time": "2023-01-01T11:00:00",
  "status": "confirmed",
  "notes": "string",
  "reminder_sent": false,
  "created_at": "2023-01-01T09:00:00",
  "updated_at": "2023-01-01T09:00:00"
}
```

### Availability Slot

```json
{
  "id": "string",
  "consultant_id": "string",
  "start_time": "2023-01-01T10:00:00",
  "end_time": "2023-01-01T11:00:00",
  "is_booked": false
}
```

## Integration Guide

### Authentication

All endpoints require authentication. Include the JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

### Booking Flow Implementation

1. **List Consultants**
   - Use `/consultants` endpoint to show available consultants
   - Display consultant details (name, specialty, etc.)

2. **View Available Slots**
   - When a user selects a consultant (like Dr. Aynalem Kassa in your UI)
   - Call `GET /appointments/availability/consultant/{id}` to get available slots
   - Group slots by date for the calendar view

3. **Calendar Integration**
   - Implement the calendar view as shown in image 2
   - Highlight dates with available slots
   - When a date is selected (e.g., May 17th), fetch available slots for that day

4. **Time Slot Selection**
   - Display available time slots (10:00 AM, 12:00 PM, etc.) as shown
   - Users select one time slot

5. **Reminder Setting**
   - Let users select reminder time (doesn't affect backend)
   - This can be stored client-side or implemented using push notifications

6. **Booking Confirmation**
   - When "Confirm" button is pressed:
   - Call `POST /appointments/` with:
     ```json
     {
       "consultant_id": "selected_consultant_id",
       "start_time": "selected_slot_start_time",
       "end_time": "selected_slot_end_time",
       "notes": "optional_notes"
     }
     ```

7. **Confirmation & Reminder**
   - The backend sends a confirmation email
   - The system will automatically send a reminder email based on appointment time

### Time Slot Display

For the "Select Time" view in image 1:
- Display slots by day: "Today", "Tomorrow", etc.
- Show count of available slots for each day
- When no slots are available, show "No slots available" and offer to check calendar

### Calendar View

For the calendar in image 2:
- Use a month view with navigation arrows
- Highlight dates with availability
- When a date is selected, show available time slots below
- Implement time slot selection with visual feedback

## Client-Side Considerations

1. **Date & Time Handling**
   - All times are in UTC format
   - Convert to local time zone for display
   - Format times according to locale

2. **Reminder UI**
   - The 25-minute reminder option shown in your UI would be handled client-side
   - You can use local notifications for this feature

3. **Error Handling**
   - Handle cases where a slot becomes unavailable during booking
   - Provide appropriate error messages

4. **Accessibility**
   - Ensure calendar and time selection are accessible
   - Follow the color scheme shown in mockups

5. **Navigation**
   - Implement back navigation from booking screens
   - Add confirmation dialogs before cancelling the booking process 