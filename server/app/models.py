# models.py: Database operations for Azure SQL
import pyodbc
from .config import Config


class DatabaseConnection:
    @staticmethod
    def get_connection():
        config = Config()
        return pyodbc.connect(config.azure_sql_connection_string)


class User:
    def __init__(self, firebase_uid, username, email, first_name=None, last_name=None, location=None, bio=None, user_type='individual', organization_name=None, created_at=None, updated_at=None):
        self.firebase_uid = firebase_uid
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.location = location
        self.bio = bio
        self.user_type = user_type or 'individual'
        self.organization_name = organization_name
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self):
        """Convert user object to dictionary for JSON responses"""
        return {
            "firebase_uid": self.firebase_uid,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "location": self.location,
            "bio": self.bio,
            "user_type": self.user_type,
            "organization_name": self.organization_name,
            "interests": self.get_user_interests()
        }

    def get_user_interests(self):
        """Get user's interests as a list of interest names"""
        return User.get_user_interests_by_uid(self.firebase_uid)

    @staticmethod
    def create_user(firebase_uid, username, email, first_name=None, last_name=None, location="Unknown", user_type='individual', organization_name=None):
        """Create a new user in the database using existing schema"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO Users (FirebaseUID, Username, Email, FirstName, LastName, Location, UserType, OrganizationName)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (firebase_uid, username, email, first_name,
                 last_name, location, user_type, organization_name)
            )
            conn.commit()
            return User(firebase_uid, username, email, first_name, last_name, location, None, user_type, organization_name)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_user_by_firebase_uid(firebase_uid):
        """Get user by Firebase UID"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT FirebaseUID, Username, Email, FirstName, LastName, Location, Bio, UserType, OrganizationName, CreatedAt, UpdatedAt
                FROM Users WHERE FirebaseUID = ?
                """,
                (firebase_uid,)
            )
            row = cursor.fetchone()
            if row:
                return User(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10])
            return None
        finally:
            conn.close()

    @staticmethod
    def get_user_by_email(email):
        """Get user by email"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT FirebaseUID, Username, Email, FirstName, LastName, Location, Bio, UserType, OrganizationName, CreatedAt, UpdatedAt
                FROM Users WHERE Email = ?
                """,
                (email,)
            )
            row = cursor.fetchone()
            if row:
                return User(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10])
            return None
        finally:
            conn.close()

    @staticmethod
    def get_user_interests_by_uid(firebase_uid):
        """Get all interests for a user by Firebase UID"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT i.Name 
                FROM Interests i 
                INNER JOIN UserInterests ui ON i.InterestID = ui.InterestID 
                WHERE ui.UserUID = ?
                ORDER BY i.Name
                """,
                (firebase_uid,)
            )
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        finally:
            conn.close()

    @staticmethod
    def add_user_interest(firebase_uid, interest_name):
        """Add an interest to a user"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            # First, get or create the interest
            cursor.execute(
                "SELECT InterestID FROM Interests WHERE Name = ?", (interest_name,))
            row = cursor.fetchone()

            if row:
                interest_id = row[0]
            else:
                # Create new interest
                cursor.execute(
                    "INSERT INTO Interests (Name) OUTPUT INSERTED.InterestID VALUES (?)",
                    (interest_name,)
                )
                interest_id = cursor.fetchone()[0]

            # Add user-interest relationship (ignore if already exists)
            cursor.execute(
                """
                IF NOT EXISTS (SELECT 1 FROM UserInterests WHERE UserUID = ? AND InterestID = ?)
                    INSERT INTO UserInterests (UserUID, InterestID) VALUES (?, ?)
                """,
                (firebase_uid, interest_id, firebase_uid, interest_id)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def remove_user_interest(firebase_uid, interest_name):
        """Remove an interest from a user"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                DELETE ui FROM UserInterests ui
                INNER JOIN Interests i ON ui.InterestID = i.InterestID
                WHERE ui.UserUID = ? AND i.Name = ?
                """,
                (firebase_uid, interest_name)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def set_user_interests(firebase_uid, interest_names):
        """Set user interests (replaces all existing interests)"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            # Remove all existing interests for the user
            cursor.execute(
                "DELETE FROM UserInterests WHERE UserUID = ?", (firebase_uid,))

            # Add new interests
            for interest_name in interest_names:
                # Get or create interest
                cursor.execute(
                    "SELECT InterestID FROM Interests WHERE Name = ?", (interest_name,))
                row = cursor.fetchone()

                if row:
                    interest_id = row[0]
                else:
                    # Create new interest
                    cursor.execute(
                        "INSERT INTO Interests (Name) OUTPUT INSERTED.InterestID VALUES (?)",
                        (interest_name,)
                    )
                    interest_id = cursor.fetchone()[0]

                # Add user-interest relationship
                cursor.execute(
                    "INSERT INTO UserInterests (UserUID, InterestID) VALUES (?, ?)",
                    (firebase_uid, interest_id)
                )

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def update_user(firebase_uid, **kwargs):
        """Update user information"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            # Handle interests separately
            interests = kwargs.pop('interests', None)

            # Build dynamic update query for basic fields
            update_fields = []
            values = []

            # Map snake_case parameter names to database field names
            field_mapping = {
                'username': 'Username',
                'email': 'Email',
                'first_name': 'FirstName',
                'last_name': 'LastName',
                'location': 'Location',
                'bio': 'Bio',
                'user_type': 'UserType',
                'organization_name': 'OrganizationName'
            }

            for param_name, db_field in field_mapping.items():
                if param_name in kwargs:
                    update_fields.append(f"{db_field} = ?")
                    values.append(kwargs[param_name])

            # Update basic user fields if any
            updated_basic = False
            if update_fields:
                update_fields.append("UpdatedAt = GETDATE()")
                query = f"UPDATE Users SET {', '.join(update_fields)} WHERE FirebaseUID = ?"
                values.append(firebase_uid)

                cursor.execute(query, values)
                conn.commit()
                updated_basic = True

            # Handle interests update
            updated_interests = False
            if interests is not None:
                # Close current connection and use the static method
                conn.close()
                User.set_user_interests(firebase_uid, interests)
                updated_interests = True

            return updated_basic or updated_interests
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            raise e
        finally:
            try:
                conn.close()
            except Exception:
                pass

    @staticmethod
    def get_all_interests():
        """Get all available interests in the system"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT Name, Description FROM Interests ORDER BY Name"
            )
            rows = cursor.fetchall()
            return [{
                "name": row[0],
                "description": row[1] if row[1] else None
            } for row in rows]
        finally:
            conn.close()

    @staticmethod
    def follow_user(follower_uid, following_uid):
        """Follow another user"""
        if follower_uid == following_uid:
            raise ValueError("Cannot follow yourself")

        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            # Check if both users exist
            cursor.execute(
                "SELECT COUNT(*) FROM Users WHERE FirebaseUID IN (?, ?)", (follower_uid, following_uid))
            count = cursor.fetchone()[0]
            if count != 2:
                raise ValueError("One or both users do not exist")

            # Check if already following
            cursor.execute(
                "SELECT COUNT(*) FROM SocialConnections WHERE FollowerUID = ? AND FollowingUID = ?",
                (follower_uid, following_uid)
            )
            if cursor.fetchone()[0] > 0:
                return False  # Already following

            # Create follow relationship
            cursor.execute(
                "INSERT INTO SocialConnections (FollowerUID, FollowingUID) VALUES (?, ?)",
                (follower_uid, following_uid)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def unfollow_user(follower_uid, following_uid):
        """Unfollow a user"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM SocialConnections WHERE FollowerUID = ? AND FollowingUID = ?",
                (follower_uid, following_uid)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_following(firebase_uid):
        """Get list of users that this user is following"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT u.FirebaseUID, u.Username, u.FirstName, u.LastName, sc.CreatedAt
                FROM SocialConnections sc
                INNER JOIN Users u ON sc.FollowingUID = u.FirebaseUID
                WHERE sc.FollowerUID = ?
                ORDER BY sc.CreatedAt DESC
                """,
                (firebase_uid,)
            )
            rows = cursor.fetchall()
            return [{
                "firebase_uid": row[0],
                "username": row[1],
                "first_name": row[2],
                "last_name": row[3],
                "followed_at": row[4].isoformat() if hasattr(row[4], 'isoformat') else row[4] if row[4] else None
            } for row in rows]
        finally:
            conn.close()

    @staticmethod
    def get_followers(firebase_uid):
        """Get list of users that are following this user"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT u.FirebaseUID, u.Username, u.FirstName, u.LastName, sc.CreatedAt
                FROM SocialConnections sc
                INNER JOIN Users u ON sc.FollowerUID = u.FirebaseUID
                WHERE sc.FollowingUID = ?
                ORDER BY sc.CreatedAt DESC
                """,
                (firebase_uid,)
            )
            rows = cursor.fetchall()
            return [{
                "firebase_uid": row[0],
                "username": row[1],
                "first_name": row[2],
                "last_name": row[3],
                "followed_at": row[4].isoformat() if hasattr(row[4], 'isoformat') else row[4] if row[4] else None
            } for row in rows]
        finally:
            conn.close()

    @staticmethod
    def is_following(follower_uid, following_uid):
        """Check if one user is following another"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM SocialConnections WHERE FollowerUID = ? AND FollowingUID = ?",
                (follower_uid, following_uid)
            )
            return cursor.fetchone()[0] > 0
        finally:
            conn.close()

    @staticmethod
    def get_user_by_username(username):
        """Get user by username"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT FirebaseUID, Username, Email, FirstName, LastName, Location, Bio, CreatedAt, UpdatedAt FROM Users WHERE Username = ?",
                (username,)
            )
            row = cursor.fetchone()
            if row:
                return User(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
            return None
        finally:
            conn.close()


class Event:
    def __init__(self, event_id, organizer_uid, title, description, start_time, end_time, location, category_id, max_attendees=None, image_url=None, created_at=None, updated_at=None, is_archived=False, archived_at=None):
        self.event_id = event_id
        self.organizer_uid = organizer_uid
        self.title = title
        self.description = description
        self.start_time = start_time
        self.end_time = end_time
        self.location = location
        self.category_id = category_id
        self.max_attendees = max_attendees
        self.image_url = image_url
        self.created_at = created_at
        self.updated_at = updated_at
        self.is_archived = is_archived
        self.archived_at = archived_at

    def to_dict(self):
        # Helper function to safely convert datetime to ISO format
        def safe_isoformat(dt):
            if dt is None:
                return None
            if hasattr(dt, 'isoformat'):
                return dt.isoformat()
            return str(dt)  # If it's already a string, return as is

        return {
            "event_id": self.event_id,
            "organizer_uid": self.organizer_uid,
            "title": self.title,
            "description": self.description,
            "start_time": safe_isoformat(self.start_time),
            "end_time": safe_isoformat(self.end_time),
            "location": self.location,
            "category_id": self.category_id,
            "max_attendees": self.max_attendees,
            "image_url": self.image_url,
            "created_at": safe_isoformat(self.created_at),
            "updated_at": safe_isoformat(self.updated_at),
            "is_archived": self.is_archived,
            "archived_at": safe_isoformat(self.archived_at)
        }

    @staticmethod
    def create_event(organizer_uid, title, start_time, end_time, location, category_id=None, description=None, max_attendees=None, image_url=None):
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            # Use OUTPUT clause to get the inserted EventID
            cursor.execute(
                """
                INSERT INTO Events (OrganizerUID, Title, Description, StartTime, EndTime, Location, CategoryID, MaxAttendees, ImageURL)
                OUTPUT INSERTED.EventID
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (organizer_uid, title, description, start_time, end_time,
                 location, category_id, max_attendees, image_url)
            )
            event_id = cursor.fetchone()[0]
            conn.commit()

            return Event(event_id, organizer_uid, title, description, start_time, end_time, location, category_id, max_attendees, image_url)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_events(q=None, page: int = 1, per_page: int = 20, sort_by: str = "StartTime", sort_dir: str = "ASC", include_archived: bool = False):
        """
        Simplified search: only supports a free-text query `q` (matches Title/Description/Location)
        plus pagination and simple sorting. Returns dict { events: [Event,...], total: int }.
        By default, excludes archived events unless include_archived=True.
        """
        clauses = []
        params = []

        # Exclude archived events by default
        if not include_archived:
            clauses.append("IsArchived = 0")

        if q:
            like = f"%{q}%"
            clauses.append(
                "(Title LIKE ? OR Description LIKE ? OR Location LIKE ?)")
            params += [like, like, like]

        where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        # sanitize sort_by and sort_dir
        sort_dir = "DESC" if str(sort_dir).upper() == "DESC" else "ASC"
        allowed_sort_cols = {"StartTime", "EndTime", "CreatedAt", "Title"}
        sort_by = sort_by if sort_by in allowed_sort_cols else "StartTime"

        # pagination
        try:
            page = max(1, int(page))
        except Exception:
            page = 1
        try:
            per_page = max(1, int(per_page))
        except Exception:
            per_page = 20

        offset = (page - 1) * per_page

        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            # total count
            count_query = f"SELECT COUNT(*) FROM Events {where_sql}"
            cursor.execute(count_query, params)
            row = cursor.fetchone()
            total = int(row[0]) if row else 0

            # fetch paged rows
            query = f"""
                    SELECT *
                    FROM Events
                    {where_sql}
                    ORDER BY {sort_by} {sort_dir}
                    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
                """
            exec_params = params + [offset, per_page]
            cursor.execute(query, exec_params)
            rows = cursor.fetchall()

            events = [
                Event(
                    event_id=row[0],
                    organizer_uid=row[1],
                    title=row[2],
                    description=row[3],
                    start_time=row[4],
                    end_time=row[5],
                    location=row[6],
                    category_id=row[7],
                    max_attendees=row[8],
                    image_url=row[9],
                    created_at=row[10],
                    updated_at=row[11],
                    is_archived=bool(row[12]) if len(row) > 12 else False,
                    archived_at=row[13] if len(row) > 13 else None
                )
                for row in rows
            ]

            return {"events": events, "total": total}
        finally:
            conn.close()

    @staticmethod
    def get_all_events(include_archived=False):
        """Get all events. By default excludearchived events."""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            if include_archived:
                cursor.execute("SELECT * FROM Events")
            else:
                cursor.execute("SELECT * FROM Events WHERE IsArchived = 0")
            rows = cursor.fetchall()

            # Convert rows to Event objects
            events = [
                Event(
                    event_id=row[0],
                    organizer_uid=row[1],
                    title=row[2],
                    description=row[3],
                    start_time=row[4],
                    end_time=row[5],
                    location=row[6],
                    category_id=row[7],
                    max_attendees=row[8],
                    image_url=row[9],
                    created_at=row[10],
                    updated_at=row[11],
                    is_archived=bool(row[12]) if len(row) > 12 else False,
                    archived_at=row[13] if len(row) > 13 else None
                )
                for row in rows
            ]

            return events
        except Exception as e:
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_event_by_id(event_id, include_archived=False):
        """Get event by ID. By default exclude archived events."""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            if include_archived:
                cursor.execute(
                    "SELECT * FROM Events WHERE EventID = ?", (event_id,))
            else:
                cursor.execute(
                    "SELECT * FROM Events WHERE EventID = ? AND IsArchived = 0", (event_id,))
            row = cursor.fetchone()
            if row:
                return Event(
                    event_id=row[0],
                    organizer_uid=row[1],
                    title=row[2],
                    description=row[3],
                    start_time=row[4],
                    end_time=row[5],
                    location=row[6],
                    category_id=row[7],
                    max_attendees=row[8],
                    image_url=row[9],
                    created_at=row[10],
                    updated_at=row[11],
                    is_archived=bool(row[12]) if len(row) > 12 else False,
                    archived_at=row[13] if len(row) > 13 else None
                )
            return None
        except Exception as e:
            raise e
        finally:
            conn.close()

    @staticmethod
    def update_event(event_id, organizer_uid, **kwargs):
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            # Check the event exists and user owns it
            cursor.execute(
                "SELECT OrganizerUID FROM Events WHERE EventID = ?", (event_id,))
            row = cursor.fetchone()
            if not row or row[0] != organizer_uid:
                return None

            # Formats update fields
            fields = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(event_id)

            # Update query
            query = f"UPDATE Events SET {fields} WHERE EventID = ?"
            cursor.execute(query, values)
            conn.commit()

            # Return updated record
            cursor.execute(
                "SELECT * FROM Events WHERE EventID = ?", (event_id,))
            updated_row = cursor.fetchone()
            return Event(*updated_row) if updated_row else None
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def archive_event(event_id, organizer_uid):
        """Archive an event. Only the organizer can archive their events."""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            # Verify event exists and user is the organizer
            cursor.execute(
                "SELECT OrganizerUID, IsArchived FROM Events WHERE EventID = ?", (event_id,))
            row = cursor.fetchone()
            if not row:
                return None  # Event not found
            if row[0] != organizer_uid:
                return False  # Not authorized
            if row[1]:  # Already archived
                return None  # Already archived

            # Archive the event
            cursor.execute(
                """
                UPDATE Events 
                SET IsArchived = 1, ArchivedAt = GETDATE(), UpdatedAt = GETDATE() 
                WHERE EventID = ?
                """,
                (event_id,)
            )
            conn.commit()

            # Return the updated event
            return Event.get_event_by_id(event_id, include_archived=True)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def delete_event(event_id, organizer_uid):
        """
        Permanently delete an event. Only the organizer can delete their events.
        Note: Organization users should typically use archive_event instead.
        """
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT OrganizerUID FROM Events WHERE EventID = ?", (event_id,))
            row = cursor.fetchone()
            if not row or row[0] != organizer_uid:
                return False

            cursor.execute("DELETE FROM Events WHERE EventID = ?", (event_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_events_by_organizer(organizer_uid, include_archived=False):
        """Get all events organized by a specific user. By default, excludes archived events."""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            if include_archived:
                cursor.execute(
                    """
                    SELECT EventID, OrganizerUID, Title, Description, StartTime, EndTime, Location, 
                           CategoryID, MaxAttendees, ImageURL, CreatedAt, UpdatedAt, IsArchived, ArchivedAt
                    FROM Events 
                    WHERE OrganizerUID = ?
                    ORDER BY StartTime ASC
                    """,
                    (organizer_uid,)
                )
            else:
                cursor.execute(
                    """
                    SELECT EventID, OrganizerUID, Title, Description, StartTime, EndTime, Location, 
                           CategoryID, MaxAttendees, ImageURL, CreatedAt, UpdatedAt, IsArchived, ArchivedAt
                    FROM Events 
                    WHERE OrganizerUID = ? AND IsArchived = 0
                    ORDER BY StartTime ASC
                    """,
                    (organizer_uid,)
                )
            rows = cursor.fetchall()

            events = [
                Event(
                    event_id=row[0],
                    organizer_uid=row[1],
                    title=row[2],
                    description=row[3],
                    start_time=row[4],
                    end_time=row[5],
                    location=row[6],
                    category_id=row[7],
                    max_attendees=row[8],
                    image_url=row[9],
                    created_at=row[10],
                    updated_at=row[11],
                    is_archived=bool(row[12]) if len(row) > 12 else False,
                    archived_at=row[13] if len(row) > 13 else None
                )
                for row in rows
            ]

            return events
        except Exception as e:
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_events_by_attendee(user_uid, include_archived=False):
        """Get all events that a user is attending (has RSVP'd 'Going' to), excluding events they organized and archived events by default"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            archived_condition = "" if include_archived else "AND e.IsArchived = 0"
            cursor.execute(
                f"""
                SELECT e.EventID, e.OrganizerUID, e.Title, e.Description, e.StartTime, e.EndTime, e.Location, 
                       e.CategoryID, e.MaxAttendees, e.ImageURL, e.CreatedAt, e.UpdatedAt, e.IsArchived, e.ArchivedAt
                FROM Events e
                INNER JOIN RSVPs r ON e.EventID = r.EventID
                WHERE r.UserUID = ? AND r.Status = 'Going' AND e.OrganizerUID != ? {archived_condition}
                ORDER BY e.StartTime ASC
                """,
                (user_uid, user_uid)
            )
            rows = cursor.fetchall()

            events = [
                Event(
                    event_id=row[0],
                    organizer_uid=row[1],
                    title=row[2],
                    description=row[3],
                    start_time=row[4],
                    end_time=row[5],
                    location=row[6],
                    category_id=row[7],
                    max_attendees=row[8],
                    image_url=row[9],
                    created_at=row[10],
                    updated_at=row[11],
                    is_archived=bool(row[12]) if len(row) > 12 else False,
                    archived_at=row[13] if len(row) > 13 else None
                )
                for row in rows
            ]

            return events
        except Exception as e:
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_friend_events(firebase_uid, include_archived=False):
        """Events that friends the user is following are attending or interested in. Excludes archived events by default."""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            archived_condition = "" if include_archived else "AND e.IsArchived = 0"
            cursor.execute(
                f"""
                SELECT DISTINCT e.*
                FROM Events e
                JOIN RSVPs r ON e.EventID = r.EventID
                JOIN SocialConnections s ON s.FollowingUID = r.UserUID
                WHERE s.FollowerUID = ?
                  AND r.Status IN ('Going', 'Interested')
                  {archived_condition}
                """,
                (firebase_uid,)
            )
            rows = cursor.fetchall()
            if rows:
                return [
                    Event(
                        event_id=row[0],
                        organizer_uid=row[1],
                        title=row[2],
                        description=row[3],
                        start_time=row[4],
                        end_time=row[5],
                        location=row[6],
                        category_id=row[7],
                        max_attendees=row[8],
                        image_url=row[9],
                        created_at=row[10],
                        updated_at=row[11],
                        is_archived=bool(row[12]) if len(row) > 12 else False,
                        archived_at=row[13] if len(row) > 13 else None
                    )
                    for row in rows
                ]
            return []
        except Exception as e:
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_friend_created_events(firebase_uid, include_archived=False):
        """Events created by friends the user is following. Excludes archived events by default."""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            archived_condition = "AND e.IsArchived = 0" if not include_archived else ""
            cursor.execute(
                f"""
                SELECT e.*
                FROM Events e
                JOIN SocialConnections s ON s.FollowingUID = e.OrganizerUID
                WHERE s.FollowerUID = ?
                  {archived_condition}
                """,
                (firebase_uid,)
            )
            rows = cursor.fetchall()
            if rows:
                return [
                    Event(
                        event_id=row[0],
                        organizer_uid=row[1],
                        title=row[2],
                        description=row[3],
                        start_time=row[4],
                        end_time=row[5],
                        location=row[6],
                        category_id=row[7],
                        max_attendees=row[8],
                        image_url=row[9],
                        created_at=row[10],
                        updated_at=row[11],
                        is_archived=bool(row[12]) if len(row) > 12 else False,
                        archived_at=row[13] if len(row) > 13 else None
                    )
                    for row in rows
                ]
            return []
        except Exception as e:
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_friend_feed(firebase_uid):
        # Combine events friends are attending/interested in and events they created
        attending = Event.get_friend_events(firebase_uid)
        created = Event.get_friend_created_events(firebase_uid)
        combined = attending + [e for e in created if e not in attending]
        combined.sort(key=lambda e: e.start_time)
        return combined


class RSVP:
    def __init__(self, rsvp_id, user_uid, event_id, status, created_at=None, updated_at=None):
        self.rsvp_id = rsvp_id
        self.user_uid = user_uid
        self.event_id = event_id
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self):
        def safe_isoformat(dt):
            if dt is None:
                return None
            if hasattr(dt, 'isoformat'):
                return dt.isoformat()
            return str(dt)

        return {
            "rsvp_id": self.rsvp_id,
            "user_uid": self.user_uid,
            "event_id": self.event_id,
            "status": self.status,
            "created_at": safe_isoformat(self.created_at),
            "updated_at": safe_isoformat(self.updated_at)
        }

    @staticmethod
    def create_or_update_rsvp(user_uid, event_id, status):
        """Create or update an RSVP for an event"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            # Check if RSVP already exists
            cursor.execute(
                "SELECT RSVPID FROM RSVPs WHERE UserUID = ? AND EventID = ?",
                (user_uid, event_id)
            )
            existing_rsvp = cursor.fetchone()

            if existing_rsvp:
                # Update existing RSVP
                cursor.execute(
                    "UPDATE RSVPs SET Status = ?, UpdatedAt = GETDATE() WHERE RSVPID = ?",
                    (status, existing_rsvp[0])
                )
                rsvp_id = existing_rsvp[0]
            else:
                # Create new RSVP
                cursor.execute(
                    """
                    INSERT INTO RSVPs (UserUID, EventID, Status)
                    OUTPUT INSERTED.RSVPID
                    VALUES (?, ?, ?)
                    """,
                    (user_uid, event_id, status)
                )
                rsvp_id = cursor.fetchone()[0]

            conn.commit()
            return RSVP(rsvp_id, user_uid, event_id, status)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_user_rsvps(user_uid):
        """Get all RSVPs for a user"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT RSVPID, UserUID, EventID, Status, CreatedAt, UpdatedAt
                FROM RSVPs 
                WHERE UserUID = ?
                ORDER BY CreatedAt DESC
                """,
                (user_uid,)
            )
            rows = cursor.fetchall()

            rsvps = [
                RSVP(
                    rsvp_id=row[0],
                    user_uid=row[1],
                    event_id=row[2],
                    status=row[3],
                    created_at=row[4],
                    updated_at=row[5]
                )
                for row in rows
            ]

            return rsvps
        except Exception as e:
            raise e
        finally:
            conn.close()

    @staticmethod
    def delete_rsvp(user_uid, event_id):
        """Delete an RSVP"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM RSVPs WHERE UserUID = ? AND EventID = ?",
                (user_uid, event_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
