# Messaging System Documentation

## Overview
This document provides comprehensive details about the messaging system implemented in the FemCare backend. The messaging system features a request-approval workflow for initial contact between users, with a special focus on vent posts. This README is intended for Flutter developers who need to integrate with this messaging system.

## Core Concepts

### Message Workflow
The messaging system follows this workflow:

1. **Initial Contact via Vent Post**:
   - When a user sees a vent post and wants to message the post owner
   - System checks if there's prior communication between these users
   - If no prior communication exists, a message request is created
   - Vent owner receives a notification about the message request

2. **Request Approval Process**:
   - Vent owner can accept or reject the message request
   - If accepted, regular messaging can begin between the users
   - If rejected, the requester cannot send messages to the vent owner

3. **Ongoing Communication**:
   - Once a message request is accepted or if prior communication exists
   - Users can freely message each other without further approval

### Message Statuses
Messages can have the following statuses:

| Status | Description |
|--------|-------------|
| `requested` | Initial message request waiting for approval |
| `accepted` | Message request that has been accepted |
| `rejected` | Message request that has been rejected |
| `sent` | Regular message that has been sent |
| `delivered` | Message that has been delivered to the recipient device |
| `read` | Message that has been read by the recipient |

## API Endpoints

### 1. Send a Message
```
POST /messages/
```

**Request Body**:
```json
{
  "content": "Hello, I saw your vent post and would like to connect.",
  "receiver_id": "user-uuid-here",
  "post_id": "vent-post-uuid-here" // Optional, for initial messages from a vent post
}
```

**Query Parameters**:
- `sender_id`: UUID of the message sender

**Response** (201 Created):
```json
{
  "id": "message-uuid",
  "content": "Hello, I saw your vent post and would like to connect.",
  "sender_id": "sender-uuid",
  "receiver_id": "receiver-uuid",
  "post_id": "vent-post-uuid",
  "timestamp": "2023-06-14T12:34:56.789Z",
  "status": "requested" // Or "sent" if prior communication exists
}
```

**Notes**:
- For new conversations from a vent post, status will be `requested`
- For existing conversations or non-vent messages, status will be `sent`
- The system automatically determines if a message request is needed

### 2. Get Message Requests

```
GET /messages/requests/{user_id}
```

**Response** (200 OK):
```json
[
  {
    "id": "message-uuid",
    "content": "Hello, I saw your vent post and would like to connect.",
    "sender_id": "sender-uuid",
    "receiver_id": "user-uuid",
    "post_id": "vent-post-uuid",
    "timestamp": "2023-06-14T12:34:56.789Z",
    "status": "requested"
  },
  // More message requests...
]
```

### 3. Respond to Message Request

```
POST /messages/requests/{request_id}/respond
```

**Request Body**:
```json
{
  "status": "accepted" // Or "rejected"
}
```

**Query Parameters**:
- `user_id`: UUID of the message receiver (vent owner)

**Response** (200 OK):
```json
{
  "id": "message-uuid",
  "content": "Hello, I saw your vent post and would like to connect.",
  "sender_id": "sender-uuid",
  "receiver_id": "user-uuid",
  "post_id": "vent-post-uuid",
  "timestamp": "2023-06-14T12:34:56.789Z",
  "status": "accepted" // Or "rejected"
}
```

### 4. Check if User Can Message Another User

```
GET /messages/can-message/{user_id}/{vent_owner_id}
```

**Response** (200 OK):
```json
{
  "can_message_directly": true,
  "pending_request": false,
  "request_rejected": false,
  "request_id": null
}
```

### 5. Get User Conversations

```
GET /messages/conversations/{user_id}
```

**Response** (200 OK):
```json
[
  {
    "partner_id": "user-uuid",
    "partner_name": "User Name",
    "last_message": {
      "id": "message-uuid",
      "content": "Hello there!",
      "sender_id": "user-uuid",
      "receiver_id": "partner-uuid",
      "post_id": null,
      "timestamp": "2023-06-14T12:34:56.789Z",
      "status": "read"
    },
    "unread_count": 0
  },
  // More conversations...
]
```

### 6. Get Message Thread Between Two Users

```
GET /messages/thread/{user_id}/{partner_id}
```

**Response** (200 OK):
```json
[
  {
    "id": "message1-uuid",
    "content": "Hello, how are you?",
    "sender_id": "user1-uuid",
    "receiver_id": "user2-uuid",
    "post_id": "vent-post-uuid",
    "timestamp": "2023-06-14T12:30:00.000Z",
    "status": "read"
  },
  {
    "id": "message2-uuid",
    "content": "I'm doing well, thanks for asking!",
    "sender_id": "user2-uuid",
    "receiver_id": "user1-uuid",
    "post_id": null,
    "timestamp": "2023-06-14T12:35:00.000Z",
    "status": "delivered"
  },
  // More messages...
]
```

