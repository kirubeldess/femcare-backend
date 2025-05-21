# Flutter Integration Guide: Messaging & Notifications

This guide provides Flutter developers with instructions on how to integrate the FemCare backend's messaging and notification features into their mobile application.

## Core Concepts

*   **Message Requests:** To ensure user privacy and consent, especially when initiating contact from shared content like "Vent Posts," users first send a "message request." The recipient must accept this request before direct messaging can begin.
*   **Conversations:** Once a message request is accepted, a dedicated conversation is established between the two users, allowing them to exchange messages freely.
*   **Database-Backed Notifications:** The backend uses a database to store notifications. The mobile app needs to periodically "poll" (ask the server) for new notifications for the current user.

## 1. Messaging Workflow

The typical flow for messaging involves handling requests, and then engaging in conversations.

### Step 1: Initiating a Conversation (Sending a Message Request)

When a user (User A) wants to message another user (User B), typically the owner of a Vent Post:

1.  **Attempt to Send a Message Request:**
    *   **Endpoint:** `POST /messages/requests`
    *   **Query Parameter:** `sender_id={userA_id}` (the ID of the user sending the request)
    *   **Request Body:**
        ```json
        {
          "receiver_id": "userB_id",
          "post_id": "vent-post-uuid-if-applicable", // Optional, if initiating from a vent post
          "initial_message": "Hello, I saw your vent post and would like to connect."
        }
        ```
    *   **Backend Logic & Response:**
        *   The backend first checks if a conversation already exists between User A and User B. If so, it will return an HTTP 400 error (e.g., `{"detail": "A conversation already exists between these users"}`). The app should interpret this as meaning direct messaging is already possible, and User A can proceed to **Step 3: Engaging in a Conversation** (likely by fetching existing conversations to find the relevant one).
        *   The backend also checks if User A already has a `pending` message request to User B for the same `post_id`. If so, it will return an HTTP 400 error (e.g., `{"detail": "A pending request already exists for this post"}`). The app should inform User A their previous request is still pending.
        *   If no existing conversation or duplicate pending request is found, a new message request is created with `status: "pending"`. The `receiver_id` (User B) will get a notification (see **Section 2: Notification Handling**).
        *   **Successful Response (201 Created):** Details of the newly created message request.
            ```json
            {
              "id": "new-request-uuid",
              "sender_id": "userA_id",
              "receiver_id": "userB_id",
              "post_id": "vent-post-uuid-if-applicable",
              "initial_message": "Hello, I saw your vent post and would like to connect.",
              "timestamp": "2023-10-28T12:00:00Z",
              "status": "pending"
            }
            ```
    *   **App Logic:**
        *   On success (201), inform User A that their request has been sent.
        *   On error (400 due to existing conversation), navigate User A to their conversations list or the existing conversation with User B.
        *   On error (400 due to pending request), inform User A their request is still pending.

### Step 2: Managing Received Message Requests (For the Recipient - User B)

When User B (the recipient) receives a message request:

1.  **Be Alerted via Notifications:**
    *   User B's app will learn about the new request by polling the notification endpoints (see **Section 2: Notification Handling**). The notification will contain a message like "User A wants to talk about your vent post" and `related_content_id` pointing to the `post_id` or `request_id`.

2.  **Fetch Details of Pending Message Requests:**
    *   To display a list of requests needing action:
    *   **Endpoint:** `GET /messages/requests/received/{userB_id}`
    *   **Response:** A list of message requests where User B is the receiver and `status` is `pending`.

3.  **Respond to a Message Request:**
    *   **Endpoint:** `POST /messages/requests/{request_id}/respond`
    *   **Query Parameter:** `user_id={userB_id}` (the ID of User B, who is responding)
    *   **Request Body:**
        ```json
        {
          "status": "accepted" // or "rejected"
        }
        ```
    *   **Backend Action & Notification:** Updates the message request's status.
        *   If `accepted`: A new conversation is created automatically by the backend. The original sender (User A) receives a notification that their request was accepted.
        *   If `rejected`: The original sender (User A) receives a notification that their request was rejected.
    *   **Response (200 OK):** Details of the updated message request (now with status `accepted` or `rejected`). The response here is actually a `NotificationResponse` for the sender, confirming the action taken.

### Step 3: Engaging in a Conversation

Once a message request is accepted (or if the initial `POST /messages/requests` call indicated a conversation already existed):

1.  **List Active Conversations:**
    *   **Endpoint:** `GET /messages/conversations/{current_user_id}`
    *   **Response:** A list of conversations for the `current_user_id`. Each item typically includes the other participant's details (`partner_id`, `partner_name`), the last message, and unread count.
        ```json
        [
          {
            "partner_id": "partner-user-uuid",
            "partner_name": "Partner User Name",
            "last_message": { /* ... details of last message ... */ },
            "unread_count": 0 // Example
          }
          // ... more conversations
        ]
        ```

