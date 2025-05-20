# Using the Unified AI Chatbot in Your Mobile App

This guide explains how your Flutter (or any mobile) app should interact with the unified AI chatbot feature, supporting per-user chat histories.

---

## 1. Start or Continue a Chat Session

- When a user opens the AI chat:
  - Check if there's an open (active) `AIConsultation` session for the user.
  - If not, create a new session:
    ```http
    POST /ai-consultations/
    {
      "user_id": "<user_id>",
      "initial_message": "Hi" // optional
    }
    ```
  - Store the returned `consultation_id` (session ID) for all future messages in this chat.

---

## 2. Send a Message

- When the user sends a message:
  - POST to `/ai-consultations/{consultation_id}/message`
  - Body:
    ```json
    {
      "message": "Your message here"
    }
    ```
  - The backend will:
    - Save the user message to `AIConsultationMessage`.
    - Call the LLM service with the chat history as context.
    - Save the AI's reply to `AIConsultationMessage`.
    - Return the AI's reply to the app.

---

## 3. Display Chat History

- When the chat screen loads (or when you want to refresh):
  - GET `/ai-consultations/{consultation_id}/messages`
  - The backend returns all messages for that session, e.g.:
    ```json
    [
      {
        "sender": "user",
        "content": "Hi",
        "timestamp": "2025-05-21T10:00:00"
      },
      {
        "sender": "ai",
        "content": "Hello! How can I help you today?",
        "timestamp": "2025-05-21T10:00:01"
      }
    ]
    ```
  - Display these in a chat UI (e.g., bubbles, with sender and timestamp).

---

## 4. Session Management

- Allow users to:
  - Continue an existing session (show previous chat).
  - Start a new session (create a new `AIConsultation`).

---

## 5. Authentication

- All requests must include the user's JWT token in the `Authorization` header.

---

## 6. Example Flutter Pseudocode

```dart
// Start or continue a session
final sessionResponse = await http.post(
  Uri.parse('$apiUrl/ai-consultations/'),
  headers: {'Authorization': 'Bearer $token'},
  body: jsonEncode({'user_id': userId}),
);
final consultationId = jsonDecode(sessionResponse.body)['session_id'];

// Send a message
final aiResponse = await http.post(
  Uri.parse('$apiUrl/ai-consultations/$consultationId/message'),
  headers: {'Authorization': 'Bearer $token'},
  body: jsonEncode({'message': 'Tell me about nutrition'}),
);
final aiReply = jsonDecode(aiResponse.body)['content'];

// Get chat history
final historyResponse = await http.get(
  Uri.parse('$apiUrl/ai-consultations/$consultationId/messages'),
  headers: {'Authorization': 'Bearer $token'},
);
final messages = jsonDecode(historyResponse.body); // List of messages
```

---

## 7. Summary

- The app always talks to the same AI (LLM) backend.
- Each user's chat history is stored and retrieved by their session.
- The app can display, continue, or start new chat sessions as needed.

---

**For more details, see the backend API documentation or contact the backend team.** 