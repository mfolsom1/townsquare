from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Event(db.Model):
    __tablename__ = 'Events'

    EventID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Title = db.Column(db.String(200), nullable=False)
    Description = db.Column(db.Text)
    StartTime = db.Column(db.DateTime, nullable=False)
    EndTime = db.Column(db.DateTime, nullable=False)
    Location = db.Column(db.String(300), nullable=False)
    CreatedAt = db.Column(db.DateTime, default=datetime.now)
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
            "bio": self.bio
        }
    
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
    def update_user(firebase_uid, **kwargs):
        """Update user information"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            # Build dynamic update query
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
            
            if update_fields:
                update_fields.append("UpdatedAt = GETDATE()")
                query = f"UPDATE Users SET {', '.join(update_fields)} WHERE FirebaseUID = ?"
                values.append(firebase_uid)
                
                cursor.execute(query, values)
                conn.commit()
                return True
            return False
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
