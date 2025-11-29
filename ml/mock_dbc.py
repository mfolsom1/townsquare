# mock_dbc.py: Model testing helpers
import json
import os
from pathlib import Path
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MockDatabaseConnector:
    """Mock database connector for testing.

    This connector generates in-memory mock data for the offline test_mock.py file.
    If an environment variable `ML_TEST_FIXTURE` is set or a file exists at
    `ml/fixtures/production_fixture.json`, the connector will load that JSON
    fixture and use it instead. 
    NOTE: The fixture does not contain sanitized data.
    """

    def __init__(self, test_user_id: str = "user_001", fixture_path: Optional[str] = None):
        self.test_user_id = test_user_id

        # Resolve fixture path, env var overrides explicit arg.
        # Default path is ml/fixtures/production_fixture.json
        env_path = os.environ.get('ML_TEST_FIXTURE')
        if env_path:
            fixture_path = env_path

        if fixture_path is None:
            default_fixture = Path(__file__).resolve(
            ).parent.parent / 'ml' / 'fixtures' / 'production_fixture.json'
            # Also accept ml/fixtures relative to repo root
            alt_fixture = Path(__file__).resolve().parent / \
                'fixtures' / 'production_fixture.json'
            if default_fixture.exists():
                fixture_path = str(default_fixture)
            elif alt_fixture.exists():
                fixture_path = str(alt_fixture)
            else:
                fixture_path = None

        if fixture_path and Path(fixture_path).exists():
            try:
                with open(fixture_path, 'r', encoding='utf8') as fh:
                    fixture = json.load(fh)
                logger.info(f"Loaded test fixture from {fixture_path}")
                # Normalize fixture keys into self.data
                self.data = {
                    'events': fixture.get('events', []),
                    'users': fixture.get('users', []),
                    'rsvps': fixture.get('rsvps', []),
                    'activities': fixture.get('activities', []),
                    'friends': fixture.get('friends', []),
                    'friend_recs': fixture.get('friend_recommendations', fixture.get('friend_recs', [])),
                }
                # Removing synthetic test events (titles like 'Test Event')
                try:
                    self._remove_synthetic_test_events()
                except Exception:
                    # Don't fail loading fixture on sanitization issues
                    pass
            except Exception as e:
                logger.error(f"Failed to load fixture {fixture_path}: {e}")
                # Fallback to generated mock data
                self.data = self._create_data()
        else:
            # No fixture provided->generate default mock data
            self.data = self._create_data()

    def _create_data(self) -> Dict[str, Any]:
        """Create mock user, event, and profile data"""
        now = datetime.now()

        # Create a few mock events TODO: unnecessary with fixture
        events = []
        # Create 12 events to meet training minimum req
        for i in range(1, 13):
            events.append({
                "EventID": i,
                "Title": f"Event {i}",
                "Description": f"Description for event {i}",
                "StartTime": (now + timedelta(days=i)).isoformat(),
                "EndTime": (now + timedelta(days=i, hours=2)).isoformat(),
                "Location": "Testville",
                "CategoryName": "Community",
                "Tags": ["test", "community"] if i % 2 == 0 else ["fun"],
            })

        # Create a few mock users
        users = []
        for j in range(1, 5):
            users.append({
                "FirebaseUID": f"user_{j:03d}",
                "Username": f"tester{j}",
                "Interests": ["music", "sports"] if j % 2 == 0 else ["art"],
                "Bio": f"Bio for user {j}",
                "Location": "Testville",
            })

        # RSVPs for users (test_user attending some events)
        rsvps = self._create_rsvps(self.test_user_id, events)

        # Activities
        activities = self._create_activities(self.test_user_id, events)

        # Friends (simple connections)
        friends = self._create_friends(self.test_user_id, users)

        # Friend recommendations (one or two)
        friend_recs = [
            {
                "EventID": 2,
                "FriendUsername": "tester2",
                "FriendStatus": "Going",
                "BaseScore": 2.0,
                "FriendCount": 1,
            },
            {
                "EventID": 5,
                "FriendUsername": "tester3",
                "FriendStatus": "Interested",
                "BaseScore": 1.0,
                "FriendCount": 2,
            },
        ]

        return {
            "events": events,
            "users": users,
            "rsvps": rsvps,
            "activities": activities,
            "friends": friends,
            "friend_recs": friend_recs,
        }

    def _remove_synthetic_test_events(self):
        """Filter out any event whose Title contains 'Test Event' (case-insensitive)
        or which has a tag 'test'. Also filters events with obviously generated Lorem Ipsum content.
        """
        events = self.data.get('events', [])
        if not events:
            return
        filtered = []
        removed_count = 0

        for e in events:
            title = (e.get('Title') or e.get('title') or '')
            tags = e.get('Tags') or []
            description = (e.get('Description') or e.get('description') or '')

            # Check for test events
            if isinstance(title, str) and 'test event' in title.lower():
                logger.info(f"Removing synthetic test event: {title}")
                removed_count += 1
                continue

            # Check for test tags
            if any((isinstance(t, str) and t.lower() == 'test') for t in tags):
                logger.info(f"Removing event with test tag: {title}")
                removed_count += 1
                continue

            # Check for placeholder/generated content (common phrases in fake data)
            if isinstance(description, str) and len(description) > 100:
                suspicious_phrases = [
                    'lorem ipsum', 'dolor sit amet', 'consectetur adipiscing',
                    'test description', 'placeholder text'
                ]
                if any(phrase in description.lower() for phrase in suspicious_phrases):
                    logger.info(
                        f"Removing event with placeholder content: {title}")
                    removed_count += 1
                    continue

            filtered.append(e)

        self.data['events'] = filtered
        if removed_count > 0:
            logger.info(
                f"Filtered out {removed_count} synthetic/test events from fixture")

    def _create_rsvps(self, user_id: str, events: List[Dict]) -> List[Dict]:
        """Create mock RSVPs for a given user"""
        now = datetime.now()
        rsvps = []
        # Mark the test user as Interested/Going for first three events
        statuses = ["Going", "Interested", "Going"]
        for ev, status in zip(events[:3], statuses):
            rsvps.append({
                "RSVPID": f"rsvp_{ev['EventID']}",
                "UserUID": user_id,
                "EventID": ev["EventID"],
                "Status": status,
                "CreatedAt": (now - timedelta(days=1)).isoformat(),
            })
        return rsvps

    def _create_activities(self, user_id: str, events: List[Dict]) -> List[Dict]:
        """Create mock user activities"""
        now = datetime.now()
        activities = []
        # Create some view activities
        for ev in events[3:5]:
            activities.append({
                "ActivityID": f"act_{ev['EventID']}",
                "UserUID": user_id,
                "ActivityType": "viewed_event_details",
                "TargetID": ev["EventID"],
                "Description": "User viewed event details",
                "CreatedAt": (now - timedelta(days=2)).isoformat(),
            })
        return activities

    def _create_friends(self, user_id: str, users: List[Dict]) -> List[Dict]:
        """Create mock friend connections"""
        friends = []
        for u in users[:3]:
            friends.append({
                "FirebaseUID": u["FirebaseUID"],
                "Username": u["Username"],
            })
        return friends

    def fetch_events(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch mock events"""
        events = self.data.get("events", [])
        if limit:
            return events[:limit]
        return events

    def fetch_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch mock user by user ID or username"""
        for u in self.data.get("users", []):
            if u.get("FirebaseUID") == user_id or u.get("Username") == user_id:
                return u
        # allow test_user_id match with fallback default user
        if user_id == self.test_user_id:
            return {
                "FirebaseUID": self.test_user_id,
                "Username": "test_user",
                "Interests": ["music", "art"],
                "Bio": "Test user bio",
                "Location": "Test City",
                "UserType": "individual",
                "OrganizationName": None,
            }
        return None

    def fetch_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Fetch mock user by username (wrapper for consistency with DatabaseConnector)"""
        return self.fetch_user(username)

    def fetch_users_for_training(self, limit: int = 500) -> List[Dict[str, Any]]:
        """Fetch mock users for training"""
        users = self.data.get("users", [])
        return users[:limit]

    def fetch_user_rsvps(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetch mock RSVPs for a given user"""
        return [r for r in self.data.get("rsvps", []) if r.get("UserUID") == user_id]

    def fetch_user_activity(self, user_id: str, activity_type: str = None) -> List[Dict[str, Any]]:
        """Fetch mock user activity"""
        acts = [a for a in self.data.get(
            "activities", []) if a.get("UserUID") == user_id]
        if activity_type:
            acts = [a for a in acts if a.get("ActivityType") == activity_type]
        return acts

    def fetch_user_friends(self, user_id: str, limit: int = 100, include_activity: bool = False) -> List[Dict[str, Any]]:
        """Fetch mock user friends - returns list of users that user_id is following with mutual status"""
        all_friends = self.data.get("friends", [])

        # Get friend relationships where user_id is the follower
        friend_relationships = [
            f for f in all_friends
            if f.get("FollowerUID") == user_id
        ]

        if not friend_relationships:
            return []

        # Get the actual user records for the friends
        friend_uids = [f["FollowingUID"] for f in friend_relationships]
        friends_list = []

        for friend_uid in friend_uids[:limit]:
            friend_user = self.fetch_user(friend_uid)
            if friend_user:
                # Check if this is a mutual follow (friendship)
                is_mutual = any(
                    f.get("FollowerUID") == friend_uid and f.get(
                        "FollowingUID") == user_id
                    for f in all_friends
                )

                friends_list.append({
                    "FirebaseUID": friend_user.get("FirebaseUID"),
                    # Alias for compatibility
                    "FriendUID": friend_user.get("FirebaseUID"),
                    "Username": friend_user.get("Username", "Unknown"),
                    "FirstName": friend_user.get("FirstName", ""),
                    "LastName": friend_user.get("LastName", ""),
                    "IsMutual": is_mutual  # Track mutual friendship
                })

        return friends_list

    def fetch_friend_recommendations(self, user_id: str, include_scoring: bool = True) -> List[Dict[str, Any]]:
        """Generate friend recommendations dynamically from fixture data"""
        # Get user's friends (IsMutual flag for boosting)
        friends = self.fetch_user_friends(user_id, limit=100)

        if not friends:
            logger.debug(f"No friends found for user {user_id}")
            return []

        friend_events = {}

        # Aggregate events that friends are attending/interested in
        for friend in friends:
            friend_uid = friend.get('FriendUID', friend.get('FirebaseUID'))
            friend_username = friend.get('Username', 'Unknown')
            is_mutual = friend.get('IsMutual', False)

            # Get friend's RSVPs
            friend_rsvps = self.fetch_user_rsvps(friend_uid)

            for rsvp in friend_rsvps:
                event_id = rsvp.get('EventID')
                status = rsvp.get('Status', 'Interested')

                if event_id not in friend_events:
                    friend_events[event_id] = {
                        'EventID': event_id,
                        'FriendUsername': friend_username,
                        'FriendStatus': status,
                        'FriendCount': 0,
                        'MutualFriendCount': 0,  # Track mutual friends separately
                        'BaseScore': 0.0,
                        'Statuses': [],
                        'IsMutual': is_mutual
                    }

                friend_events[event_id]['FriendCount'] += 1
                if is_mutual:
                    friend_events[event_id]['MutualFriendCount'] += 1

                friend_events[event_id]['Statuses'].append(status)

                # Score based on RSVP status
                status_scores = {'Going': 1.0, 'Maybe': 0.7, 'Interested': 0.5}
                base_score = status_scores.get(status, 0.5)

                # Apply 1.5x multiplier for mutual friendships
                if is_mutual:
                    base_score *= 1.5

                friend_events[event_id]['BaseScore'] += base_score

        # Convert to list
        result = list(friend_events.values())

        if include_scoring and result:
            # Normalize scores by friend count
            for rec in result:
                rec['BaseScore'] = rec['BaseScore'] / \
                    max(rec['FriendCount'], 1)

                # Use most enthusiastic friend's status as primary status
                if 'Going' in rec['Statuses']:
                    rec['FriendStatus'] = 'Going'
                elif 'Maybe' in rec['Statuses']:
                    rec['FriendStatus'] = 'Maybe'
                else:
                    rec['FriendStatus'] = 'Interested'

                # Clean up temporary field
                del rec['Statuses']

        logger.info(
            f"Generated {len(result)} friend recommendations for user {user_id} "
            f"({sum(1 for r in result if r.get('MutualFriendCount', 0) > 0)} with mutual follow boost)"
        )
        return result

    def store_friend_recommendations(self, user_id: str, friend_events: List[Dict[str, Any]]):
        """Store mock friend recommendations"""
        # For mock, just log and keep in memory
        logger.info(
            f"Mock store {len(friend_events)} friend recs for {user_id}")
        self.data["friend_recs"] = friend_events

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
