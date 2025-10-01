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

# TODO: Docstrings

# Preprocesses text for embeddings
class TextPreprocessor:
    def __init__(self):
        self.stop_words = set(['a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
    
    def clean_text(self, text: str) -> str:
        # Basic text cleaning
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
        # Combine and preprocess event title, description, category, and tags
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
        # Preprocess user interests text
        if not interests:
            return ""
        
        interests_text = ' '.join(interests)
        return self.clean_text(interests_text)
    # TODO: Anything else?

# Validates data against logic, might be unnecessary
#class DataValidator: 

# Handles model azure db connections and queries
class DatabaseConnector:
    def __init__(self):
        self.connection_string = self._get_connection_string()
    
    def _get_connection_string(self) -> str:
        # Build connection string from environment variables
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
    
    def fetch_events(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        # Fetch events with their categories and tags
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
                        event['Tags'] = [tag.strip() for tag in event['Tags'].split(',')]
                    else:
                        event['Tags'] = []
                    events.append(event)
                
                logger.info(f"Fetched {len(events)} events from database")
                return events
                
        except Exception as e:
            logger.error(f"Error fetching events: {e}")
            return []
    
    def fetch_user(self, user_uid: str) -> Optional[Dict[str, Any]]:
        # Fetch user data by FirebaseUID
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
                        user['Interests'] = [interest.strip() for interest in user['Interests'].split(',')]
                    else:
                        user['Interests'] = []
                    return user
                return None
                
        except Exception as e:
            logger.error(f"Error fetching user {user_uid}: {e}")
            return None
    
    def fetch_user_rsvps(self, user_uid: str) -> List[Dict[str, Any]]:
        # Fetch user RSVPs with event details
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
    
    def fetch_user_activity(self, user_uid: str, activity_type: str = None) -> List[Dict[str, Any]]:
        # Fetch user activity for recommendation weighting
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
                activities = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                return activities
                
        except Exception as e:
            logger.error(f"Error fetching activity for user {user_uid}: {e}")
            return []
        
# Handles text embedding generation (sentence transformers, TODO better option?)
class EmbeddingGenerator:
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self.model = None
    
    def load_model(self):
        # Load the embedding model
        if self.model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Model loaded successfully")
    
    def generate_embedding(self, text: str) -> np.ndarray:
        # Generate embedding for a single text
        self.load_model()
        if not text.strip():
            # Return zero vector for empty text
            return np.zeros(self.model.get_sentence_embedding_dimension())
        
        embedding = self.model.encode([text])[0]
        return embedding
    
    def generate_embeddings_batch(self, texts: List[str]) -> np.ndarray:
        # Generate embeddings for multiple texts
        self.load_model()
        if not texts:
            return np.array([])
        
        # Filter out empty texts
        valid_texts = [text for text in texts if text.strip()]
        if not valid_texts:
            return np.zeros((0, self.model.get_sentence_embedding_dimension()))
        
        embeddings = self.model.encode(valid_texts)
        return embeddings
    
# Manages storage and retrieval of vectors using FAISS for cosine similarity calc
class VectorStore:
    def __init__(self, storage_path: str = VECTOR_STORAGE_PATH):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
    
    def save_vectors(self, vectors: np.ndarray, ids: List, vector_type: str):
        # Save vectors to FAISS index and metadata
        if len(vectors) == 0:
            logger.warning(f"No vectors to save for {vector_type}")
            return
        
        # Create FAISS index
        dimension = vectors.shape[1]
        index = faiss.IndexFlatIP(dimension) # Inner product, cosine similarity
        
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
        # Load FAISS index and metadata
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
        if index is None or index.ntotal == 0:
            return np.array([]), np.array([])
        
        # Normalize query vector
        query_vector = query_vector.astype('float32').reshape(1, -1)
        faiss.normalize_L2(query_vector)
        
        # Search for similar vectors
        similarities, indices = index.search(query_vector, top_k)
        
        return similarities[0], indices[0]

def get_interaction_weight(interaction_type: str) -> float:
    # Get weight for different interaction types based on schema
    weights = {
        'Going': 3.0, # RSVP Going
        'Interested': 1.5, # RSVP Interested (2.0 total)
        'created_event': 2.5, # User created the event
        'viewed_event_details': 1.0, # Clicked event
        'followed_user': 0.5, # Followed even host
        'joined_interest': 0.5
    }
    return weights.get(interaction_type, 1.0)
