# recommend.py: Load model and generate recommendations
import numpy as np
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .utils import (DatabaseConnector, VectorStore, EmbeddingGenerator,
                    TextPreprocessor, get_interaction_weight)

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Primary rec engine class"""

    def __init__(self):
        # Init helpers
        self.db_connector = DatabaseConnector()
        self.vector_store = VectorStore()
        self.embedding_generator = EmbeddingGenerator()
        self.preprocessor = TextPreprocessor()

        self.event_index = None
        self.event_ids = None

        # Load vectors on initialization
        self.load_vectors()

    def load_vectors(self):
        # Load pre-computed vectors into memory
        try:
            self.event_index, self.event_ids = self.vector_store.load_vectors(
                "events")

            if self.event_index:
                logger.info(f"Loaded {len(self.event_ids)} event vectors")
            else:
                logger.warning("No event vectors found")

        except Exception as e:
            logger.error(f"Error loading vectors: {e}")

    def get_user_vector(self, user_uid: str) -> Optional[np.ndarray]:
        # Get/compute user vector in real-time
        user = self.db_connector.fetch_user(user_uid)
        if not user:
            logger.warning(f"User {user_uid} not found")
            return None

        # Retrieve user interactions for real-time computations
        rsvps = self.db_connector.fetch_user_rsvps(user_uid)
        activities = self.db_connector.fetch_user_activity(user_uid)

        if rsvps or activities:
            # From interactions (Historical user, completed survey and has interacted with events)
            return self._compute_user_vector_from_interactions(user_uid, rsvps, activities)
        else:
            # From interests (New user)
            return self._compute_user_vector_from_interests(user)

    def _compute_user_vector_from_interests(self, user: Dict[str, Any]) -> Optional[np.ndarray]:
        # Compute user vector from interests
        interests = user.get('Interests', [])
        if not interests:
            return None

        interests_text = self.preprocessor.preprocess_user_interests(interests)
        # Generate embeddings from text
        return self.embedding_generator.generate_embedding(interests_text)

    def _compute_user_vector_from_interactions(self, user_uid: str,
                                               rsvps: List[Dict[str, Any]],
                                               activities: List[Dict[str, Any]]) -> Optional[np.ndarray]:
        # Compute user vector for event from interactions in real-time
        if not self.event_index or not self.event_ids:
            return self._compute_user_vector_from_interests(
                self.db_connector.fetch_user(user_uid) or {}
            )

        event_embeddings = []
        weights = []

        # Process recent RSVPs (TODO: last 30 days(?))
        recent_cutoff = datetime.now() - timedelta(days=30)
        for rsvp in rsvps:
            if rsvp['CreatedAt'] and rsvp['CreatedAt'] > recent_cutoff:
                event_id = rsvp['EventID']
                if event_id in self.event_ids:
                    event_idx = self.event_ids.index(event_id)
                    embedding = self.event_index.reconstruct(event_idx)
                    weight = get_interaction_weight(rsvp['Status'])
                    event_embeddings.append(embedding)
                    weights.append(weight)

        # Process recent activities (TODO: clicking, viewing for x amount of time, sharing, saving)
        for activity in activities:
            if activity['CreatedAt'] and activity['CreatedAt'] > recent_cutoff:
                if activity['ActivityType'] == 'viewed_event_details':
                    event_id = activity['TargetID']
                    if event_id in self.event_ids:
                        event_idx = self.event_ids.index(event_id)
                        embedding = self.event_index.reconstruct(event_idx)
                        weight = get_interaction_weight(
                            activity['ActivityType'])
                        event_embeddings.append(embedding)
                        weights.append(weight)

        # If no activity/RSVPs, new user, compute from interests
        if not event_embeddings:
            return self._compute_user_vector_from_interests(
                self.db_connector.fetch_user(user_uid) or {}
            )

        # Weighted average (w/ recency consideration, see recommend_events)
        weights_array = np.array(weights)
        embeddings_array = np.array(event_embeddings)

        if weights_array.sum() > 0:
            weights_array = weights_array / weights_array.sum()

        return np.average(embeddings_array, axis=0, weights=weights_array)

    def recommend_events(self, user_uid: str, top_k: int = 10,
                         filters: Optional[Dict[str, Any]] = None,
                         recommendation_strategy: str = "hybrid") -> List[Dict[str, Any]]:
        """Unified recommendation function with strategy options"""

        logger.info(
            f"Generating {recommendation_strategy} recommendations for user {user_uid}")

        try:
            if recommendation_strategy == "friends_only":
                return self._get_friend_primary_recommendations(user_uid, top_k, filters)

            # Hybrid approach (default)
            user_vector = self.get_user_vector(user_uid)
            if user_vector is None:
                logger.warning(
                    f"Could not generate vector for user {user_uid}")
                return self.get_fallback_recommendations(top_k, filters)

            if self.event_index is None or len(self.event_ids) == 0:
                logger.warning("No event vectors available")
                return self.get_fallback_recommendations(top_k, filters)

            # Search for similar events
            similarities, indices = self.vector_store.search_similar(
                user_vector, self.event_index, top_k * 3
            )

            # Process recommendations
            recommendations = []
            for similarity, idx in zip(similarities, indices):
                if idx < len(self.event_ids):
                    event_id = self.event_ids[idx]
                    event_details = self.get_event_details(event_id)
                    if event_details:
                        score = float(similarity)
                        score = self.apply_recency_boost(event_details, score)

                        recommendations.append({
                            **event_details,
                            'similarity_score': score,
                            'event_id': event_id,
                            'source': 'content_based'
                        })

            # Enhanced friend boosts with strategy awareness
            if recommendation_strategy in ["hybrid", "friends_boosted"]:
                recommendations = self.apply_friend_boosts(user_uid, recommendations,
                                                           strategy=recommendation_strategy)

            # Apply filters
            if filters:
                recommendations = self.apply_filters(recommendations, filters)

            # Sort and return
            recommendations.sort(
                key=lambda x: x['similarity_score'], reverse=True)
            final_recommendations = recommendations[:top_k]

            logger.info(
                f"Generated {len(final_recommendations)} recommendations for user {user_uid}")
            return final_recommendations

        except Exception as e:
            logger.error(
                f"Error generating recommendations for user {user_uid}: {e}")
            return self.get_fallback_recommendations(top_k, filters)

    def get_event_details(self, event_id: int) -> Optional[Dict[str, Any]]:
        # Pull event details from database
        events = self.db_connector.fetch_events()
        for event in events:
            if event['EventID'] == event_id:
                return event
        return None

    def apply_filters(self, events: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Apply filters to events
        filtered_events = events

        if 'location' in filters:
            location = filters['location'].lower()
            filtered_events = [e for e in filtered_events
                               if e.get('Location', '').lower().find(location) != -1]

        if 'category' in filters:
            category = filters['category'].lower()
            filtered_events = [e for e in filtered_events
                               if e.get('CategoryName', '').lower() == category]

        if 'date_range' in filters:
            start_date, end_date = filters['date_range']
            filtered_events = [e for e in filtered_events
                               if self._within_date_range(e, start_date, end_date)]

        logger.info(
            f"Applied filters: {len(events)} -> {len(filtered_events)} events")
        return filtered_events

    def _within_date_range(self, event: Dict[str, Any], start_date: datetime,
                           end_date: datetime) -> bool:
        # Check if event is within date range
        event_time = event.get('StartTime')
        if not event_time:
            return True

        if isinstance(event_time, str):
            try:
                event_time = datetime.fromisoformat(
                    event_time.replace('Z', '+00:00'))
            except:
                return True

        return start_date <= event_time <= end_date

    def apply_recency_boost(self, event: Dict[str, Any], base_score: float) -> float:
        # Boost score for events happening soon
        event_time = event.get('StartTime')
        if not event_time:
            return base_score

        if isinstance(event_time, str):
            try:
                event_time = datetime.fromisoformat(
                    event_time.replace('Z', '+00:00'))
            except:
                return base_score

        days_until_event = (event_time - datetime.now()).days

        # Boost events happening in the next 7 days
        if 0 <= days_until_event <= 7:
            boost = 1.0 + (7 - days_until_event) * 0.05  # 5% boost per day
            return base_score * min(boost, 1.3)  # Max 30% boost

        return base_score

    def apply_friend_boosts(self, user_uid: str, recommendations: List[Dict[str, Any]],
                            strategy: str = "hybrid") -> List[Dict[str, Any]]:
        """Enhanced friend boosts with configurable strategy"""

        friend_events = self.db_connector.fetch_friend_recommendations(
            user_uid, include_scoring=True
        )

        if not friend_events:
            return recommendations

        rec_map = {rec['event_id']: rec for rec in recommendations}

        for friend_event in friend_events:
            event_id = friend_event['EventID']

            # Calculate boost based on strategy
            if strategy == "friends_boosted":
                boost_multiplier = 1.5
            else:  # hybrid
                boost_multiplier = 1.2

            base_score = friend_event.get('BaseScore', 1.0)
            friend_count = friend_event.get('FriendCount', 1)
            friend_boost = base_score * \
                boost_multiplier * (1 + 0.1 * friend_count)

            if event_id in rec_map:
                rec_map[event_id]['similarity_score'] *= friend_boost
                rec_map[event_id]['friend_boost'] = friend_boost
                rec_map[event_id]['friend_username'] = friend_event['FriendUsername']
                rec_map[event_id]['friend_status'] = friend_event['FriendStatus']
            else:
                event_details = self.get_event_details(event_id)
                if event_details:
                    recommendations.append({
                        **event_details,
                        'event_id': event_id,
                        'similarity_score': 0.3 * friend_boost,
                        'friend_boost': friend_boost,
                        'friend_username': friend_event['FriendUsername'],
                        'friend_status': friend_event['FriendStatus'],
                        'source': 'friend_based'
                    })

        return recommendations

    def store_friend_recommendations(self, user_uid: str, recommendations: List[Dict[str, Any]]):
        """Store friend-based recommendations for quick access"""
        friend_recs = [
            rec for rec in recommendations
            if rec.get('friend_username') and rec.get('source') in ['friend_based', 'content_based']
        ]
        self.db_connector.store_friend_recommendations(user_uid, friend_recs)

    def _get_friend_primary_recommendations(self, user_uid: str, top_k: int,
                                            filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Integrated friend-primary recommendations"""
        friend_recommendations = self.db_connector.fetch_friend_recommendations(
            user_uid, include_scoring=True
        )

        recommendations = []
        for rec in friend_recommendations[:top_k * 2]:
            event_details = self.get_event_details(rec['EventID'])
            if event_details:
                base_score = rec.get('BaseScore', 1.0)
                friend_count = rec.get('FriendCount', 1)
                score = base_score * (1 + 0.2 * friend_count)

                recommendations.append({
                    **event_details,
                    'event_id': rec['EventID'],
                    'similarity_score': score,
                    'friend_username': rec['FriendUsername'],
                    'friend_status': rec['FriendStatus'],
                    'friend_count': friend_count,
                    'source': 'friend_primary'
                })

        if filters:
            recommendations = self.apply_filters(recommendations, filters)

        recommendations.sort(key=lambda x: x['similarity_score'], reverse=True)
        return recommendations[:top_k]

    def get_fallback_recommendations(self, top_k: int = 10,
                                     filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        # Fallback rec events after personalization fails (hopefully it never comes to this...)
        logger.info("Using fallback recommendations")

        events = self.db_connector.fetch_events(limit=top_k * 2)
        if filters:
            events = self.apply_filters(events, filters)

        # Sort by most recent and popular events, nearest start time
        events.sort(key=lambda x: x.get('StartTime', ''))

        # Add default score and reason
        for event in events[:top_k]:
            event['similarity_score'] = 0.0
            event['fallback_reason'] = 'personalized_recommendations_unavailable'

        return events[:top_k]

    def refresh_models(self):
        # Refresh model by reloading vectors
        logger.info("Refreshing recommendation models")
        self.load_vectors()


class RecommendationAPI:
    """API layer for recommendations"""

    def __init__(self):
        self.engine = RecommendationEngine()

    def get_recommendations(self, user_uid: str, top_k: int = 10,
                            filters: Optional[Dict[str, Any]] = None,
                            recommendation_strategy: str = "hybrid") -> Dict[str, Any]:
        recommendations = self.engine.recommend_events(
            user_uid, top_k, filters, recommendation_strategy
        )

        return {
            "user_uid": user_uid,
            "recommendations": recommendations,
            "count": len(recommendations),
            "filters_applied": filters or {},
            "strategy_used": recommendation_strategy
        }

    def refresh_models(self):
        # Externally refresh models
        self.engine.refresh_models()
        return {"status": "models_refreshed"}
