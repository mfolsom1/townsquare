# train.py: Implementation of model training
import numpy as np
import os
import logging
import json
import time
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from .utils import (
    DatabaseConnector,
    EmbeddingGenerator,
    VectorStore,
    TextPreprocessor,
    DataValidator,
    get_interaction_weight,
)

logger = logging.getLogger(__name__)


class ModelTrainer:
    """Model training pipeline for EVENT recommendations using content + similar user signals"""

    def __init__(self, storage_path: str = "model_artifacts", db_connector: Optional[DatabaseConnector] = None):
        # Allow injecting a db_connector (for tests) to reuse the
        # MockDatabaseConnector and avoid multiple fixture loads
        if db_connector is None:
            self.db_connector = DatabaseConnector()
        else:
            self.db_connector = db_connector
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = VectorStore()
        self.text_preprocessor = TextPreprocessor()
        self.data_validator = DataValidator()

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Training configuration
        self.config = {
            "min_events_for_training": 10,  # Reduce later for faster iteration
            "embedding_dimension": 384,
            "similarity_threshold": 0.7,
            "retraining_interval_days": 7,
        }

    def generate_event_embeddings(self) -> bool:
        """Generate event embeddings, content-based recommendations"""
        try:
            logger.info("Generating event embeddings...")

            # Fetch events from database
            events = self.db_connector.fetch_events()

            if len(events) < self.config["min_events_for_training"]:
                logger.warning(
                    f"Insufficient events for training: {len(events)}")
                return False

            # Validate event data
            valid_events = self.data_validator.validate_events(events)
            logger.info(f"Validated {len(valid_events)}/{len(events)} events")

            # Preprocess event text
            event_texts = []
            event_ids = []

            for event in valid_events:
                processed_text = self.text_preprocessor.preprocess_event_text(
                    event)
                event_texts.append(processed_text)
                event_ids.append(event["EventID"])

            # Generate embeddings in batches
            embeddings = self.embedding_generator.generate_embeddings_batch(
                event_texts)

            if len(embeddings) == 0:
                logger.error("No embeddings generated")
                return False

            # Store vectors
            self.vector_store.save_vectors(embeddings, event_ids, "events")

            # Save event metadata for quick access
            self._save_event_metadata(valid_events)

            # Cache marker
            version_info = {
                'version': int(time.time()),
                'event_count': len(event_ids),
                'created_at': datetime.now().isoformat()
            }
            version_path = self.storage_path / "cache_version.json"
            # Write version info atomically to avoid partial files
            try:
                tmp_version = version_path.with_suffix('.json.tmp')
                with open(tmp_version, 'w', encoding='utf8') as f:
                    json.dump(version_info, f)
                os.replace(str(tmp_version), str(version_path))
            except Exception as e:
                logger.error(
                    f"Error writing cache version file {version_path}: {e}")
                try:
                    if tmp_version.exists():
                        tmp_version.unlink()
                except Exception:
                    pass

            logger.info(
                f"Successfully generated embeddings for {len(event_ids)} events"
            )
            return True

        except Exception as e:
            logger.error(f"Error generating event embeddings: {e}")
            return False

    def generate_user_embeddings(self) -> bool:
        """Generate user embeddings to find similar users for event recommendations"""
        try:
            logger.info("Generating user embeddings...")

            # Fetch users with their interests
            users_data = self.db_connector.fetch_users_for_training()

            if not users_data:
                logger.warning("No user data available for training")
                return False

            user_embeddings = []
            user_uids = []

            for user in users_data:
                # Create comprehensive user profile text
                profile_text = self.text_preprocessor.preprocess_user_profile(
                    user)

                if profile_text.strip():
                    embedding = self.embedding_generator.generate_embedding(
                        profile_text
                    )
                    user_embeddings.append(embedding)
                    user_uids.append(user["FirebaseUID"])

            if user_embeddings:
                embeddings_array = np.array(user_embeddings)
                self.vector_store.save_vectors(
                    embeddings_array, user_uids, "users")
                logger.info(f"Generated embeddings for {len(user_uids)} users")

            return True

        except Exception as e:
            logger.error(f"Error generating user embeddings: {e}")
            return False

    def find_similar_users(self, user_uid: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Find users with similar interests (event recommendation cross-pollination)"""
        try:
            user_index, user_ids = self.vector_store.load_vectors("users")

            if user_index is None:
                logger.warning(
                    "No user vectors available for similarity search")
                return []

            # Find the current user's index
            if user_uid not in user_ids:
                logger.warning(f"User {user_uid} not found in user vectors")
                return []

            user_idx = user_ids.index(user_uid)
            user_vector = user_index.reconstruct(user_idx)

            # Find similar users (excluding self)
            similarities, indices = self.vector_store.search_similar(
                user_vector, user_index, top_k + 1  # +1 to account for self
            )

            similar_users = []
            for similarity, idx in zip(similarities, indices):
                if idx < len(user_ids):
                    similar_user_uid = user_ids[idx]
                    if similar_user_uid != user_uid:  # Exclude self
                        similar_users.append(
                            {
                                "user_uid": similar_user_uid,
                                "similarity_score": float(similarity),
                            }
                        )

            logger.info(
                f"Found {len(similar_users)} similar users for {user_uid}")
            return similar_users[:top_k]

        except Exception as e:
            logger.error(f"Error finding similar users for {user_uid}: {e}")
            return []

    def get_events_from_similar_users(self, user_uid: str, top_k: int = 10,
                                      include_friends: bool = True) -> List[Dict[str, Any]]:
        """Enhanced version: Get events from similar users with friend integration"""
        try:
            all_recommended_events = []

            # Get events from similar users
            similar_users = self.find_similar_users(user_uid, top_k=3)

            for similar_user in similar_users:
                similar_user_uid = similar_user["user_uid"]
                similarity_score = similar_user["similarity_score"]

                user_rsvps = self.db_connector.fetch_user_rsvps(
                    similar_user_uid)

                for rsvp in user_rsvps[:5]:
                    if rsvp["Status"] in ["Going", "Interested"]:
                        event_score = similarity_score * \
                            get_interaction_weight(rsvp["Status"])

                        all_recommended_events.append({
                            "event_id": rsvp["EventID"],
                            "similar_user_uid": similar_user_uid,
                            "similarity_score": similarity_score,
                            "event_score": event_score,
                            "source": "similar_user",
                        })

            # Integrate friend-based events if requested
            if include_friends:
                friend_events = self._get_friend_based_events(user_uid)
                all_recommended_events.extend(friend_events)

            # Remove duplicates and sort
            unique_events = {}
            for event in all_recommended_events:
                event_id = event["event_id"]
                if (event_id not in unique_events or
                        event["event_score"] > unique_events[event_id]["event_score"]):
                    unique_events[event_id] = event

            recommended_events = sorted(
                unique_events.values(), key=lambda x: x["event_score"], reverse=True
            )

            logger.info(
                f"Found {len(recommended_events)} events for {user_uid}")
            return recommended_events[:top_k]

        except Exception as e:
            logger.error(f"Error getting events from similar users: {e}")
            return []

    def _get_friend_based_events(self, user_uid: str) -> List[Dict[str, Any]]:
        """Helper method to get friend-based events (integrated into main flow)"""
        friend_events = []

        # Get top 3 friends
        friends = self.db_connector.fetch_user_friends(user_uid, limit=3)
        if not friends:
            return friend_events

        # Get friend recommendations with scoring
        friend_recommendations = self.db_connector.fetch_friend_recommendations(
            user_uid, include_scoring=True
        )

        for rec in friend_recommendations:
            # Calculate friend influence score
            base_score = rec.get('BaseScore', 1.0)
            friend_count = rec.get('FriendCount', 1)

            # Friends have higher weight than similar users
            friend_weight = 2.0
            event_score = base_score * friend_weight * \
                (1 + 0.2 * friend_count)  # 20% boost per additional friend

            friend_events.append({
                "event_id": rec["EventID"],
                # Could aggregate multiple friends
                "friend_usernames": [rec["FriendUsername"]],
                "friend_status": rec["FriendStatus"],
                "event_score": event_score,
                "source": "friend_activity",
            })

        return friend_events

    def train_collaborative_filtering(self) -> bool:
        """Train collaborative filtering model using user-event interactions"""
        try:
            logger.info("Training collaborative filtering model...")

            # Get user-event interactions for training
            interactions = self._get_user_event_interactions()

            if len(interactions) < 20:  # Minimum interactions needed
                logger.warning(
                    f"Insufficient interactions for CF: {len(interactions)}")
                return False

            # Simple user-user collaborative filtering implementation
            user_similarity_matrix = self._compute_user_similarity_matrix()

            # Save collaborative filtering artifacts
            self._save_collaborative_model(user_similarity_matrix)

            logger.info("Collaborative filtering model trained successfully")
            return True

        except Exception as e:
            logger.error(f"Error training collaborative filtering model: {e}")
            return False

    def _get_user_event_interactions(self) -> List[Dict[str, Any]]:
        """Get user-event interactions for collaborative filtering"""
        try:
            # Get all RSVPs as interactions
            with self.db_connector.get_connection() as conn:
                cursor = conn.cursor()

                query = """
                SELECT 
                    UserUID,
                    EventID,
                    CASE 
                        WHEN Status = 'Going' THEN 2.0
                        WHEN Status = 'Interested' THEN 1.0
                        ELSE 0.0
                    END as interaction_score,
                    CreatedAt
                FROM RSVPs
                WHERE Status IN ('Going', 'Interested')
                AND CreatedAt > DATEADD(day, -90, GETDATE())
                """

                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Error fetching user-event interactions: {e}")
            return []

    def _compute_user_similarity_matrix(self) -> Dict[str, Dict[str, float]]:
        """Compute user by user similarity matrix (collaborative filtering)"""
        try:
            # Load user vectors for similarity computation
            user_index, user_ids = self.vector_store.load_vectors("users")

            if user_index is None:
                return {}

            similarity_matrix = {}
            for i, user_uid in enumerate(user_ids):
                user_vector = user_index.reconstruct(i)

                # Find similar users
                similarities, indices = self.vector_store.search_similar(
                    user_vector, user_index, top_k=20
                )

                user_similarities = {}
                for similarity, idx in zip(similarities, indices):
                    if idx < len(user_ids) and user_ids[idx] != user_uid:
                        user_similarities[user_ids[idx]] = float(similarity)

                similarity_matrix[user_uid] = user_similarities

            return similarity_matrix

        except Exception as e:
            logger.error(f"Error computing user similarity matrix: {e}")
            return {}

    def _save_collaborative_model(self, similarity_matrix: Dict[str, Dict[str, float]]):
        """Save collaborative filtering model artifacts"""
        try:
            model_path = self.storage_path / "collaborative_model.pkl"
            with open(model_path, "wb") as f:
                pickle.dump(
                    {
                        "similarity_matrix": similarity_matrix,
                        "trained_at": datetime.now().isoformat(),
                    },
                    f,
                )

            logger.info("Saved collaborative filtering model")
        except Exception as e:
            logger.error(f"Error saving collaborative model: {e}")

    def _save_event_metadata(self, events: List[Dict[str, Any]]):
        """Save event metadata for quick access"""
        try:
            metadata_path = self.storage_path / "event_metadata.pkl"
            metadata = {
                event["EventID"]: {
                    "Title": event.get("Title"),
                    "Description": event.get("Description"),
                    "StartTime": event.get("StartTime"),
                    "Location": event.get("Location"),
                    "CategoryName": event.get("CategoryName"),
                    "Tags": event.get("Tags", []),
                }
                for event in events
            }

            # Write to tmp file and replace
            tmp_meta = metadata_path.with_suffix('.pkl.tmp')
            try:
                with open(tmp_meta, "wb") as f:
                    pickle.dump(metadata, f)
                    f.flush()
                    try:
                        os.fsync(f.fileno())
                    except Exception:
                        # os.fsync may not be available on all platforms/filesystems
                        pass
                os.replace(str(tmp_meta), str(metadata_path))
                logger.info(f"Saved metadata for {len(metadata)} events")
            except Exception as e:
                logger.error(f"Error writing event metadata atomically: {e}")
                try:
                    if tmp_meta.exists():
                        tmp_meta.unlink()
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Error saving event metadata: {e}")

    def _generate_friend_insights(self):
        """Generate insights about friend relationships for recommendation weighting"""
        try:
            # This could analyze friend networks, mutual interests, etc.
            # TODO: Placeholder
            logger.info(
                "Friend insights generation placeholder - ready for implementation")

        except Exception as e:
            logger.error(f"Error generating friend insights: {e}")

    def evaluate_recommendation_quality(self) -> Dict[str, Any]:
        """Evaluate recommendation quality with basic metrics"""
        try:
            logger.info("Evaluating recommendation quality...")

            # TODO: proper offline evaluation
            evaluation_results = {
                "event_coverage": self._calculate_event_coverage(),
                "user_coverage": self._calculate_user_coverage(),
                "embedding_quality": self._evaluate_embedding_quality(),
                "evaluation_date": datetime.now().isoformat(),
            }

            # Save evaluation results
            eval_path = self.storage_path / "evaluation_results.json"
            with open(eval_path, "w") as f:
                import json
                json.dump(evaluation_results, f, indent=2)

            logger.info("Recommendation quality evaluation completed")
            return evaluation_results

        except Exception as e:
            logger.error(f"Error evaluating recommendation quality: {e}")
            return {}

    def _calculate_event_coverage(self) -> float:
        """Calculate what percentage of events are reachable by recommendations"""
        try:
            events = self.db_connector.fetch_events()
            if not events:
                return 0.0

            # Load event vectors to see how many we can recommend
            event_index, event_ids = self.vector_store.load_vectors("events")

            if event_index is None:
                return 0.0

            # TODO: basic coverage metric, update later
            coverage = len(event_ids) / len(events)
            return round(coverage, 4)

        except Exception as e:
            logger.error(f"Error calculating event coverage: {e}")
            return 0.0

    def _calculate_user_coverage(self) -> float:
        """Calculate what percentage of users can receive personalized recommendations"""
        try:
            # Count users with enough data for recommendations
            with self.db_connector.get_connection() as conn:
                cursor = conn.cursor()

                query = """
                SELECT COUNT(DISTINCT u.FirebaseUID) as covered_users
                FROM Users u
                WHERE EXISTS (
                    SELECT 1 FROM UserInterests ui WHERE ui.UserUID = u.FirebaseUID
                ) OR EXISTS (
                    SELECT 1 FROM RSVPs r WHERE r.UserUID = u.FirebaseUID 
                    AND r.Status IN ('Going', 'Interested')
                )
                """

                cursor.execute(query)
                covered_users = cursor.fetchone()[0]

                total_users_query = "SELECT COUNT(*) FROM Users"
                cursor.execute(total_users_query)
                total_users = cursor.fetchone()[0]

                if total_users == 0:
                    return 0.0

                coverage = covered_users / total_users
                return round(coverage, 4)

        except Exception as e:
            logger.error(f"Error calculating user coverage: {e}")
            return 0.0

    def _evaluate_embedding_quality(self) -> Dict[str, float]:
        """Embedding quality evaluation"""
        try:
            # Load event vectors to check quality
            event_index, event_ids = self.vector_store.load_vectors("events")

            if event_index is None:
                return {"quality_score": 0.0}

            # TODO: better metric than evaluating vector distribution (relevance, usefulness > quantity)
            quality_score = min(len(event_ids) / 100.0, 1.0)

            return {
                "quality_score": round(quality_score, 4),
                "events_embedded": len(event_ids),
            }

        except Exception as e:
            logger.error(f"Error evaluating embedding quality: {e}")
            return {"quality_score": 0.0}

    def full_training_pipeline(self, include_friend_integration: bool = True) -> bool:
        """Enhanced training pipeline with friend integration option"""
        try:
            logger.info("Starting enhanced training pipeline...")

            # 1: Generate event embeddings (content-based)
            event_success = self.generate_event_embeddings()
            if not event_success:
                logger.error("Event embeddings generation failed.")
                return False

            # 2: Generate user embeddings
            user_success = self.generate_user_embeddings()
            if not user_success:
                logger.warning(
                    "User embeddings generation had issues... continuing.")

            # 3: Train collaborative filtering
            cf_success = self.train_collaborative_filtering()
            if not cf_success:
                logger.info(
                    "Collaborative filtering skipped due to insufficient data.")

            # 4: Generate friend relationship insights
            if include_friend_integration:
                self._generate_friend_insights()

            # 5: Evaluate models
            evaluation_results = self.evaluate_recommendation_quality()
            logger.info(f"Model evaluation results: {evaluation_results}")

            logger.info("Enhanced training pipeline completed successfully")
            return True

        except Exception as e:
            logger.error(f"Training pipeline failed: {e}")
            return False

    def refresh_models(self) -> bool:
        """Refresh all models by retraining"""
        logger.info("Refreshing all ML models...")
        return self.full_training_pipeline()


def main():
    """Main training function"""
    trainer = ModelTrainer()
    success = trainer.full_training_pipeline()

    if success:
        logger.info("Training successful!")
        eval_results = trainer.evaluate_recommendation_quality()
        logger.info(f"Evaluation Summary: {eval_results}")
    else:
        logger.error("Training failed.")
        exit(1)


if __name__ == "__main__":
    main()