2.  **Fetch Messages for a Specific Conversation:**
    *   **Endpoint:** `GET /messages/conversations/{conversation_id}/messages`
    *   **Query Parameter:** `user_id={current_user_id}` (Important: This helps the backend mark messages from the other user as `read` if `current_user_id` is the recipient in that context).
    *   **Response:** A list of messages in the thread, ordered chronologically.

3.  **Send a New Message in an Active Conversation:**
    *   **Endpoint:** `POST /messages/conversations/{conversation_id}/messages`
    *   **Query Parameter:** `sender_id={current_user_id}`
    *   **Request Body:**
        ```json
        {
          "content": "This is a new message in our conversation."
        }
        ```
    *   **Backend Action:** Creates the message. The recipient will receive a notification.
    *   **Response (201 Created):** Details of the sent message.

### Step 4: Updating Message Status (Marking as Read/Delivered)

*   **Automatic Read Status Update:** When fetching messages using `GET /messages/conversations/{conversation_id}/messages` with the `user_id` query parameter, the backend attempts to mark messages sent by the *other* user in that conversation as `read` if the provided `user_id` is the recipient.
*   **Explicit Status Update (Optional/Fallback):**
    *   **Endpoint:** `PATCH /messages/{message_id}`
    *   **Query Parameter:** `user_id={current_user_id}` (the user whose action is causing the status change, e.g., who read the message)
    *   **Request Body:**
        ```json
        {
          "status": "read" // or "delivered"
        }
        ```

## 2. Notification Handling (Polling)

The Flutter app needs to periodically ask the server for new notifications.

### Step 1: Fetching User Notifications

*   **Endpoint:** `GET /notifications/user/{current_user_id}`
*   **Query Parameters (Optional):**
    *   `skip={number}` (for pagination, default 0)
    *   `limit={number}` (for pagination, default 50)
    *   `is_read={true|false}` (to filter by read status)
*   **Response:** A list of notifications.
    ```json
    [
      {
        "id": "notification-uuid",
        "user_id": "current_user_id",
        "message": "User X sent you a new message request regarding 'Vent Post Title'.",
        "is_read": false,
        "timestamp": "2023-10-27T10:00:00Z",
        "related_content_type": "message", // e.g., "message" (for requests/new messages), "post"
        "related_content_id": "message-request-uuid-or-post-id" // ID to navigate
      }
      // ... more notifications
    ]
    ```
*   **App Logic:** Use `related_content_type` and `related_content_id` to navigate the user to the relevant screen (e.g., a specific message request, a conversation view, or a post).

### Step 2: Getting Unread Notification Count

*   **Endpoint:** `GET /notifications/user/{current_user_id}/count`
*   **Response:**
    ```json
    {
      "unread_count": 5
    }
    ```
*   **App Logic:** Useful for displaying a badge on a "Notifications" icon or tab.

### Step 3: Marking Notifications as Read

When a user views a notification or the content it links to:

1.  **Mark a Specific Notification as Read:**
    *   **Endpoint:** `PATCH /notifications/user/{current_user_id}/{notification_id}/read`
    *   **Request Body:** None needed.
    *   **Response (200 OK):** The updated notification details with `is_read: true`.

2.  **Mark All Notifications as Read:**
    *   **Endpoint:** `PATCH /notifications/user/{current_user_id}/read-all`
    *   **Request Body:** None needed.
    *   **Response (200 OK):** `{"marked_read": count_of_notifications_updated}`

### Step 4: Deleting a Notification (Optional Client-Side Action)

If you want to allow users to dismiss/delete notifications from their view:

*   **Endpoint:** `DELETE /notifications/user/{current_user_id}/{notification_id}`
*   **Response:** 204 No Content (on success).

## Recommended Polling Strategy for Notifications

1.  **On App Start / User Login:**
    *   Fetch the initial unread notification count (`GET .../count`) to update UI badges.
    *   Fetch the initial list of notifications (`GET /notifications/user/...`).

2.  **Periodically (e.g., every 30-60 seconds, or when the app comes to the foreground):**
    *   Fetch the unread notification count.
    *   If the count is greater than zero or has changed since the last poll, fetch the full list of notifications to update the UI.

3.  **When User Interacts with a Notification's Content:**
    *   After navigating the user to the content linked by `related_content_id`, mark that specific notification as read using `PATCH .../{notification_id}/read`.

This guide outlines the primary interactions a Flutter app will have with the backend messaging and notification APIs. For complete details on request/response schemas, error codes, and other specific parameters, refer to the main API documentation (`MESSAGING_SYSTEM_README.md` and `NOTIFICATION_SYSTEM_README.md`). 