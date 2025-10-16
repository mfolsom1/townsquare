# models.py: Database operations for Azure SQL
import pyodbc
from .config import Config

class DatabaseConnection:
    @staticmethod
    def get_connection():
        config = Config()
        return pyodbc.connect(config.azure_sql_connection_string)

class User:
    def __init__(self, firebase_uid, username, email, first_name=None, last_name=None, location=None, bio=None, created_at=None, updated_at=None):
        self.firebase_uid = firebase_uid
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.location = location
        self.bio = bio
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
            "interests": self.get_user_interests()
        }
    
    def get_user_interests(self):
        """Get user's interests as a list of interest names"""
        return User.get_user_interests_by_uid(self.firebase_uid)
    
    @staticmethod
    def create_user(firebase_uid, username, email, first_name=None, last_name=None, location="Unknown"):
        """Create a new user in the database using existing schema"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO Users (FirebaseUID, Username, Email, FirstName, LastName, Location) VALUES (?, ?, ?, ?, ?, ?)",
                (firebase_uid, username, email, first_name, last_name, location)
            )
            conn.commit()
            return User(firebase_uid, username, email, first_name, last_name, location)
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
                "SELECT FirebaseUID, Username, Email, FirstName, LastName, Location, Bio, CreatedAt, UpdatedAt FROM Users WHERE FirebaseUID = ?",
                (firebase_uid,)
            )
            row = cursor.fetchone()
            if row:
                return User(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
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
                "SELECT FirebaseUID, Username, Email, FirstName, LastName, Location, Bio, CreatedAt, UpdatedAt FROM Users WHERE Email = ?",
                (email,)
            )
            row = cursor.fetchone()
            if row:
                return User(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
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
            cursor.execute("SELECT InterestID FROM Interests WHERE Name = ?", (interest_name,))
            row = cursor.fetchone()
            
            if row:
                interest_id = row[0]
            else:
                # Create new interest
                cursor.execute(
                    "INSERT INTO Interests (Name) VALUES (?)",
                    (interest_name,)
                )
                interest_id = cursor.lastrowid
            
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
            cursor.execute("DELETE FROM UserInterests WHERE UserUID = ?", (firebase_uid,))
            
            # Add new interests
            for interest_name in interest_names:
                # Get or create interest
                cursor.execute("SELECT InterestID FROM Interests WHERE Name = ?", (interest_name,))
                row = cursor.fetchone()
                
                if row:
                    interest_id = row[0]
                else:
                    # Create new interest
                    cursor.execute(
                        "INSERT INTO Interests (Name) VALUES (?)",
                        (interest_name,)
                    )
                    interest_id = cursor.lastrowid
                
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
                'bio': 'Bio'
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

class Event:
    def __init__ (self, event_id, organizer_uid, title, description, start_time, end_time, location, category_id, max_attendees=None, image_url=None, created_at=None, updated_at=None):
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
    
    def to_dict(self):
        return {
            "event_id": self.event_id,
            "organizer_uid": self.organizer_uid,
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "location": self.location,
            "category_id": self.category_id,
            "max_attendees": self.max_attendees,
            "image_url": self.image_url,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @staticmethod
    def create_event(organizer_uid, title, start_time, end_time, location, category_id=None, description=None, max_attendees=None, image_url=None):
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO Events (OrganizerUID, Title, Description, StartTime, EndTime, Location, CategoryID, MaxAttendees, ImageURL)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (organizer_uid, title, description, start_time, end_time, location, category_id, max_attendees, image_url)
            )
            conn.commit()
            event_id = cursor.lastrowid

            return Event(event_id, organizer_uid, title, description, start_time, end_time, location, category_id, max_attendees, image_url)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def get_all_events():
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM Events")
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
                    updated_at=row[11]
                )
                for row in rows
            ]

            return events
        except Exception as e:
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def get_event_by_id(event_id):
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM Events WHERE EventID = ?", (event_id,))
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
                    updated_at=row[11]
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
            cursor.execute("SELECT OrganizerUID FROM Events WHERE EventID = ?", (event_id,))
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
            cursor.execute("SELECT * FROM Events WHERE EventID = ?", (event_id,))
            updated_row = cursor.fetchone()
            return Event(*updated_row) if updated_row else None
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def delete_event(event_id, organizer_uid):
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT OrganizerUID FROM Events WHERE EventID = ?", (event_id,))
            row = cursor.fetchone()
            if not row or row[0] != organizer_uid:
                return False
            
            cursor.execute("DELETE FROM Events WHERE EventID = ?", (event_id))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
            
    @staticmethod
    def get_friend_events(firebase_uid):
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT DISTINCT e.*
                FROM Events e
                JOIN RSVPs r ON e.EventID = r.EventID
                JOIN SocialConnections s ON s.FollowingUID = r.UserUID
                WHERE s.FollowerUID = ?
                  AND r.Status IN ('Going', 'Interested')
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
                    )
                    for row in rows
                ]
            return []
        except Exception as e:
            raise e
        finally:
            conn.close()

