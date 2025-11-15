"""
Test recommendations for a specific user
Usage from server directory: python -m pytest tests/test_recommendations.py -s
Or run directly: python tests/test_recommendations.py
Modify TEST_USERNAME to test different users
"""
import sys
import os
from dotenv import load_dotenv

# Add project root to path for ml module imports
project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, project_root)

from ml.recommend import RecommendationAPI

# Load .env from server directory
server_env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(server_env_path)


# Configure test user here
TEST_USERNAME = "test_user15"


def test_recommendations():
    print("\n" + "="*70)
    print(f"TESTING RECOMMENDATIONS FOR {TEST_USERNAME}")
    print("="*70 + "\n")

    try:
        print("Step 1: Initializing recommendation engine...")
        api = RecommendationAPI()
        print("[OK] Engine initialized\n")

        # Fetch user by username
        print(f"Step 2: Looking up user '{TEST_USERNAME}'...")
        user = api.engine.db_connector.fetch_user_by_username(TEST_USERNAME)
        if not user:
            print(f"[ERROR] User '{TEST_USERNAME}' not found in database\n")
            return False

        test_user_uid = user['FirebaseUID']
        user_email = user.get('Email', 'N/A')
        print(f"[OK] Found user: {user.get('Username')} ({user_email})")
        print(f"     UID: {test_user_uid}\n")

        # Get user stats
        interests = user.get('Interests', [])
        rsvps = api.engine.db_connector.fetch_user_rsvps(test_user_uid)
        friends = api.engine.db_connector.fetch_user_friends(test_user_uid)
        activities = api.engine.db_connector.fetch_user_activity(test_user_uid)

        print(f"User Profile:")
        print(
            f"  - Interests: {len(interests)} ({', '.join(interests[:3])}{'...' if len(interests) > 3 else ''})")
        print(f"  - Following: {len(friends)} users")
        print(f"  - RSVPs: {len(rsvps)} events")
        print(f"  - Activities: {len(activities)} records\n")

        print("Step 3: Checking if vectors are loaded...")
        if api.engine.are_vectors_loaded():
            print(
                f"[OK] Vectors loaded: {len(api.engine.event_ids)} events indexed\n")
        else:
            print("[WARNING] No vectors loaded\n")

        print("Step 4: Getting hybrid recommendations (default)...")
        result = api.get_recommendations(
            user_uid=test_user_uid,
            top_k=10,
            recommendation_strategy="hybrid"
        )

        if 'error' in result:
            print(f"[ERROR] {result['error']}\n")
            return False

        recommendations = result.get('recommendations', [])
        print(f"[OK] Got {len(recommendations)} recommendations\n")

        if recommendations:
            print("Top 5 Recommendations:")
            print("-" * 70)
            for i, rec in enumerate(recommendations[:5], 1):
                title = rec.get('Title', 'Unknown')
                score = rec.get('similarity_score', 0)
                source = rec.get('source', 'unknown')
                friend = rec.get('friend_username', None)
                friend_status = rec.get('friend_status', None)

                print(f"{i}. {title[:50]}")
                print(f"   Score: {score:.3f} | Source: {source}")
                if friend:
                    print(f"   Friend: {friend} is {friend_status}")
                print()

        print("Step 5: Getting friends-only recommendations...")
        result_friends = api.get_recommendations(
            user_uid=test_user_uid,
            top_k=5,
            recommendation_strategy="friends_only"
        )

        friends_recs = result_friends.get('recommendations', [])
        print(f"[OK] Got {len(friends_recs)} friend-based recommendations\n")

        if friends_recs:
            print("Friend Recommendations:")
            print("-" * 70)
            for i, rec in enumerate(friends_recs, 1):
                title = rec.get('Title', 'Unknown')
                friend_username = rec.get('friend_username', 'Unknown')
                friend_status = rec.get('friend_status', 'Unknown')
                score = rec.get('similarity_score', 0)

                print(f"{i}. {title[:50]}")
                print(
                    f"   Score: {score:.3f} | Friend: {friend_username} ({friend_status})")
                print()

        # Summary
        print("="*70)
        print("[SUCCESS] TEST COMPLETED")
        print("="*70)

        print(f"\nRecommendation engine successfully generated:")
        print(f"  - {len(recommendations)} hybrid recommendations")
        print(f"  - {len(friends_recs)} friend-based recommendations")

        if recommendations:
            friend_boosted = sum(
                1 for r in recommendations if r.get('friend_username'))
            print(
                f"  - {friend_boosted}/{len(recommendations)} recommendations include friend boosts")

        print(
            f"\nUser '{TEST_USERNAME}' can view these recommendations in the web app.")
        print()

        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_recommendations()
    sys.exit(0 if success else 1)
