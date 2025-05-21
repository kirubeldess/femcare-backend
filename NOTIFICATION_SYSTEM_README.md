# Notification System Documentation

## Overview

This document provides details about the notification system implemented in the FemCare backend. The notification system uses a database-backed approach to store and retrieve notifications for users. This system integrates with the messaging workflow to notify users about message requests, conversation updates, and other important events.

## Database Schema

The notification system uses the following database schema:

```sql
CREATE TABLE notifications (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    message TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    related_content_type notificationcontenttype,
    related_content_id TEXT
);
```

Where `notificationcontenttype` is an enum with the following values:
- `post` - Notification related to a post
- `comment` - Notification related to a comment
- `message` - Notification related to messaging

## Notification Types

The notification system supports various types of notifications, including:

1. **Message Request Notifications**
   - When a user sends a message request to a vent post owner
   - When a message request is accepted or rejected

2. **Conversation Notifications**
   - When a user receives a new message in a conversation

3. **Other Notifications**
   - System announcements
   - Content moderation notifications

## API Endpoints

### User Notification Endpoints

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
  },
  // More notifications...
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

#### 3. Get a Specific Notification

```
GET /notifications/user/{user_id}/{notification_id}
```

**Response** (200 OK):
```json
{
  "id": "notification-uuid",
  "user_id": "user-uuid",
  "message": "Your message request was accepted",
  "is_read": false,
  "timestamp": "2023-06-14T12:34:56.789Z",
  "related_content_type": "message",
  "related_content_id": "conversation-uuid"
}
```

#### 4. Mark a Notification as Read

```
PATCH /notifications/user/{user_id}/{notification_id}/read
```

**Response** (200 OK):
```json
{
  "id": "notification-uuid",
  "user_id": "user-uuid",
  "message": "Your message request was accepted",
  "is_read": true,
  "timestamp": "2023-06-14T12:34:56.789Z",
  "related_content_type": "message",
  "related_content_id": "conversation-uuid"
}
```

#### 5. Mark All Notifications as Read

```
PATCH /notifications/user/{user_id}/read-all
```

**Response** (200 OK):
```json
{
  "marked_read": 5
}
```

#### 6. Delete a Notification

```
DELETE /notifications/user/{user_id}/{notification_id}
```

**Response** (204 No Content)

### Admin Notification Endpoints

#### 1. Get All Notifications (Admin)

```
GET /admin/notifications/
```

**Query Parameters**:
- `is_read`: Filter by read status (optional)
- `skip`: Number of items to skip (pagination)
- `limit`: Maximum number of items to return

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
  },
  // More notifications...
]
```

#### 2. Mark Notification as Read (Admin)

```
PATCH /admin/notifications/{notification_id}/read
```

**Response** (200 OK):
```json
{
  "id": "notification-uuid",
  "user_id": "user-uuid",
  "message": "You have a new message request",
  "is_read": true,
  "timestamp": "2023-06-14T12:34:56.789Z",
  "related_content_type": "message",
  "related_content_id": "message-request-uuid"
}
```

## Integration with Messaging System

The notification system is integrated with the messaging system in the following key areas:

### 1. Message Requests

When a user sends a message request to a vent post owner, a notification is created for the vent owner:

```python
send_notification(
    db=db,
    user_id=request.receiver_id,
    message=f"Someone wants to talk about your vent post",
    related_content_type=NotificationContentType.post,
    related_content_id=request.post_id,
)
```

### 2. Request Responses

When a vent owner accepts or rejects a message request, a notification is created for the requester:

```python
# For accepted requests
send_notification(
    db=db,
    user_id=message_request.sender_id,
    message="Your message request was accepted! You can now start chatting.",
    related_content_type=NotificationContentType.post,
    related_content_id=message_request.post_id,
)

# For rejected requests
send_notification(
    db=db,
    user_id=message_request.sender_id,
    message="Your message request was declined.",
    related_content_type=NotificationContentType.post,
    related_content_id=message_request.post_id,
)
```

### 3. New Messages

When a user receives a new message in a conversation, a notification is created:

```python
send_notification(
    db=db,
    user_id=recipient_id,
    message="You have a new message",
    related_content_type=NotificationContentType.message,
    related_content_id=conversation.request_id,
)
```

## Client Integration Guide

### 1. Setup for Mobile

Here's an example of how to implement notification polling in a mobile app:

```dart
class NotificationService {
  final String baseUrl;
  final String authToken;
  
  NotificationService({required this.baseUrl, required this.authToken});
  