### 7. Update Message Status

```
PATCH /messages/{message_id}
```

**Request Body**:
```json
{
  "status": "read" // Or "delivered"
}
```

**Response** (200 OK):
```json
{
  "id": "message-uuid",
  "content": "Message content",
  "sender_id": "sender-uuid",
  "receiver_id": "receiver-uuid",
  "post_id": null,
  "timestamp": "2023-06-14T12:34:56.789Z",
  "status": "read"
}
```

### 8. Admin-Only: Delete a Specific Message

```
DELETE /messages/{message_id}
```

**Authentication**:
- Requires admin authorization token

**Response** (204 No Content):
```json
{
  "status": "success",
  "detail": "Message deleted successfully"
}
```

### 9. Admin-Only: Delete a Message Thread

```
DELETE /messages/thread/{user_id}/{partner_id}
```

**Authentication**:
- Requires admin authorization token

**Response** (204 No Content):
```json
{
  "status": "success",
  "detail": "Deleted X messages between users"
}
```

### 10. Admin-Only: Delete All User Messages

```
DELETE /messages/user/{user_id}/all
```

**Authentication**:
- Requires admin authorization token

**Response** (204 No Content):
```json
{
  "status": "success",
  "detail": "Deleted X messages for user user-uuid"
}
```

### 11. Admin-Only: Delete Post-Related Messages

```
DELETE /messages/post/{post_id}/messages
```

**Authentication**:
- Requires admin authorization token

**Response** (204 No Content):
```json
{
  "status": "success",
  "detail": "Deleted X messages related to post post-uuid"
}
```

## Notification System

The messaging system uses a database-backed notification system to alert users about message requests, accepted/rejected requests, and new messages. Each notification is stored in the database and can be retrieved via REST endpoints.

### Notification Endpoints

#### 1. Get User Notifications

```
GET /notifications/user/{user_id}
```

**Query Parameters**:
- `skip`: Number of items to skip (pagination) - default: 0
- `limit`: Maximum number of items to return - default: 50
- `is_read`: Filter by read status (optional)

**Response** (200 OK):
```json
[
  {
    "id": "notification-uuid",
    "user_id": "user-uuid",
    "message": "You have a new message request",
    "is_read": false,
    "timestamp": "2023-06-14T12:34:56.789Z",
    "related_content_type": "message",
    "related_content_id": "message-request-uuid"
  }
]
```

#### 2. Get Notification Count

```
GET /notifications/user/{user_id}/count
```

**Response** (200 OK):
```json
{
  "unread_count": 5
}
```

#### 3. Mark a Notification as Read

```
PATCH /notifications/user/{user_id}/{notification_id}/read
```

#### 4. Mark All Notifications as Read

```
PATCH /notifications/user/{user_id}/read-all
```

For more details on the notification system, see the `NOTIFICATION_SYSTEM_README.md` document.

## Flutter Integration Guide

### Prerequisites
- Flutter SDK installed
- Dart HTTP package (`http` or `dio`)
- State management solution (Provider, Bloc, Riverpod, etc.)

### Installation

1. Add HTTP package to your `pubspec.yaml`:
```yaml
dependencies:
  http: ^1.1.0 # or dio: ^5.3.0
```

