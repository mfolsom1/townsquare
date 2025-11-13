-- Migration: Add Organization Support
-- This migration adds organization functionality to the TownSquare database

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

-- Add OrgID column to Events table
ALTER TABLE Events ADD OrgID INT NULL;

-- Add foreign key constraint for Events -> Organizations
ALTER TABLE Events ADD CONSTRAINT FK_Events_Organization FOREIGN KEY (OrgID) REFERENCES Organizations(OrgID);

-- Add index for organization events
CREATE INDEX idx_events_organization ON Events (OrgID);