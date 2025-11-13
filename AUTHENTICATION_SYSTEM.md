# Authentication & Authorization System

## Overview

The TownSquare authentication system uses Firebase Authentication for identity management combined with a custom two-tier authorization model. The system distinguishes between individual users (standard accounts) and organization users (privileged accounts) with different permission levels for event management.

## Architecture

**Backend**: `server/app/auth_utils.py`, `server/app/routes.py`, `server/app/models.py`  
**Frontend**: `client/src/auth/`, `client/src/firebase.js`

### Key Components
- Firebase Authentication for secure token-based identity verification
- Two-tier user system (individual vs organization)
- Custom route decorators for authorization enforcement
- Automatic user provisioning on first authentication
- Client-side AuthContext for state management

## User Types

### Individual Users (Default)
Standard accounts with read and participation permissions. Can browse events, RSVP, follow users, and manage their own profile. Cannot create or manage events.

### Organization Users
Privileged accounts with full event management capabilities. Includes all individual user permissions plus the ability to create, edit, archive, and delete events they organize.

**User Type Assignment**: Set during registration via `user_type` field. Stored in database Users table and used for authorization checks throughout the application.

## Authentication Flow

### Registration
1. User signs up through Firebase (email/password, Google, etc.)
2. Firebase returns ID token
3. Frontend sends token to `/api/auth/verify`
4. Backend verifies token with Firebase Admin SDK
5. New user record created in database
6. User data returned to frontend

### Login
1. User authenticates with Firebase
2. Firebase returns ID token
3. Frontend sends token to `/api/auth/verify`
4. Backend verifies token and retrieves existing user
5. User data returned to frontend

### Authenticated Requests
All protected API endpoints require an `Authorization: Bearer <token>` header. Backend decorators verify the token, extract the user ID, and enforce authorization rules before executing route logic.

## Backend Implementation

**Location**: `server/app/auth_utils.py`

### Authentication Decorators

#### @require_auth
Verifies user authentication for any user type. Extracts and validates Firebase ID token from request header, then injects the user's Firebase UID into the route function.

**Error Responses**: 401 (missing/invalid token), 500 (system error)

#### @require_organization
Extends @require_auth with additional authorization check. Verifies user is an organization account before allowing access. Injects both Firebase UID and user object into route function.

**Error Responses**: 401 (missing/invalid token), 404 (user not found), 403 (not an organization), 500 (system error)

## Database Schema

**Location**: `database/schema.sql`

### Users Table
Stores user profiles with Firebase UID as primary key. Critical fields include:
- Firebase UID (links to Firebase Authentication)
- User type (determines authorization level: 'individual' or 'organization')
- Organization name (optional, for organization users)
- Standard profile fields (username, email, bio, location)

Default user type is 'individual'. Authorization decorators query this field to enforce permissions.

## API Endpoints by Permission Level

**Location**: `server/app/routes.py`

### Public Endpoints
No authentication required. Includes event browsing, event details, and category/interest listings.

### Authenticated Endpoints (@require_auth)
Requires any authenticated user. Includes:
- User profile management
- RSVP operations
- Social features (follow/unfollow, friend feeds)
- User interests management
- Viewing organized/attending events

### Organization-Only Endpoints (@require_organization)
Requires organization user type. Includes:
- Event creation
- Event editing (must be organizer)
- Event archiving (must be organizer)
- Event deletion (must be organizer)
- Archived events retrieval

All organization endpoints verify both authentication and user type before granting access.

## User Model

**Location**: `server/app/models.py`

The User class represents authenticated users with methods for:
- Creating new user records
- Retrieving users by Firebase UID
- Updating user profiles
- Querying user relationships

User type defaults to 'individual' during creation. Authorization logic checks this field to determine permissions.

## Frontend Integration

**Location**: `client/src/firebase.js`, `client/src/auth/`

### Firebase Configuration
Firebase is initialized with project credentials and provides authentication methods for signup, login, and token management. The auth object is exported and used throughout the application.

