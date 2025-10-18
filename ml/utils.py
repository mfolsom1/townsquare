# utils.py: Helper functions for ML
import numpy as np
import pyodbc
import logging
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss
import time
import os
from dotenv import load_dotenv

# TODO: split file

# Load environment variables
load_dotenv()

# Configuration
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
VECTOR_STORAGE_PATH = "vector_store"
DEFAULT_TOP_K = 10

# Configure dev logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ml_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TextPreprocessor:
    """Preprocesses text for embeddings"""

    def __init__(self):
        self.stop_words = set(['a',
                               'an',
                               'the',
                               'and',
                               'or',
                               'but',
                               'in',
                               'on',
                               'at',
                               'to',
                               'for',
                               'of',
                               'with',
                               'by'])

    def clean_text(self, text: str) -> str:
        """Basic text cleaning"""
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^a-zA-Z0-9\s.,!?]', '', text)

        # Remove extra whitespace
        text = ' '.join(text.split())

        return text

    def preprocess_event_text(self, event_data: Dict[str, Any]) -> str:
        """Combine and preprocess event title, description, category, and tags"""
        title = event_data.get('Title', '')
        description = event_data.get('Description', '')
        category = event_data.get('CategoryName', '')
        tags = event_data.get('Tags', [])

        # Handle tags whether they're string or list
        if isinstance(tags, list):
            tags_text = ' '.join(tags)
        else:
            tags_text = str(tags)

        # Combine all text
        combined_text = f"{title} {description} {category} {tags_text}"

        # Clean the text
        cleaned_text = self.clean_text(combined_text)

        return cleaned_text

    def preprocess_user_interests(self, interests: List[str]) -> str:
        """Preprocess user interests text"""
        if not interests:
            return ""

        interests_text = ' '.join(interests)
        return self.clean_text(interests_text)

    def preprocess_user_profile(self, user_data: Dict[str, Any]) -> str:
        """Create comprehensive user profile text for similarity analysis"""
        interests = user_data.get('Interests', [])
        bio = user_data.get('Bio', '')
        location = user_data.get('Location', '')

        interests_text = self.preprocess_user_interests(interests)
        bio_cleaned = self.clean_text(bio)
        location_cleaned = self.clean_text(location)

        # Weight interests more heavily than bio for similarity
        profile_text = f"{interests_text} {interests_text} {bio_cleaned} {location_cleaned}"

        return profile_text


