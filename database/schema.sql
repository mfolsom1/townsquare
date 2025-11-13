-- schema.sql: Azure SQL Database table definitions
-- TownSquare Database Schema

-- Users table
CREATE TABLE Users (
    FirebaseUID NVARCHAR(128) PRIMARY KEY, -- Firebase UID
    Username NVARCHAR(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL UNIQUE,
    Email NVARCHAR(320) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL UNIQUE,
    FirstName NVARCHAR(100),
    LastName NVARCHAR(100),
    Location NVARCHAR(200) NOT NULL,
    Bio NVARCHAR(1000),
    CreatedAt DATETIME2 DEFAULT GETDATE() NOT NULL,
    UpdatedAt DATETIME2 DEFAULT GETDATE() NOT NULL
);

-- EventCategories table (referenced by Events)
CREATE TABLE EventCategories (
    CategoryID INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(100) NOT NULL UNIQUE,
    Description NVARCHAR(MAX),
    Color CHAR(7) CHECK (Color LIKE '#[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]'), -- Hex color format
    CreatedAt DATETIME2 DEFAULT GETDATE() NOT NULL
);

-- Index for category lookups
CREATE INDEX idx_eventcategories_name ON EventCategories (Name);

-- Organizations table
CREATE TABLE Organizations (
    OrgID INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(100) NOT NULL UNIQUE,
    Description NVARCHAR(1000),
    CreatedAt DATETIME2 DEFAULT GETDATE() NOT NULL,
    UpdatedAt DATETIME2 DEFAULT GETDATE() NOT NULL
);

-- Index for organization name lookups
CREATE INDEX idx_organizations_name ON Organizations (Name);

-- Events table
CREATE TABLE Events (
    EventID INT IDENTITY(1,1) PRIMARY KEY,
    OrganizerUID NVARCHAR(128) NOT NULL,
    Title NVARCHAR(200) NOT NULL,
    Description NVARCHAR(MAX),
    StartTime DATETIME2 NOT NULL,
    EndTime DATETIME2 NOT NULL,
    Location NVARCHAR(300) NOT NULL,
    CategoryID INT NOT NULL,
    MaxAttendees INT CHECK (MaxAttendees IS NULL OR MaxAttendees >= 0),
    ImageURL NVARCHAR(500),
    OrgID INT NULL, -- Events can optionally be posted under an organization
    CreatedAt DATETIME2 DEFAULT GETDATE() NOT NULL,
    UpdatedAt DATETIME2 DEFAULT GETDATE() NOT NULL,
    CONSTRAINT chk_event_time CHECK (EndTime > StartTime),
    CONSTRAINT FK_Events_Organizer FOREIGN KEY (OrganizerUID) REFERENCES Users(FirebaseUID),
    CONSTRAINT FK_Events_Category FOREIGN KEY (CategoryID) REFERENCES EventCategories(CategoryID),
    CONSTRAINT FK_Events_Organization FOREIGN KEY (OrgID) REFERENCES Organizations(OrgID)
);

-- Indexes for Events
CREATE INDEX idx_events_organizer ON Events (OrganizerUID);
CREATE INDEX idx_events_category_starttime ON Events (CategoryID, StartTime);
CREATE INDEX idx_events_starttime ON Events (StartTime);
CREATE INDEX idx_events_organization ON Events (OrgID);

-- EventTags table
CREATE TABLE EventTags (
    TagID INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(50) NOT NULL UNIQUE,
    Description NVARCHAR(200),
    Color CHAR(7) CHECK (Color IS NULL OR Color LIKE '#[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]'), -- Hex color format, nullable
    CreatedAt DATETIME2 DEFAULT GETDATE() NOT NULL
);

-- Index for tag name lookups
CREATE INDEX idx_eventtags_name ON EventTags (Name);

-- EventTagAssignments table (many-to-many: Events <-> EventTags)
CREATE TABLE EventTagAssignments (
    EventID INT NOT NULL,
    TagID INT NOT NULL,
    CONSTRAINT PK_EventTagAssignments PRIMARY KEY (EventID, TagID),
    CONSTRAINT FK_EventTagAssignments_Event FOREIGN KEY (EventID) REFERENCES Events(EventID) ON DELETE CASCADE,
    CONSTRAINT FK_EventTagAssignments_Tag FOREIGN KEY (TagID) REFERENCES EventTags(TagID) ON DELETE CASCADE
);

-- Supporting index for reverse lookups
CREATE INDEX idx_eventtagassignments_tag_event ON EventTagAssignments (TagID, EventID);

-- Interests table
CREATE TABLE Interests (
    InterestID INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(100) NOT NULL UNIQUE,
    Description NVARCHAR(MAX),
    CreatedAt DATETIME2 DEFAULT GETDATE() NOT NULL
);

-- Index for interest name lookups
CREATE INDEX idx_interests_name ON Interests (Name);

-- UserInterests table (many-to-many: Users <-> Interests)
CREATE TABLE UserInterests (
    UserUID NVARCHAR(128) NOT NULL,
    InterestID INT NOT NULL,
    CONSTRAINT PK_UserInterests PRIMARY KEY (UserUID, InterestID),
    CONSTRAINT FK_UserInterests_User FOREIGN KEY (UserUID) REFERENCES Users(FirebaseUID) ON DELETE CASCADE,
    CONSTRAINT FK_UserInterests_Interest FOREIGN KEY (InterestID) REFERENCES Interests(InterestID) ON DELETE CASCADE
);

-- Supporting index for reverse lookups
CREATE INDEX idx_userinterests_interest_user ON UserInterests (InterestID, UserUID);

-- UserFriendRecommendations table for storing friend recs
CREATE TABLE UserFriendRecommendations (
    RecommendationID INT IDENTITY(1,1) PRIMARY KEY,
    UserUID NVARCHAR(128) NOT NULL,
    EventID INT NOT NULL,
    FriendUsername NVARCHAR(50) NOT NULL,
    FriendStatus NVARCHAR(20) NOT NULL CHECK (FriendStatus IN ('Going', 'Interested')),
    CreatedAt DATETIME2 DEFAULT GETDATE() NOT NULL,
    CONSTRAINT FK_UserFriendRecs_User FOREIGN KEY (UserUID) REFERENCES Users(FirebaseUID) ON DELETE CASCADE,
    CONSTRAINT FK_UserFriendRecs_Event FOREIGN KEY (EventID) REFERENCES Events(EventID) ON DELETE CASCADE
);

-- Index for quick retrieval
CREATE INDEX idx_userfriendrecs_user ON UserFriendRecommendations (UserUID, CreatedAt DESC);

-- SocialConnections table (follower/following relationships)
CREATE TABLE SocialConnections (
    FollowerUID NVARCHAR(128) NOT NULL,
    FollowingUID NVARCHAR(128) NOT NULL,
    CreatedAt DATETIME2 DEFAULT GETDATE() NOT NULL,
    CONSTRAINT PK_SocialConnections PRIMARY KEY (FollowerUID, FollowingUID),
    CONSTRAINT chk_no_self_follow CHECK (FollowerUID <> FollowingUID),
    CONSTRAINT FK_SocialConnections_Follower FOREIGN KEY (FollowerUID) REFERENCES Users(FirebaseUID) ON DELETE CASCADE,
    CONSTRAINT FK_SocialConnections_Following FOREIGN KEY (FollowingUID) REFERENCES Users(FirebaseUID)
);

-- Index for fetching a user's followers efficiently
CREATE INDEX idx_socialconnections_following_follower ON SocialConnections (FollowingUID, FollowerUID);

-- RSVPs table
CREATE TABLE RSVPs (
    RSVPID INT IDENTITY(1,1) PRIMARY KEY,
    UserUID NVARCHAR(128) NOT NULL,
    EventID INT NOT NULL,
    Status NVARCHAR(20) NOT NULL CHECK (Status IN ('Going', 'Interested', 'Not Going')),
    CreatedAt DATETIME2 DEFAULT GETDATE() NOT NULL,
    UpdatedAt DATETIME2 DEFAULT GETDATE() NOT NULL,
    CONSTRAINT UQ_RSVPs_UserEvent UNIQUE (UserUID, EventID), -- Prevent duplicate RSVPs for same user/event
    CONSTRAINT FK_RSVPs_User FOREIGN KEY (UserUID) REFERENCES Users(FirebaseUID) ON DELETE CASCADE,
    CONSTRAINT FK_RSVPs_Event FOREIGN KEY (EventID) REFERENCES Events(EventID) ON DELETE CASCADE
);

-- Indexes for RSVPs
CREATE INDEX idx_rsvps_event_status ON RSVPs (EventID, Status);
CREATE INDEX idx_rsvps_user ON RSVPs (UserUID);

-- UserActivity table
CREATE TABLE UserActivity (
    ActivityID INT IDENTITY(1,1) PRIMARY KEY,
    UserUID NVARCHAR(128) NOT NULL,
    ActivityType NVARCHAR(50) NOT NULL CHECK (ActivityType IN ('created_event', 'rsvp_event', 'viewed_event_details', 'followed_user', 'joined_interest')),
    TargetID INT, -- Polymorphic reference (no FK constraint)
    Description NVARCHAR(MAX),
    CreatedAt DATETIME2 DEFAULT GETDATE() NOT NULL,
    CONSTRAINT FK_UserActivity_User FOREIGN KEY (UserUID) REFERENCES Users(FirebaseUID) ON DELETE CASCADE
);

-- Indexes for UserActivity
CREATE INDEX idx_useractivity_user_created ON UserActivity (UserUID, CreatedAt DESC);
CREATE INDEX idx_useractivity_target ON UserActivity (TargetID);

-- UserOrgMemberships table (many-to-many: Users <-> Organizations)
CREATE TABLE UserOrgMemberships (
    UserUID NVARCHAR(128) NOT NULL,
    OrgID INT NOT NULL,
    JoinedAt DATETIME2 DEFAULT GETDATE() NOT NULL,
    CONSTRAINT PK_UserOrgMemberships PRIMARY KEY (UserUID, OrgID),
    CONSTRAINT FK_UserOrgMemberships_User FOREIGN KEY (UserUID) REFERENCES Users(FirebaseUID) ON DELETE CASCADE,
    CONSTRAINT FK_UserOrgMemberships_Org FOREIGN KEY (OrgID) REFERENCES Organizations(OrgID) ON DELETE CASCADE
);

-- Supporting index for reverse lookups
CREATE INDEX idx_userorgs_org_user ON UserOrgMemberships (OrgID, UserUID);

-- UserOrgFollows table (many-to-many: Users following Organizations)
CREATE TABLE UserOrgFollows (
    UserUID NVARCHAR(128) NOT NULL,
    OrgID INT NOT NULL,
    CreatedAt DATETIME2 DEFAULT GETDATE() NOT NULL,
    CONSTRAINT PK_UserOrgFollows PRIMARY KEY (UserUID, OrgID),
    CONSTRAINT FK_UserOrgFollows_User FOREIGN KEY (UserUID) REFERENCES Users(FirebaseUID) ON DELETE CASCADE,
    CONSTRAINT FK_UserOrgFollows_Org FOREIGN KEY (OrgID) REFERENCES Organizations(OrgID) ON DELETE CASCADE
);

-- Supporting index for reverse lookups
CREATE INDEX idx_userorgfollows_org_user ON UserOrgFollows (OrgID, UserUID);