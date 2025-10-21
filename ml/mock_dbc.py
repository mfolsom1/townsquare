# mock_dbc.py: Model testing helpers
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MockDatabaseConnector:
    """Mock database connector for testing"""

    def __init__(self, test_user_id: str = "user_001"):
        self.test_user_id = test_user_id
        self.data = self._create_data()

    def _create_data(self) -> Dict[str, Any]:
        """Create mock user, event, and profile data"""
        pass

    def _create_rsvps(self, user_id: str, events: List[Dict]) -> List[Dict]:
        """Create mock RSVPs for a given user"""
        pass

    def _create_activities(self, user_id: str, events: List[Dict]) -> List[Dict]:
        """Create mock user activities"""
        pass

    def _create_friends(self, user_id: str, users: List[Dict]) -> List[Dict]:
        """Create mock friend connections"""
        pass

    def fetch_events(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch mock events"""
        pass

    def fetch_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch mock user by user ID"""
        pass

    def fetch_users_for_training(self, limit: int = 500) -> List[Dict[str, Any]]:
        """Fetch mock users for training"""
        pass

    def fetch_user_rsvps(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetch mock RSVPs for a given user"""
        pass

    def fetch_user_activity(self, user_id: str, activity_type: str = None) -> List[Dict[str, Any]]:
        """Fetch mock user activity"""
        pass

    def fetch_user_friends(self, user_id: str, limit: int = 3, include_activity: bool = False) -> List[Dict[str, Any]]:
        """Fetch mock user friends"""
        pass

    def fetch_friend_recommendations(self, user_id: str, include_scoring: bool = True) -> List[Dict[str, Any]]:
        """Fetch mock friend recommendations"""
        pass

    def store_friend_recommendations(self, user_id: str, friend_events: List[Dict[str, Any]]):
        """Store mock friend recommendations"""
        pass

    def get_connection(self):
        """Return a mock database connection"""
        class MockConnection:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def cursor(self): return self
            def execute(self, *args): pass
            def fetchall(self): return []
            def fetchone(self): return None
            def commit(self): pass
        return MockConnection()
