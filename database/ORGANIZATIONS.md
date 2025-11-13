# Organization Support Implementation

This document describes the organization functionality that has been added to the TownSquare application.

## Overview

The organization system allows users to:
1. **Follow organizations** - Users can follow organizations they're interested in
2. **Join organizations** - Users can become members of organizations  
3. **Post events under organizations** - Events can optionally be associated with an organization

This implementation keeps things simple as requested, focusing on these three core features.

## Database Changes

### New Tables

1. **Organizations**
   - `OrgID` (Primary Key, Identity)
   - `Name` (Unique, required)
   - `Description` (Optional)
   - `CreatedAt`, `UpdatedAt` (Timestamps)

2. **UserOrgMemberships** (Many-to-many: Users ↔ Organizations)
   - `UserUID` (Foreign Key to Users)
   - `OrgID` (Foreign Key to Organizations)
   - `JoinedAt` (Timestamp)
   - Composite Primary Key: (UserUID, OrgID)

3. **UserOrgFollows** (Many-to-many: Users following Organizations)
   - `UserUID` (Foreign Key to Users)
   - `OrgID` (Foreign Key to Organizations)
   - `CreatedAt` (Timestamp)
   - Composite Primary Key: (UserUID, OrgID)

### Modified Tables

4. **Events** - Added optional `OrgID` field
   - Events can now optionally be posted under an organization
   - `OrgID` (Foreign Key to Organizations, nullable)

## API Endpoints

### Organization CRUD
- `GET /api/organizations` - Get all organizations
- `POST /api/organizations` - Create new organization (requires auth)
- `GET /api/organizations/{org_id}` - Get specific organization
- `PUT /api/organizations/{org_id}` - Update organization (requires auth)

### Organization Membership
- `POST /api/organizations/{org_id}/join` - Join organization (requires auth)
- `POST /api/organizations/{org_id}/leave` - Leave organization (requires auth)
- `GET /api/user/organizations` - Get user's organization memberships (requires auth)

### Organization Following
- `POST /api/organizations/{org_id}/follow` - Follow organization (requires auth)
- `POST /api/organizations/{org_id}/unfollow` - Unfollow organization (requires auth)
- `GET /api/user/followed-organizations` - Get followed organizations (requires auth)

### Organization Events
- `GET /api/organizations/{org_id}/events` - Get events posted under organization

### Modified Endpoints
- `POST /api/events` - Event creation now accepts optional `OrgID` field

## Model Changes

### New Classes
- **Organization** - Complete CRUD operations for organizations

### Enhanced Classes
- **User** - Added methods for org membership and following:
  - `join_organization()`, `leave_organization()`
  - `follow_organization()`, `unfollow_organization()`
  - `get_user_organizations()`, `get_followed_organizations()`
  - `is_organization_member()`, `is_following_organization()`

- **Event** - Enhanced to support organizations:
  - Added `org_id` parameter to constructor and methods
  - `get_events_by_organization()` method
  - Updated `create_event()` to accept `org_id`

## Migration

To apply these changes to an existing database:

1. Run the migration script: `/database/migrations/add_organizations.sql`
2. Test the functionality using: `/test_organizations.py`

## Usage Examples

### Creating an Organization
```json
POST /api/organizations
{
  "name": "Tech Meetup Group",
  "description": "A community for tech enthusiasts"
}
```

### Joining an Organization
```json
POST /api/organizations/1/join
```

### Creating an Event Under an Organization
```json
POST /api/events
{
  "Title": "Tech Talk: AI Trends",
  "Description": "Monthly tech talk",
  "StartTime": "2024-01-15T18:00:00",
  "EndTime": "2024-01-15T20:00:00",
  "Location": "Tech Hub",
  "CategoryID": 1,
  "OrgID": 1
}
```

## Key Design Decisions

1. **Separation of Membership vs Following**: 
   - Membership = active participation in organization
   - Following = interested in updates/events from organization

2. **Optional Organization Events**: 
   - Events can exist without organizations (personal events)
   - Events can be posted under organizations for official events

3. **Simple Permissions**: 
   - Any authenticated user can create organizations
   - Any user can join/leave organizations freely
   - Future: Could add admin roles, approval processes, etc.

4. **Cascading Deletes**: 
   - If organization is deleted, memberships/follows are automatically removed
   - Events posted under deleted orgs become personal events (OrgID = NULL)

## Testing

Use the provided test script to verify functionality:
```bash
python3 test_organizations.py
```

This will test all CRUD operations, membership, following, and event associations.