2. Create API service class for messages:

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class MessageService {
  final String baseUrl;
  final String authToken; // For authentication
  
  MessageService({required this.baseUrl, required this.authToken});
  
  // Headers with auth token
  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer $authToken',
  };
  
  // Send a message
  Future<Map<String, dynamic>> sendMessage({
    required String content,
    required String receiverId,
    String? postId,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/messages/?sender_id=$userId'), // Replace userId with actual ID
      headers: _headers,
      body: jsonEncode({
        'content': content,
        'receiver_id': receiverId,
        'post_id': postId,
      }),
    );
    
    if (response.statusCode == 201) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to send message: ${response.body}');
    }
  }
  
  // Other message-related methods...
  
  // Admin-only: Delete a message
  Future<void> deleteMessage(String messageId, String adminToken) async {
    final adminHeaders = {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $adminToken', // Admin token
    };
    
    final response = await http.delete(
      Uri.parse('$baseUrl/messages/$messageId'),
      headers: adminHeaders,
    );
    
    if (response.statusCode != 204) {
      throw Exception('Failed to delete message: ${response.body}');
    }
  }
  
  // Admin-only: Delete a message thread
  Future<void> deleteMessageThread(
    String userId,
    String partnerId,
    String adminToken,
  ) async {
    final adminHeaders = {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $adminToken', // Admin token
    };
    
    final response = await http.delete(
      Uri.parse('$baseUrl/messages/thread/$userId/$partnerId'),
      headers: adminHeaders,
    );
    
    if (response.statusCode != 204) {
      throw Exception('Failed to delete message thread: ${response.body}');
    }
  }
  
  // Admin-only: Delete all user messages
  Future<void> deleteAllUserMessages(
    String userId,
    String adminToken,
  ) async {
    final adminHeaders = {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $adminToken', // Admin token
    };
    
    final response = await http.delete(
      Uri.parse('$baseUrl/messages/user/$userId/all'),
      headers: adminHeaders,
    );
    
    if (response.statusCode != 204) {
      throw Exception('Failed to delete user messages: ${response.body}');
    }
  }
  
  // Admin-only: Delete post-related messages
  Future<void> deletePostRelatedMessages(
    String postId,
    String adminToken,
  ) async {
    final adminHeaders = {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $adminToken', // Admin token
    };
    
    final response = await http.delete(
      Uri.parse('$baseUrl/messages/post/$postId/messages'),
      headers: adminHeaders,
    );
    
    if (response.statusCode != 204) {
      throw Exception('Failed to delete post-related messages: ${response.body}');
    }
  }
}
```

### Admin Dashboard Integration Example

```dart
import 'package:flutter/material.dart';
import 'message_service.dart';

class AdminMessageModeration extends StatefulWidget {
  const AdminMessageModeration({Key? key}) : super(key: key);

  @override
  State<AdminMessageModeration> createState() => _AdminMessageModerationState();
}

class _AdminMessageModerationState extends State<AdminMessageModeration> {
  final MessageService _messageService = MessageService(
    baseUrl: 'https://your-api-url.com',
    authToken: 'your-regular-auth-token',
  );
  
  // Admin token should be securely stored and accessed
  final String _adminToken = 'your-admin-auth-token';
  
  // Sample user/message data for demonstration
  final TextEditingController _messageIdController = TextEditingController();
  final TextEditingController _userIdController = TextEditingController();
  final TextEditingController _partnerIdController = TextEditingController();
  final TextEditingController _postIdController = TextEditingController();
  
  Future<void> _showSuccessSnackbar(String message) async {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }
  