class DataValidator:
    """Data validation for full pipeline run"""

    def __init__(self):
        self.required_event_fields = ['EventID', 'Title', 'StartTime']

    def validate_events(
            self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate event data for training"""
        valid_events = []

        for event in events:
            if self._is_valid_event(event):
                valid_events.append(event)

        return valid_events

    def _is_valid_event(self, event: Dict[str, Any]) -> bool:
        """Check if event has required fields and valid data"""
        for field in self.required_event_fields:
            if field not in event or not event[field]:
                return False

        # Validate text content
        title = event.get('Title', '')
        if len(title.strip()) < 3:
            return False

        return True


class DatabaseConnector:
    """Handles model azure db connections and queries"""

    def __init__(self):
        self.connection_string = self._get_connection_string()

    def _get_connection_string(self) -> str:
        """Build connection string from environment variables"""
        server = os.getenv("DB_SERVER")
        database = os.getenv("DB_DATABASE")
        username = os.getenv("DB_USERNAME")
        password = os.getenv("DB_PASSWORD")

        if not all([server, database, username, password]):
            raise ValueError("Missing required database environment variables")

        return (
            f'DRIVER={{ODBC Driver 18 for SQL Server}};'
            f'SERVER={server};DATABASE={database};'
            f'UID={username};PWD={password};'
            'Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
        )

    def get_connection(self):
        return pyodbc.connect(self.connection_string)

    def fetch_events(
            self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch events with their categories and tags"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                query = """
                SELECT
                    e.EventID,
                    e.Title,
                    e.Description,
                    e.StartTime,
                    e.EndTime,
                    e.Location,
                    c.Name as CategoryName,
                    STRING_AGG(t.Name, ', ') as Tags
                FROM Events e
                LEFT JOIN EventCategories c ON e.CategoryID = c.CategoryID
                LEFT JOIN EventTagAssignments eta ON e.EventID = eta.EventID
                LEFT JOIN EventTags t ON eta.TagID = t.TagID
                WHERE e.StartTime > GETDATE()  -- Only future events
                GROUP BY e.EventID, e.Title, e.Description, e.StartTime, e.EndTime, e.Location, c.Name
                ORDER BY e.StartTime
                """
                if limit:
                    query += f" OFFSET 0 ROWS FETCH NEXT {limit} ROWS ONLY"

                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                events = []

                for row in cursor.fetchall():
                    # Convert tags string to clist
                    event = dict(zip(columns, row))
                    if event.get('Tags'):
                        event['Tags'] = [tag.strip()
                                         for tag in event['Tags'].split(',')]
                    else:
                        event['Tags'] = []
                    events.append(event)

                logger.info(f"Fetched {len(events)} events from database")
                return events

        except Exception as e:
            logger.error(f"Error fetching events: {e}")
            return []

    def fetch_user(self, user_uid: str) -> Optional[Dict[str, Any]]:
        """Fetch user data by FirebaseUID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                query = """
                SELECT
                    u.FirebaseUID,
                    u.Username,
                    u.Email,
                    u.FirstName,
                    u.LastName,
                    u.Location,
                    u.Bio,
                    STRING_AGG(i.Name, ', ') as Interests
                FROM Users u
                LEFT JOIN UserInterests ui ON u.FirebaseUID = ui.UserUID
                LEFT JOIN Interests i ON ui.InterestID = i.InterestID
                WHERE u.FirebaseUID = ?
                GROUP BY u.FirebaseUID, u.Username, u.Email, u.FirstName, u.LastName, u.Location, u.Bio
                """
                cursor.execute(query, (user_uid,))
                columns = [column[0] for column in cursor.description]
                row = cursor.fetchone()

                if row:
                    # Convert interests string to list
                    user = dict(zip(columns, row))
                    if user.get('Interests'):
                        user['Interests'] = [interest.strip()
                                             for interest in user['Interests'].split(',')]
                    else:
                        user['Interests'] = []
                    return user
                return None

        except Exception as e:
            logger.error(f"Error fetching user {user_uid}: {e}")
            return None

    def fetch_users_for_training(
            self, limit: int = 500) -> List[Dict[str, Any]]:
        """Fetch user data for similarity analysis"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                query = """
                    SELECT
                        u.FirebaseUID,
                        u.Username,
                        u.Location,
                        u.Bio,
                        STRING_AGG(i.Name, ', ') AS Interests
                    FROM Users u
                    LEFT JOIN UserInterests ui ON u.FirebaseUID = ui.UserUID
                    LEFT JOIN Interests i ON ui.InterestID = i.InterestID
                    WHERE u.FirebaseUID IN (
                        SELECT DISTINCT UserUID FROM RSVPs
                        WHERE Status IN ('Going', 'Interested')
                        UNION
                        SELECT DISTINCT UserUID FROM UserInterests
                    )
                    GROUP BY u.FirebaseUID, u.Username, u.Location, u.Bio
                """

                if limit:
                    query += f" ORDER BY NEWID() OFFSET 0 ROWS FETCH NEXT {limit} ROWS ONLY"

                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                users = []

                for row in cursor.fetchall():
                    user = dict(zip(columns, row))
                    if user.get('Interests'):
                        user['Interests'] = [interest.strip()
                                             for interest in user['Interests'].split(',')]
                    else:
                        user['Interests'] = []
                    users.append(user)

                return users

        except Exception as e:
            logger.error(f"Error fetching users for training: {e}")
            return []

    def fetch_user_rsvps(self, user_uid: str) -> List[Dict[str, Any]]:
        """Fetch user RSVPs with event details"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                query = """
                SELECT
                    r.RSVPID,
                    r.Status,
                    r.CreatedAt,
                    e.EventID,
                    e.Title,
                    e.Description,
                    e.StartTime,
                    e.Location,
                    c.Name as CategoryName
                FROM RSVPs r
                JOIN Events e ON r.EventID = e.EventID
                LEFT JOIN EventCategories c ON e.CategoryID = c.CategoryID
                WHERE r.UserUID = ? AND r.Status IN ('Going', 'Interested')
                ORDER BY r.CreatedAt DESC
                """
                cursor.execute(query, (user_uid,))
                columns = [column[0] for column in cursor.description]
                rsvps = [dict(zip(columns, row)) for row in cursor.fetchall()]

                logger.info(f"Fetched {len(rsvps)} RSVPs for user {user_uid}")
                return rsvps

        except Exception as e:
            logger.error(f"Error fetching RSVPs for user {user_uid}: {e}")
            return []

    def fetch_user_activity(self, user_uid: str,
                            activity_type: str = None) -> List[Dict[str, Any]]:
        """Fetch user activity for recommendation weighting"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                query = """
                SELECT
                    ActivityID,
                    ActivityType,
                    TargetID,
                    Description,
                    CreatedAt
                FROM UserActivity
                WHERE UserUID = ?
                """

                params = [user_uid]
                if activity_type:
                    query += " AND ActivityType = ?"
                    params.append(activity_type)

                query += " ORDER BY CreatedAt DESC"
                cursor.execute(query, params)
                columns = [column[0] for column in cursor.description]
                activities = [dict(zip(columns, row))
                              for row in cursor.fetchall()]

                return activities

        except Exception as e:
            logger.error(f"Error fetching activity for user {user_uid}: {e}")
            return []

    # TODO: unused, may be useful for some other feature
    def fetch_user_friends(self, user_uid: str,
                           limit: int = 3) -> List[Dict[str, Any]]:
        """Fetch user's top friends by most recent follow"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT TOP (?)
                        u.FirebaseUID,
                        u.Username,
                        u.FirstName,
                        u.LastName
                    FROM SocialConnections sc
                    JOIN Users u ON sc.FollowingUID = u.FirebaseUID
                    WHERE sc.FollowerUID = ?
                    ORDER BY sc.CreatedAt DESC
                """
                cursor.execute(query, (limit, user_uid))
                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching friends for user {user_uid}: {e}")
            return []

    def fetch_friend_recommendations(self, user_uid: str) -> List[Dict[str, Any]]:
        """Fetch events that friends are attending"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT DISTINCT
                        e.EventID,
                        e.Title,
                        e.Description,
                        e.StartTime,
                        e.Location,
                        c.Name AS CategoryName,
                        u.Username AS FriendUsername,
                        r.Status AS FriendStatus
                    FROM RSVPs r
                    JOIN SocialConnections sc ON r.UserUID = sc.FollowingUID
                    JOIN Users u ON r.UserUID = u.FirebaseUID
                    JOIN Events e ON r.EventID = e.EventID
                    LEFT JOIN EventCategories c ON e.CategoryID = c.CategoryID
                    WHERE sc.FollowerUID = ?
                      AND r.Status IN ('Going', 'Interested')
                      AND e.StartTime > GETDATE()
                      AND NOT EXISTS (
                          SELECT 1
                          FROM RSVPs r2
                          WHERE r2.UserUID = ?
                            AND r2.EventID = r.EventID
                      )
                    ORDER BY r.CreatedAt DESC
                """
                cursor.execute(query, (user_uid, user_uid))
                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(
                f"Error fetching friend recommendations for user {user_uid}: {e}")
            return []

    def store_friend_recommendations(
            self, user_uid: str, friend_events: List[Dict[str, Any]]):
        """Store top (max 3) friend recommendations for quick access"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Clear existing friend recs
                cursor.execute(
                    "DELETE FROM UserFriendRecommendations WHERE UserUID = ?", (user_uid,))

                # Insert new ones
                for event in friend_events[:3]:  # Store top 3
                    cursor.execute("""
                    INSERT INTO UserFriendRecommendations
                    (UserUID, EventID, FriendUsername, FriendStatus, CreatedAt)
                    VALUES (?, ?, ?, ?, GETDATE())
                    """, (user_uid, event['EventID'], event['FriendUsername'], event['FriendStatus']))

                conn.commit()
                logger.info(
                    f"Stored {len(friend_events[:3])} friend recommendations for user {user_uid}")

        except Exception as e:
            logger.error(f"Error storing friend recommendations: {e}")


def fetch_user_friends(self, user_uid: str, limit: int = 3, include_activity: bool = False) -> List[Dict[str, Any]]:
    """Enhanced version: Fetch user's top friends with optional activity data"""
    try:
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if include_activity:
                # Enhanced query with friend activity data
                query = """
                    SELECT TOP (?)
                        u.FirebaseUID,
                        u.Username,
                        u.FirstName,
                        u.LastName,
                        sc.CreatedAt as FollowedAt,
                        (
                            SELECT COUNT(*)
                            FROM RSVPs r
                            WHERE r.UserUID = u.FirebaseUID 
                            AND r.Status IN ('Going', 'Interested')
                            AND r.EventID IN (
                                SELECT EventID FROM Events WHERE StartTime > GETDATE()
                            )
                        ) as UpcomingEvents
                    FROM SocialConnections sc
                    JOIN Users u ON sc.FollowingUID = u.FirebaseUID
                    WHERE sc.FollowerUID = ?
                    ORDER BY sc.CreatedAt DESC
                """
            else:
                # Original simple query
                query = """
                    SELECT TOP (?)
                        u.FirebaseUID,
                        u.Username,
                        u.FirstName,
                        u.LastName
                    FROM SocialConnections sc
                    JOIN Users u ON sc.FollowingUID = u.FirebaseUID
                    WHERE sc.FollowerUID = ?
                    ORDER BY sc.CreatedAt DESC
                """

            cursor.execute(query, (limit, user_uid))
            columns = [column[0] for column in cursor.description]
            friends = [dict(zip(columns, row)) for row in cursor.fetchall()]

            logger.info(f"Fetched {len(friends)} friends for user {user_uid}")
            return friends

    except Exception as e:
        logger.error(f"Error fetching friends for user {user_uid}: {e}")
        return []


def fetch_friend_recommendations(self, user_uid: str, include_scoring: bool = True) -> List[Dict[str, Any]]:
    """Enhanced version: Fetch events that friends are attending with improved scoring"""
    try:
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if include_scoring:
                # Query with friend-based scoring
                query = """
                    SELECT DISTINCT
                        e.EventID,
                        e.Title,
                        e.Description,
                        e.StartTime,
                        e.Location,
                        c.Name AS CategoryName,
                        u.Username AS FriendUsername,
                        r.Status AS FriendStatus,
                        -- Calculate friend influence score
                        CASE 
                            WHEN r.Status = 'Going' THEN 2.0
                            WHEN r.Status = 'Interested' THEN 1.0
                            ELSE 0.0
                        END as BaseScore,
                        COUNT(r.UserUID) OVER (PARTITION BY e.EventID) as FriendCount
                    FROM RSVPs r
                    JOIN SocialConnections sc ON r.UserUID = sc.FollowingUID
                    JOIN Users u ON r.UserUID = u.FirebaseUID
                    JOIN Events e ON r.EventID = e.EventID
                    LEFT JOIN EventCategories c ON e.CategoryID = c.CategoryID
                    WHERE sc.FollowerUID = ?
                      AND r.Status IN ('Going', 'Interested')
                      AND e.StartTime > GETDATE()
                      AND NOT EXISTS (
                          SELECT 1
                          FROM RSVPs r2
                          WHERE r2.UserUID = ?
                            AND r2.EventID = r.EventID
                      )
                    ORDER BY FriendCount DESC, BaseScore DESC, e.StartTime ASC
                """
            else:
                # Original simple query
                query = """
                    SELECT DISTINCT
                        e.EventID,
                        e.Title,
                        e.Description,
                        e.StartTime,
                        e.Location,
                        c.Name AS CategoryName,
                        u.Username AS FriendUsername,
                        r.Status AS FriendStatus
                    FROM RSVPs r
                    JOIN SocialConnections sc ON r.UserUID = sc.FollowingUID
                    JOIN Users u ON r.UserUID = u.FirebaseUID
                    JOIN Events e ON r.EventID = e.EventID
                    LEFT JOIN EventCategories c ON e.CategoryID = c.CategoryID
                    WHERE sc.FollowerUID = ?
                      AND r.Status IN ('Going', 'Interested')
                      AND e.StartTime > GETDATE()
                      AND NOT EXISTS (
                          SELECT 1
                          FROM RSVPs r2
                          WHERE r2.UserUID = ?
                            AND r2.EventID = r.EventID
                      )
                    ORDER BY r.CreatedAt DESC
                """

            cursor.execute(query, (user_uid, user_uid))
            columns = [column[0] for column in cursor.description]
            recommendations = [dict(zip(columns, row))
                               for row in cursor.fetchall()]

            logger.info(
                f"Fetched {len(recommendations)} friend recommendations for user {user_uid}")
            return recommendations

    except Exception as e:
        logger.error(
            f"Error fetching friend recommendations for user {user_uid}: {e}")
        return []


class EmbeddingGenerator:
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self.model = None

    def load_model(self):
        """Load the embedding model"""
        if self.model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Model loaded successfully")

    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        self.load_model()
        if not text.strip():
            # Return zero vector for empty text
            return np.zeros(self.model.get_sentence_embedding_dimension())

        embedding = self.model.encode([text])[0]
        return embedding

    def generate_embeddings_batch(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts"""
        self.load_model()
        if not texts:
            return np.array([])

        # Filter out empty texts
        valid_texts = [text for text in texts if text.strip()]
        if not valid_texts:
            return np.zeros((0, self.model.get_sentence_embedding_dimension()))

        embeddings = self.model.encode(valid_texts)
        return embeddings


class VectorStore:
    """Manages storage and retrieval of vectors using FAISS for cosine similarity calc"""

    def __init__(self, storage_path: str = VECTOR_STORAGE_PATH):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)

    def save_vectors(self, vectors: np.ndarray, ids: List, vector_type: str):
        """Save vectors to FAISS index and metadata"""
        if len(vectors) == 0:
            logger.warning(f"No vectors to save for {vector_type}")
            return

        # Create FAISS index
        dimension = vectors.shape[1]
        # Inner product, cosine similarity
        index = faiss.IndexFlatIP(dimension)

        # Normalize vectors for cosine similarity
        faiss.normalize_L2(vectors)
        index.add(vectors)

        # Save index and metadata
        index_path = self.storage_path / f"{vector_type}_index.faiss"
        metadata_path = self.storage_path / f"{vector_type}_metadata.json"

        faiss.write_index(index, str(index_path))

        metadata = {
            'ids': ids,
            'dimension': dimension,
            'count': len(ids),
            'created_at': time.time()
        }
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)

        logger.info(f"Saved {len(ids)} {vector_type} vectors to {index_path}")

    def load_vectors(self, vector_type: str) -> Tuple[faiss.Index, List]:
        """Load FAISS index and metadata"""
        index_path = self.storage_path / f"{vector_type}_index.faiss"
        metadata_path = self.storage_path / f"{vector_type}_metadata.json"

        if not index_path.exists() or not metadata_path.exists():
            logger.warning(f"No {vector_type} vectors found at {index_path}")
            return None, []

        try:
            index = faiss.read_index(str(index_path))
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            logger.info(f"Loaded {metadata['count']} {vector_type} vectors")
            return index, metadata['ids']
        except Exception as e:
            logger.error(f"Error loading {vector_type} vectors: {e}")
            return None, []

    def search_similar(self, query_vector: np.ndarray, index: faiss.Index,
                       top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """Search for similar vectors"""
        if index is None or index.ntotal == 0:
            return np.array([]), np.array([])

        # Normalize query vector
        query_vector = query_vector.astype('float32').reshape(1, -1)
        faiss.normalize_L2(query_vector)

        # Search for similar vectors
        similarities, indices = index.search(query_vector, top_k)

        return similarities[0], indices[0]


def get_interaction_weight(interaction_type: str) -> float:
    """Get weight for different interaction types"""
    weights = {
        'Going': 3.0,  # RSVP Going
        'Interested': 1.5,  # RSVP Interested (2.0 total)
        'created_event': 2.5,  # User created the event
        'viewed_event_details': 1.0,  # Clicked event
        'followed_user': 0.8,  # Followed event host
        'joined_interest': 0.5,
        'friend_attending': 2.0,
        'friend_interested': 1.0,
    }
    return weights.get(interaction_type, 1.0)
