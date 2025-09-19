-- schema.sql: Azure SQL Database table definitions
-- TownSquare Database Schema

-- Users table
CREATE TABLE Users (
    UserID INT IDENTITY(1,1) PRIMARY KEY,
    Username NVARCHAR(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL UNIQUE,
    Email NVARCHAR(320) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL UNIQUE,
    PasswordHash CHAR(64) NOT NULL, -- SHA-256 produces 64 hex characters
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

-- Events table
CREATE TABLE Events (
    EventID INT IDENTITY(1,1) PRIMARY KEY,
    OrganizerID INT NOT NULL,
    Title NVARCHAR(200) NOT NULL,
    Description NVARCHAR(MAX),
    StartTime DATETIME2 NOT NULL,
    EndTime DATETIME2 NOT NULL,
    Location NVARCHAR(300) NOT NULL,
    CategoryID INT NOT NULL,
    MaxAttendees INT CHECK (MaxAttendees IS NULL OR MaxAttendees >= 0),
    ImageURL NVARCHAR(500),
    CreatedAt DATETIME2 DEFAULT GETDATE() NOT NULL,
    UpdatedAt DATETIME2 DEFAULT GETDATE() NOT NULL,
    CONSTRAINT chk_event_time CHECK (EndTime > StartTime),
    CONSTRAINT FK_Events_Organizer FOREIGN KEY (OrganizerID) REFERENCES Users(UserID),
    CONSTRAINT FK_Events_Category FOREIGN KEY (CategoryID) REFERENCES EventCategories(CategoryID)
);

-- Indexes for Events
CREATE INDEX idx_events_organizer ON Events (OrganizerID);
CREATE INDEX idx_events_category_starttime ON Events (CategoryID, StartTime);
CREATE INDEX idx_events_starttime ON Events (StartTime);

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
    UserID INT NOT NULL,
    InterestID INT NOT NULL,
    CONSTRAINT PK_UserInterests PRIMARY KEY (UserID, InterestID),
    CONSTRAINT FK_UserInterests_User FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE,
    CONSTRAINT FK_UserInterests_Interest FOREIGN KEY (InterestID) REFERENCES Interests(InterestID) ON DELETE CASCADE
);

-- Supporting index for reverse lookups
CREATE INDEX idx_userinterests_interest_user ON UserInterests (InterestID, UserID);

-- SocialConnections table (follower/following relationships)
CREATE TABLE SocialConnections (
    FollowerID INT NOT NULL,
    FollowingID INT NOT NULL,
    CreatedAt DATETIME2 DEFAULT GETDATE() NOT NULL,
    CONSTRAINT PK_SocialConnections PRIMARY KEY (FollowerID, FollowingID),
    CONSTRAINT chk_no_self_follow CHECK (FollowerID <> FollowingID),
    CONSTRAINT FK_SocialConnections_Follower FOREIGN KEY (FollowerID) REFERENCES Users(UserID) ON DELETE CASCADE,
    CONSTRAINT FK_SocialConnections_Following FOREIGN KEY (FollowingID) REFERENCES Users(UserID)
);

-- Index for fetching a user's followers efficiently
CREATE INDEX idx_socialconnections_following_follower ON SocialConnections (FollowingID, FollowerID);

-- RSVPs table
CREATE TABLE RSVPs (
    RSVPID INT IDENTITY(1,1) PRIMARY KEY,
    UserID INT NOT NULL,
    EventID INT NOT NULL,
    Status NVARCHAR(20) NOT NULL CHECK (Status IN ('Going', 'Interested', 'Not Going')),
    CreatedAt DATETIME2 DEFAULT GETDATE() NOT NULL,
    UpdatedAt DATETIME2 DEFAULT GETDATE() NOT NULL,
    CONSTRAINT UQ_RSVPs_UserEvent UNIQUE (UserID, EventID), -- Prevent duplicate RSVPs for same user/event
    CONSTRAINT FK_RSVPs_User FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE,
    CONSTRAINT FK_RSVPs_Event FOREIGN KEY (EventID) REFERENCES Events(EventID) ON DELETE CASCADE
);

-- Indexes for RSVPs
CREATE INDEX idx_rsvps_event_status ON RSVPs (EventID, Status);
CREATE INDEX idx_rsvps_user ON RSVPs (UserID);

-- UserActivity table
CREATE TABLE UserActivity (
    ActivityID INT IDENTITY(1,1) PRIMARY KEY,
    UserID INT NOT NULL,
    ActivityType NVARCHAR(50) NOT NULL CHECK (ActivityType IN ('created_event', 'rsvp_event', 'viewed_event_details', 'followed_user', 'joined_interest')),
    TargetID INT, -- Polymorphic reference (no FK constraint)
    Description NVARCHAR(MAX),
    CreatedAt DATETIME2 DEFAULT GETDATE() NOT NULL,
    CONSTRAINT FK_UserActivity_User FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
);

-- Indexes for UserActivity
CREATE INDEX idx_useractivity_user_created ON UserActivity (UserID, CreatedAt DESC);
CREATE INDEX idx_useractivity_target ON UserActivity (TargetID);