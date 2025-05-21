# Message Moderation Guide for FemCare Platform

## Overview

This guide provides instructions for administrators to moderate user messages in the FemCare platform. The messaging system follows a request-based workflow specifically for vent posts, and this document outlines the tools and processes for effective content moderation.

## Moderation Responsibilities

As a moderator, your responsibilities include:

1. Reviewing reported messages for harmful content
2. Removing inappropriate content when necessary
3. Handling user complaints about messaging
4. Enforcing community guidelines in private communications
5. Ensuring GDPR compliance by removing user data upon request

## Admin-Only Endpoints

### 1. Delete a Specific Message

```
DELETE /messages/{message_id}
```

**Usage**: When a specific message contains inappropriate content but the conversation should continue.

**Parameters**:
- `message_id`: The UUID of the message to delete

**Response**: 204 No Content on success

**Example**:
```bash
curl -X DELETE https://api.femcare.com/messages/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### 2. Delete a Message Thread

```
DELETE /messages/thread/{user_id}/{partner_id}
```

**Usage**: When an entire conversation between two users violates guidelines.

**Parameters**:
- `user_id`: The UUID of the first user
- `partner_id`: The UUID of the second user

**Response**: 204 No Content on success

**Example**:
```bash
curl -X DELETE https://api.femcare.com/messages/thread/user-id-1/user-id-2 \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### 3. Delete All User Messages

```
DELETE /messages/user/{user_id}/all
```

**Usage**: 
- When a user requests removal of all their data (GDPR compliance)
- When a user account is suspended or terminated

**Parameters**:
- `user_id`: The UUID of the user whose messages should be deleted

**Response**: 204 No Content on success

**Example**:
```bash
curl -X DELETE https://api.femcare.com/messages/user/user-id/all \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### 4. Delete Post-Related Messages

```
DELETE /messages/post/{post_id}/messages
```

**Usage**: When a vent post is removed and all related messages should be deleted.

**Parameters**:
- `post_id`: The UUID of the post whose messages should be deleted

**Response**: 204 No Content on success

**Example**:
```bash
curl -X DELETE https://api.femcare.com/messages/post/post-id/messages \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

## Moderation Process

### Handling User Reports

1. When a user reports a message:
   - Review the reported message content
   - Check context by examining other messages in the thread
   - Make a decision based on community guidelines

2. Actions to take:
   - **No violation**: Mark report as resolved with no action
   - **Minor violation**: Delete the specific message
   - **Serious violation**: Delete the entire thread
   - **Repeated violations**: Consider user account restrictions

### GDPR Compliance

When a user requests deletion of their data:

1. Verify the user's identity
2. Use the `/messages/user/{user_id}/all` endpoint to remove all messaging data
3. Document the deletion request and completion
4. Send confirmation to the user

### Audit Trail

All moderation actions are logged with:
- Moderator ID
- Action taken
- Timestamp
- Reason code

Access the moderation logs through the admin dashboard to review recent actions.

## Community Guidelines for Private Messages

Private messages on FemCare must comply with these guidelines:

1. **No harassment or threats**
2. **No hate speech or discrimination**
3. **No explicit sexual content**
4. **No unsolicited medical advice**
5. **No sharing of personal contact information**
6. **No spam or commercial solicitation**
7. **No impersonation of medical professionals**

## Response Templates

### Message Removed Notification

```
Your message has been removed because it violates our community guidelines regarding [REASON].
Please review our guidelines at [LINK]. Repeated violations may result in account restrictions.
```

### Thread Removed Notification

```
A conversation you participated in has been removed due to content that violates our community guidelines.
Please review our guidelines at [LINK] to ensure future communications comply.
```

## Support Contacts

If you have questions about moderation decisions:
- Email: moderation@femcare.com
- Internal chat: #team-moderation
- Weekly moderation team call: Thursdays at 10:00 AM

## Escalation Process

For sensitive issues requiring immediate attention:
1. Tag the conversation as "Urgent" in the moderation queue
2. Notify the lead moderator via the #urgent-mod-issues channel
3. Document the escalation in the case notes

---

Remember: The goal of moderation is to ensure a safe, supportive environment for all users, while respecting privacy and focusing particularly on protecting vulnerable users sharing sensitive health experiences. 