  Future<void> _showErrorSnackbar(String error) async {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(error),
        backgroundColor: Colors.red,
      ),
    );
  }
  
  Future<void> _deleteMessage() async {
    final messageId = _messageIdController.text.trim();
    if (messageId.isEmpty) {
      _showErrorSnackbar('Please enter a message ID');
      return;
    }
    
    try {
      await _messageService.deleteMessage(messageId, _adminToken);
      _messageIdController.clear();
      _showSuccessSnackbar('Message deleted successfully');
    } catch (e) {
      _showErrorSnackbar('Error: ${e.toString()}');
    }
  }
  
  Future<void> _deleteThread() async {
    final userId = _userIdController.text.trim();
    final partnerId = _partnerIdController.text.trim();
    
    if (userId.isEmpty || partnerId.isEmpty) {
      _showErrorSnackbar('Please enter both user IDs');
      return;
    }
    
    try {
      await _messageService.deleteMessageThread(
        userId,
        partnerId,
        _adminToken,
      );
      _userIdController.clear();
      _partnerIdController.clear();
      _showSuccessSnackbar('Message thread deleted successfully');
    } catch (e) {
      _showErrorSnackbar('Error: ${e.toString()}');
    }
  }
  
  Future<void> _deleteUserMessages() async {
    final userId = _userIdController.text.trim();
    
    if (userId.isEmpty) {
      _showErrorSnackbar('Please enter a user ID');
      return;
    }
    
    try {
      await _messageService.deleteAllUserMessages(
        userId,
        _adminToken,
      );
      _userIdController.clear();
      _showSuccessSnackbar('All user messages deleted successfully');
    } catch (e) {
      _showErrorSnackbar('Error: ${e.toString()}');
    }
  }
  
  Future<void> _deletePostMessages() async {
    final postId = _postIdController.text.trim();
    
    if (postId.isEmpty) {
      _showErrorSnackbar('Please enter a post ID');
      return;
    }
    
    try {
      await _messageService.deletePostRelatedMessages(
        postId,
        _adminToken,
      );
      _postIdController.clear();
      _showSuccessSnackbar('Post-related messages deleted successfully');
    } catch (e) {
      _showErrorSnackbar('Error: ${e.toString()}');
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Admin Message Moderation')),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Delete Single Message',
              style: Theme.of(context).textTheme.headline6,
            ),
            SizedBox(height: 8),
            TextField(
              controller: _messageIdController,
              decoration: InputDecoration(
                labelText: 'Message ID',
                border: OutlineInputBorder(),
              ),
            ),
            SizedBox(height: 8),
            ElevatedButton(
              onPressed: _deleteMessage,
              child: Text('Delete Message'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.red,
              ),
            ),
            
            SizedBox(height: 24),
            
            Text(
              'Delete Message Thread',
              style: Theme.of(context).textTheme.headline6,
            ),
            SizedBox(height: 8),
            TextField(
              controller: _userIdController,
              decoration: InputDecoration(
                labelText: 'User ID',
                border: OutlineInputBorder(),
              ),
            ),
            SizedBox(height: 8),
            TextField(
              controller: _partnerIdController,
              decoration: InputDecoration(
                labelText: 'Partner ID',
                border: OutlineInputBorder(),
              ),
            ),
            SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    onPressed: _deleteThread,
                    child: Text('Delete Thread'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red,
                    ),
                  ),
                ),
                SizedBox(width: 8),
                Expanded(
                  child: ElevatedButton(
                    onPressed: _deleteUserMessages,
                    child: Text('Delete All User Messages'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red.shade900,
                    ),
                  ),
                ),
              ],
            ),
            
            SizedBox(height: 24),
            
            Text(
              'Delete Post-Related Messages',
              style: Theme.of(context).textTheme.headline6,
            ),
            SizedBox(height: 8),
            TextField(
              controller: _postIdController,
              decoration: InputDecoration(
                labelText: 'Post ID',
                border: OutlineInputBorder(),
              ),
            ),
            SizedBox(height: 8),
            ElevatedButton(
              onPressed: _deletePostMessages,
              child: Text('Delete Post Messages'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.red,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
```

## Important Considerations

### Database Migrations
The messaging system requires specific enum values in the database. If you're integrating with an existing database, make sure to run the `update_message_schema.py` script to update the database schema.

### Error Handling
The Flutter code should handle these common errors:
- 403: No approved conversation exists (when trying to get message thread)
- 404: User or post not found
- 400: Invalid message request operation (e.g., rejecting an already accepted request)

### Security
- Ensure all requests include proper authentication
- Validate sender_id and user_id on the server side
- Implement rate limiting for message sending and request creation
- Admin-only endpoints must be properly secured with strong authentication

### Real-time Updates
For real-time messaging experience:
- The system uses a database-backed notification approach
- Implement polling on the client side to check for new notifications and messages
- Consider these polling intervals:
  - Frequent polling (5-10 seconds) when the messaging UI is open
  - Less frequent polling (30-60 seconds) when the app is in the foreground
  - Push notifications for background updates
- Example polling implementation:

```dart
class NotificationPoller {
  Timer? _timer;
  final NotificationService _notificationService;
  final String _userId;
  
  NotificationPoller(this._notificationService, this._userId);
  
  void startPolling({Duration interval = const Duration(seconds: 10)}) {
    stopPolling();
    _timer = Timer.periodic(interval, (_) => _checkForNotifications());
  }
  
  void stopPolling() {
    _timer?.cancel();
    _timer = null;
  }
  
  Future<void> _checkForNotifications() async {
    try {
      final count = await _notificationService.getUnreadCount(_userId);
      if (count > 0) {
        // Handle new notifications (show badge, update UI, etc.)
      }
    } catch (e) {
      print('Error checking notifications: $e');
    }
  }
}
```

## Testing the Integration

1. **Create a message request**:
   - Select a vent post and attempt to message the owner
   - Verify the request is created with 'requested' status

2. **Check message requests**:
   - Log in as the vent post owner
   - Verify the message request appears in the requests list

3. **Accept/reject the request**:
   - Accept a request and verify messaging is enabled
   - Reject a request and verify messaging is blocked

4. **Send and receive messages**:
   - Send messages between users with approved communication
   - Verify messages appear in both users' conversation lists
   - Test message status updates (delivered/read)

5. **Test notifications**:
   - Verify notifications are created when message requests are sent/received
   - Test marking notifications as read
   - Verify notification counts update correctly

6. **Admin moderation**:
   - Test admin-only delete endpoints with proper authorization
   - Verify messages are permanently removed from the database 