  // Headers with auth token
  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer $authToken',
  };
  
  // Get unread notification count
  Future<int> getUnreadCount(String userId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/notifications/user/$userId/count'),
      headers: _headers,
    );
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['unread_count'];
    } else {
      throw Exception('Failed to get notification count');
    }
  }
  
  // Get user notifications
  Future<List<Notification>> getUserNotifications(
    String userId, {
    bool? isRead,
    int skip = 0,
    int limit = 20,
  }) async {
    final queryParams = {
      'skip': skip.toString(),
      'limit': limit.toString(),
    };
    
    if (isRead != null) {
      queryParams['is_read'] = isRead.toString();
    }
    
    final Uri uri = Uri.parse('$baseUrl/notifications/user/$userId')
      .replace(queryParameters: queryParams);
    
    final response = await http.get(
      uri,
      headers: _headers,
    );
    
    if (response.statusCode == 200) {
      final List<dynamic> data = jsonDecode(response.body);
      return data.map((item) => Notification.fromJson(item)).toList();
    } else {
      throw Exception('Failed to get notifications');
    }
  }
  
  // Mark notification as read
  Future<Notification> markAsRead(String userId, String notificationId) async {
    final response = await http.patch(
      Uri.parse('$baseUrl/notifications/user/$userId/$notificationId/read'),
      headers: _headers,
    );
    
    if (response.statusCode == 200) {
      return Notification.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to mark notification as read');
    }
  }
  
  // Mark all notifications as read
  Future<int> markAllAsRead(String userId) async {
    final response = await http.patch(
      Uri.parse('$baseUrl/notifications/user/$userId/read-all'),
      headers: _headers,
    );
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['marked_read'];
    } else {
      throw Exception('Failed to mark all notifications as read');
    }
  }
}
```

### 2. Polling for Notifications

Since the system uses a database-backed approach without WebSockets, clients should implement polling to check for new notifications. Here's an example:

```dart
class NotificationManager {
  final NotificationService _service;
  Timer? _pollingTimer;
  final String userId;
  
  NotificationManager({
    required NotificationService service,
    required this.userId,
  }) : _service = service;
  
  // Start polling for notifications
  void startPolling({Duration interval = const Duration(seconds: 30)}) {
    // Cancel any existing timer
    stopPolling();
    
    // Create a new timer
    _pollingTimer = Timer.periodic(interval, (_) => _checkForNotifications());
    
    // Do an immediate check
    _checkForNotifications();
  }
  
  // Stop polling
  void stopPolling() {
    _pollingTimer?.cancel();
    _pollingTimer = null;
  }
  
  // Check for notifications
  Future<void> _checkForNotifications() async {
    try {
      final count = await _service.getUnreadCount(userId);
      
      // If there are unread notifications, fetch them
      if (count > 0) {
        final notifications = await _service.getUserNotifications(
          userId,
          isRead: false,
        );
        
        // Process new notifications
        _processNotifications(notifications);
      }
    } catch (e) {
      print('Error checking for notifications: $e');
    }
  }
  
  // Process new notifications (display, handle actions, etc.)
  void _processNotifications(List<Notification> notifications) {
    for (final notification in notifications) {
      // Display local notification
      _showLocalNotification(notification);
      
      // Handle specific notification types if needed
      if (notification.relatedContentType == 'message') {
        // Update UI for new messages
      }
    }
  }
  
  // Show a local notification
  void _showLocalNotification(Notification notification) {
    // Use platform-specific notification APIs
    // e.g. flutter_local_notifications
  }
}
```

## Scaling Considerations

For high-traffic applications, consider the following scaling strategies:

1. **Database Indexing**: 
   - Ensure proper indexes on `user_id` and `is_read` columns
   - Consider additional indexes based on query patterns

2. **Notification Cleanup**: 
   - Implement a cleanup job to remove old notifications
   - Consider an archiving strategy for older notifications

3. **Batch Notifications**: 
   - For events that might generate multiple notifications, consider batching them
   - Example: "You have 5 new messages" instead of 5 separate notifications

## Migration

To update the database schema for notifications, run the `update_notification_schema.py` script:

```bash
python update_notification_schema.py
```

This script will:
1. Create the notifications table if it doesn't exist
2. Add the `user_id` column if it's missing
3. Add the `message` type to the `notificationcontenttype` enum

## Conclusion

The notification system provides a reliable way to inform users about important events in the messaging system. By using a database-backed approach, notifications are persisted and can be retrieved even if a user is offline when the notification is created.

For any questions or issues, please contact the development team. 