### Authentication Flow
1. User authenticates through Firebase SDK
2. Firebase returns ID token
3. Token sent to backend `/api/auth/verify` endpoint
4. Backend verifies and returns user data
5. User data stored in application state

### Authenticated Requests
All API requests to protected endpoints include the Firebase ID token in the Authorization header. The Firebase SDK handles token refresh automatically.

## AuthContext Pattern

**Location**: `client/src/auth/AuthContext.jsx`

React Context provider that manages authentication state across the application. Key features:
- Listens for Firebase auth state changes
- Verifies tokens with backend on auth changes
- Stores user profile data including user type
- Provides `isOrganization` flag for UI conditional rendering
- Prevents rendering until auth state resolved

Components use the `useAuth()` hook to access current user data and authorization status.

## Protected Routes

**Location**: `client/src/auth/RequireAuth.jsx`

Route protection components that enforce authentication and authorization:

### RequireAuth
Wraps routes requiring any authenticated user. Redirects to login if not authenticated.

### RequireOrganization
Wraps routes requiring organization users. Redirects to login if not authenticated, or to unauthorized page if user is not an organization.

Both components wait for auth state to resolve before rendering or redirecting.

## Security Considerations

### Token Management
- Firebase ID tokens expire after 1 hour and are automatically refreshed by the SDK
- Tokens should never be stored in localStorage
- Production deployment requires HTTPS

### Best Practices
- Always verify tokens on backend (never trust frontend state)
- Use decorators for consistent authorization enforcement
- Log authentication failures for security monitoring
- Implement rate limiting on authentication endpoints
- Never expose Firebase Admin SDK credentials to frontend
- Never skip token verification on sensitive endpoints

### Firebase Admin SDK Setup
**Location**: `server/app/__init__.py`

Backend initialization requires Firebase Admin SDK with service account credentials. The credentials file path must be set in the `GOOGLE_APPLICATION_CREDENTIALS` environment variable.

## Testing

**Location**: `server/tests/test_routes.py`, `server/tests/test_auth_utils.py`

Authentication tests mock Firebase token verification and user retrieval to test authorization logic:
- Token verification for both valid and invalid tokens
- User type enforcement on organization-only endpoints
- Individual user restriction validation
- Error response handling for various failure scenarios

Tests use Python unittest.mock to patch Firebase SDK calls, allowing comprehensive testing without external dependencies.

## Common Error Responses

### 401 Unauthorized
Missing or invalid authorization token. Ensure Authorization header includes valid Bearer token. Token may have expired and needs refresh.

### 403 Forbidden
User authenticated but lacks required permissions. Typically occurs when individual user attempts organization-only operations.

### 404 Not Found
User not found in database despite valid Firebase authentication. Call `/api/auth/verify` to create user record.

## Troubleshooting

### "No authorization token provided"
Verify Authorization header is included in request with correct Bearer token format. Check token retrieval from Firebase SDK.

### "Invalid authorization token"
Verify Firebase Admin SDK initialized with correct credentials via `GOOGLE_APPLICATION_CREDENTIALS` environment variable. Ensure Firebase project IDs match between frontend and backend configurations.

### "Organization account required"
Check user's `user_type` field in database is set to 'organization'. Verify correct user type was specified during registration.

### User created but not found
Ensure `/api/auth/verify` endpoint called after Firebase signup to create database record. Verify database connection and Users table schema.

## User Type Management

### Promoting Users to Organization
User type can be updated directly in the database by setting the `UserType` field to 'organization'. Useful for promoting existing users who need event management capabilities.

### Bulk Updates
Multiple users can be promoted simultaneously, such as converting all users who have created events to organization accounts.

## Best Practices

### Backend
- Use `@require_auth` for endpoints requiring any authenticated user
- Use `@require_organization` for privileged operations
- Always validate Firebase UID matches resource owner for updates/deletes
- Log authentication failures for security auditing
- Keep Firebase Admin SDK credentials secure in environment variables

### Frontend
- Use Firebase SDK for all authentication operations
- Store user profile data in React Context
- Conditionally render UI elements based on user type
- Handle 401/403 errors with appropriate redirects
- Never store credentials in code or localStorage
