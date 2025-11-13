# Event Archiving System

## Overview

The archiving system manages event lifecycle through manual and automatic archiving before permanent deletion. Events are archived 1 day after ending and deleted 5 days after archiving. This provides a grace period for organizations to recover accidentally archived events before permanent deletion.

## Database Schema

**Location**: `database/schema.sql`

The Events table includes archiving columns that track status and timestamp. Two indexes optimize archiving queries and eligibility checks for automated tasks.

**Key Fields**:
- Archive status flag (boolean)
- Archive timestamp (datetime)
- Both fields indexed for query performance

## API Endpoints

**Location**: `server/app/routes.py`

### Archive Management
- **POST /events/{event_id}/archive** - Archive event (organization only)
- **GET /api/user/events/archived** - Retrieve archived events (organization only)
- **GET /api/user/events/organized** - Query parameter `include_archived` controls visibility

### Permanent Deletion
- **DELETE /events/{event_id}** - Bypass archiving for immediate deletion (organization only)

All endpoints verify user authorization and event ownership before performing operations.

## Archiving Logic

**Location**: `server/app/models.py`, `database/scheduled_archiving_tasks.sql`

### Manual Archiving
Organization users can archive their events anytime through the API. The system verifies user authorization and prevents duplicate archiving operations.

### Automatic Archiving
**SQL Script**: `database/scheduled_archiving_tasks.sql`  
**Frequency**: Daily (recommended: midnight)

A scheduled database task archives events that ended more than 1 day ago, updating the archive flag and timestamp.

### Permanent Deletion
**SQL Script**: `database/scheduled_archiving_tasks.sql`  
**Frequency**: Daily (recommended: midnight)

A scheduled database task permanently deletes events archived more than 5 days ago. Cascade delete constraints automatically remove related records (RSVPs, tags, recommendations).

### Event Lifecycle Timeline
- **Day 0**: Event ends
- **Day 1**: Automatically archived (if scheduled task configured)
- **Day 6**: Permanently deleted (if scheduled task configured)

## Model Layer

**Location**: `server/app/models.py`

### Event Model
The Event model provides methods for archiving operations and filtering. Key functionality includes:
- Archive event with authorization validation
- Query events with optional archived inclusion
- All query methods default to excluding archived events

All retrieval methods support an `include_archived` parameter to control visibility of archived events in results.

## Implementation

### Database Setup
1. Run migration script: `database/migration_add_archiving.sql`
2. Configure scheduled tasks for automated archiving/deletion

### Scheduled Tasks
**Location**: `database/run_archiving_task.bat`, `database/scheduled_archiving_tasks.sql`

Set up two daily SQL tasks (midnight recommended):
1. Auto-archive events ended >1 day ago
2. Permanently delete events archived >5 days ago

Use Windows Task Scheduler or cron to execute the batch file daily.

## Testing

**Location**: `server/tests/test_archiving.py`, `server/tests/test_routes.py`

The archiving system includes comprehensive test coverage at both model and API layers:
- Model layer: 15 tests covering archiving operations and query filtering
- API layer: 18 tests covering endpoints, authorization, and integration

## Troubleshooting

### Archived events appearing in queries
Verify `include_archived` parameter is set to false (default), check migration applied successfully

### Automatic archiving not running
Verify scheduled task is configured and running, check database user permissions and task logs

### Permanent deletion not occurring
Verify deletion task is configured and running, check cascade constraints and database locks on related tables
