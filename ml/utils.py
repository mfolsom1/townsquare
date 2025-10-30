# utils.py: Helper utilities for the ml package
import typing as _typing
from dotenv import load_dotenv
import time
import numpy as np
import logging
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import os
import traceback
# When ML_TEST_MODE=1 we run in test mode (DB connections disabled, no pyodbc dependencies).
# For embeddings, `sentence-transformers` recommendations are preferred
# but fall back to a deterministic dummy model if it's not installed.
TEST_MODE = os.getenv("ML_TEST_MODE", "0") == "1"

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except Exception:
    SentenceTransformer = None
    HAS_SENTENCE_TRANSFORMERS = False

# TODO: split file

# Load environment variables
load_dotenv()

# Configuration
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
VECTOR_STORAGE_PATH = "ml/vector_store"
DEFAULT_TOP_K = 10


logger = logging.getLogger(__name__)

# Embedding device (cpu/cuda) can be selected via environment variable.
# Default to 'cpu' to avoid unexpected CUDA usage during tests.
EMBEDDING_DEVICE = os.getenv('ML_EMBEDDING_DEVICE', 'cpu')
_DUMMY_EMBEDDING_DIM = int(os.getenv('ML_DUMMY_EMBED_DIM', '384'))
_EMBEDDING_STRICT = os.getenv(
    'ML_EMBEDDING_STRICT', '0') in ('1', 'true', 'True')


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
        # In test mode we don't require pyodbc
        # If not in test and pyodbc isn't available, raise ImportError
        if TEST_MODE:
            raise RuntimeError(
                "Database connections are disabled in ML_TEST_MODE. Use MockDatabaseConnector for tests.")
        try:
            import pyodbc
        except Exception:
            raise ImportError(
                "pyodbc is required for DatabaseConnector in production mode. "
                "Install it or set ML_TEST_MODE=1 to run tests with the mock DB."
            )
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
        """Fetch user's top friends with optional activity data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                if include_activity:
                    # Query with friend activity data
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
                    # Fallback to simple query
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
                friends = [dict(zip(columns, row))
                           for row in cursor.fetchall()]

                logger.info(
                    f"Fetched {len(friends)} friends for user {user_uid}")
                return friends

        except Exception as e:
            logger.error(f"Error fetching friends for user {user_uid}: {e}")
            return []

    def fetch_friend_recommendations(self, user_uid: str, include_scoring: bool = True) -> List[Dict[str, Any]]:
        """Fetch events that friends are attending with scoring"""
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
                    # Fallback to simple query
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
        self._use_dummy = not HAS_SENTENCE_TRANSFORMERS

    def load_model(self):
        """Load the embedding model"""
        if self.model is None:
            # If sentence-transformers is available and we haven't opted into
            # using the dummy, attempt to load the model. If a previous load
            # failed and set _use_dummy, fall back to dummy immediately.
            if HAS_SENTENCE_TRANSFORMERS and not getattr(self, '_use_dummy', False):
                logger.info(
                    f"Loading embedding model: {self.model_name} (device={EMBEDDING_DEVICE})")
                try:
                    # SentenceTransformer accepts device in recent versions; if not, move after load
                    try:
                        self.model = SentenceTransformer(
                            self.model_name, device=EMBEDDING_DEVICE)
                    except TypeError:
                        # Older versions may not accept device kwarg
                        self.model = SentenceTransformer(self.model_name)
                        try:
                            # Move model to device if supported
                            if hasattr(self.model, 'to'):
                                self.model.to(EMBEDDING_DEVICE)
                        except Exception:
                            logger.debug(
                                "Could not move SentenceTransformer model to device; continuing on CPU")
                    logger.info(
                        "Loaded sentence-transformers model successfully")
                    # If available, set embedding dim from model
                    try:
                        self._dim = int(
                            self.model.get_sentence_embedding_dimension())
                    except Exception:
                        self._dim = _DUMMY_EMBEDDING_DIM
                except Exception as e:
                    # Log traceback so failures are actionable
                    tb = traceback.format_exc()
                    logger.error(
                        f"Failed to load sentence-transformers model: {e}\n{tb}")
                    # If strict mode is enabled, re-raise to fail-fast
                    if _EMBEDDING_STRICT:
                        raise
                    # Fall back to deterministic dummy model on any load error
                    self._use_dummy = True
                    # instantiate dummy model immediately so future calls succeed

                    class _DummyModel:
                        def __init__(self, dim=_DUMMY_EMBEDDING_DIM):
                            self._dim = dim

                        def get_sentence_embedding_dimension(self):
                            return self._dim

                        def encode(self, texts):
                            out = []
                            for t in texts:
                                h = abs(hash(t)) % (10 ** 8)
                                rng = np.random.RandomState(h)
                                out.append(
                                    rng.rand(self._dim).astype('float32'))
                            return np.stack(out)

                    self.model = _DummyModel(dim=_DUMMY_EMBEDDING_DIM)
                    self._dim = _DUMMY_EMBEDDING_DIM
            else:
                # Create a small dummy model with predictable behavior for tests
                # TODO: replace with a better method if needed
                class _DummyModel:
                    def __init__(self, dim=_DUMMY_EMBEDDING_DIM):
                        self._dim = dim

                    def get_sentence_embedding_dimension(self):
                        return self._dim

                    def encode(self, texts):
                        out = []
                        for t in texts:
                            # Pseudo-embeddings based on hash for deterministic behavior
                            h = abs(hash(t)) % (10 ** 8)
                            rng = np.random.RandomState(h)
                            out.append(rng.rand(self._dim).astype('float32'))
                        return np.stack(out)

                logger.warning(
                    "sentence-transformers not available or failed to load; using deterministic dummy embeddings for tests")
                self.model = _DummyModel(dim=_DUMMY_EMBEDDING_DIM)
                self._dim = _DUMMY_EMBEDDING_DIM

    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        self.load_model()
        if not text.strip():
            # Return zero vector for empty text
            return np.zeros(self.model.get_sentence_embedding_dimension(), dtype='float32')
        embedding = self.model.encode([text])[0]
        return np.array(embedding, dtype='float32')

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
        return np.array(embeddings, dtype='float32')


class VectorStore:
    """Manage storage and retrieval of vectors using numpy-backed files."""

    def __init__(self, storage_path: str = VECTOR_STORAGE_PATH):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)

    def save_vectors(self, vectors: np.ndarray, ids: List, vector_type: str):
        """Save vectors to FAISS index and metadata"""
        if len(vectors) == 0:
            logger.warning(f"No vectors to save for {vector_type}")
            return

        dimension = vectors.shape[1]

        # Normalize vectors for cosine similarity
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized = vectors / norms

        vec_path = self.storage_path / f"{vector_type}_vectors.npy"
        # Write numpy array to a temp file and atomically replace the final file
        try:
            tmp_vec = vec_path.with_suffix('.npy.tmp')
            # Use a binary file handle when saving so numpy does not auto-append
            # a second '.npy' suffix, guaranteeing the tmp file path is as expected
            with open(tmp_vec, 'wb') as vf:
                np.save(vf, normalized)
            # Try atomic replace of file (works across Windows and POSIX)
            os.replace(str(tmp_vec), str(vec_path))
        except Exception as e:
            logger.error(f"Error saving vectors to {vec_path}: {e}")
            # Attempt cleanup through unlink
            try:
                if tmp_vec.exists():
                    tmp_vec.unlink()
            except Exception:
                pass
            return

        metadata_path = self.storage_path / f"{vector_type}_metadata.json"
        metadata = {
            'ids': ids,
            'dimension': int(dimension),
            'count': len(ids),
            'created_at': time.time(),
            'source': 'training'
        }
        try:
            tmp_meta = metadata_path.with_suffix('.json.tmp')
            with open(tmp_meta, 'w', encoding='utf8') as f:
                json.dump(metadata, f)
            os.replace(str(tmp_meta), str(metadata_path))
        except Exception as e:
            logger.error(f"Error writing metadata to {metadata_path}: {e}")
            try:
                if tmp_meta.exists():
                    tmp_meta.unlink()
            except Exception:
                pass
            return

        # Write a small manifest with checksum for integrity checks
        try:
            import hashlib
            sha256 = hashlib.sha256()
            # Read the saved vectors file and compute sha256
            with open(vec_path, 'rb') as vf:
                for chunk in iter(lambda: vf.read(8192), b''):
                    sha256.update(chunk)
            manifest = {
                'count': len(ids),
                'dimension': int(dimension),
                'sha256': sha256.hexdigest(),
            }
            manifest_path = self.storage_path / f"{vector_type}_manifest.json"
            tmp_manifest = manifest_path.with_suffix('.json.tmp')
            with open(tmp_manifest, 'w', encoding='utf8') as mf:
                json.dump(manifest, mf)
            os.replace(str(tmp_manifest), str(manifest_path))
        except Exception as e:
            logger.warning(f"Could not write manifest for {vector_type}: {e}")

        logger.info(
            f"Saved {len(ids)} {vector_type} vectors to {vec_path} (origin: training)")

    def load_vectors(self, vector_type: str) -> Tuple[Any, List]:
        """Load vector numpy file and metadata; return in-memory wrapper and ids."""
        metadata_path = self.storage_path / f"{vector_type}_metadata.json"
        if not metadata_path.exists():
            logger.warning(
                f"No {vector_type} vectors found in {self.storage_path}")
            return None, []

        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            vec_path = self.storage_path / f"{vector_type}_vectors.npy"
            if not vec_path.exists():
                logger.warning(
                    f"Vectors file not found for {vector_type} (expected at {vec_path})")
                return None, metadata.get('ids', [])

            vectors = np.load(str(vec_path))

            # If a manifest exists, validate checksum and expected shape
            manifest_path = self.storage_path / f"{vector_type}_manifest.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path, 'r', encoding='utf8') as mf:
                        manifest = json.load(mf)
                    m_count = manifest.get('count')
                    m_dim = manifest.get('dimension')
                    m_sha = manifest.get('sha256')
                    # Validate count/dimension
                    if m_count is not None and m_count != vectors.shape[0]:
                        logger.error(
                            f"Manifest count mismatch for {vector_type}: manifest={m_count} vs array={vectors.shape[0]}")
                        return None, []
                    if m_dim is not None and m_dim != vectors.shape[1]:
                        logger.error(
                            f"Manifest dim mismatch for {vector_type}: manifest={m_dim} vs array={vectors.shape[1]}")
                        return None, []
                    # Validate sha256
                    import hashlib
                    sha256 = hashlib.sha256()
                    with open(vec_path, 'rb') as vf:
                        for chunk in iter(lambda: vf.read(8192), b''):
                            sha256.update(chunk)
                    if m_sha and m_sha != sha256.hexdigest():
                        logger.error(
                            f"Manifest sha256 mismatch for {vector_type}")
                        return None, []
                except Exception as e:
                    logger.warning(
                        f"Could not validate manifest for {vector_type}: {e}")

            # Ensure metadata shape matches loaded vectors
            ids = metadata.get('ids')
            dim = metadata.get('dimension')
            # ids should be a list
            if not isinstance(ids, list):
                logger.error(
                    f"Invalid metadata for {vector_type}: 'ids' is not a list")
                return None, []

            # Vectors should be 2D
            if vectors.ndim != 2:
                logger.error(
                    f"Loaded vectors for {vector_type} have invalid ndim={vectors.ndim}")
                return None, []

            if dim is not None:
                try:
                    dim = int(dim)
                    if vectors.shape[1] != dim:
                        logger.error(
                            f"Dimension mismatch for {vector_type}: metadata dimension={dim} != array dim={vectors.shape[1]}")
                        return None, []
                except Exception:
                    logger.error(
                        f"Invalid 'dimension' value in metadata for {vector_type}")
                    return None, []

            class _InMemoryIndex:
                def __init__(self, vectors):
                    self._vectors = vectors.astype('float32')
                    self.ntotal = self._vectors.shape[0]

                def reconstruct(self, idx):
                    return self._vectors[idx]

            logger.info(
                f"Loaded {metadata.get('count', len(vectors))} {vector_type} vectors from {vec_path} (origin: {metadata.get('source', 'unknown')})")
            return _InMemoryIndex(vectors), metadata.get('ids', [])
        except Exception as e:
            logger.error(f"Error loading {vector_type} vectors: {e}")
            return None, []

    def search_similar(self, query_vector: np.ndarray, index: Any,
                       top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """Search for similar vectors"""
        if index is None or index.ntotal == 0:
            return np.array([]), np.array([])

        if query_vector.size == 0:
            return np.array([]), np.array([])

        q = query_vector.astype('float32').reshape(1, -1)

        # Normalize query
        q = q / (np.linalg.norm(q, axis=1, keepdims=True) + 1e-12)

        # numpy-based cosine similarity search
        stored = index._vectors  # shape (N, D)
        sims = stored.dot(q.T).reshape(-1)
        order = np.argsort(-sims)[:top_k]
        return sims[order], order


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
