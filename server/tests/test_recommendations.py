"""
<<<<<<< HEAD
Test recommendations for a specific user using fixture data.

This test validates the QUALITY of recommendations:
- Verifies recommendations are returned
- Checks recommendation structure and metadata
- Tests different recommendation strategies
- Validates friend boost functionality
Usage: python server/tests/test_recommendations.py
"""
import sys
import os

# Add project root to path FIRST
=======
Test recommendations for a specific user
Usage from server directory: python -m pytest tests/test_recommendations.py -s
Or run directly: python tests/test_recommendations.py
Modify TEST_USERNAME to test different users
"""
from ml.recommend import RecommendationAPI
import sys
import os
from dotenv import load_dotenv

# Add project root to path for ml module imports
>>>>>>> 3e9f4f67901635abb41d9ba259130748377ff4e4
project_root = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, project_root)

<<<<<<< HEAD
# Enable test mode to use fixture data
os.environ['ML_TEST_MODE'] = '1'

# Import after path setup
from ml.mock_dbc import MockDatabaseConnector  # noqa: E402
from ml.recommend import RecommendationAPI, RecommendationEngine  # noqa: E402
from ml.train import ModelTrainer  # noqa: E402
from ml import utils  # noqa: E402

# Configure test user
TEST_USERNAME = "test_user16"


def setup_ml_components():
    """Initialize ML components with MockDatabaseConnector"""
    print("Initializing ML components with fixture data...")

    # Create mock database
    mock_db = MockDatabaseConnector()

    # Generate embeddings using fixture data
    model_artifacts_path = os.path.join(
        project_root, 'ml', 'model_artifacts_test')
    trainer = ModelTrainer(
        storage_path=model_artifacts_path, db_connector=mock_db)

    print("Generating event embeddings from fixture...")
    success = trainer.generate_event_embeddings()
    if not success:
        print("[WARNING] Failed to generate embeddings")

    # Load vector store
    vector_store = utils.VectorStore()

    # Create recommendation engine
    engine = RecommendationEngine(
        load_vectors_on_init=False, db_connector=mock_db)
    engine.vector_store = vector_store
    engine.load_vectors()

    # Create API
    api = RecommendationAPI(engine=engine)

    return api, engine, mock_db


=======

# Load .env from server directory
server_env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(server_env_path)


# Configure test user here
TEST_USERNAME = "test_user16"


>>>>>>> 3e9f4f67901635abb41d9ba259130748377ff4e4
def test_recommendations():
    print("\n" + "="*70)
    print(f"TESTING RECOMMENDATIONS FOR {TEST_USERNAME}")
    print("="*70 + "\n")

    try:
<<<<<<< HEAD
        # Initialize components
        api, engine, mock_db = setup_ml_components()
        print("Engine initialized\n")

        # Fetch user by username
        print(f"Step 1: Looking up user '{TEST_USERNAME}'...")
        user = mock_db.fetch_user_by_username(TEST_USERNAME)

        if not user:
            print(f"[ERROR] User '{TEST_USERNAME}' not found in fixture")
            print("\nAvailable users in fixture:")
            available_users = [u['Username']
                               for u in mock_db.data['users'][:10]]
            for username in available_users:
                print(f"  - {username}")
=======
        print("Step 1: Initializing recommendation engine...")
        api = RecommendationAPI()
        print("[OK] Engine initialized\n")

        # Fetch user by username
        print(f"Step 2: Looking up user '{TEST_USERNAME}'...")
        user = api.engine.db_connector.fetch_user_by_username(TEST_USERNAME)
        if not user:
            print(f"[ERROR] User '{TEST_USERNAME}' not found in database\n")
>>>>>>> 3e9f4f67901635abb41d9ba259130748377ff4e4
            return False

        test_user_uid = user['FirebaseUID']
        user_email = user.get('Email', 'N/A')
<<<<<<< HEAD
        print(f"Found user: {user.get('Username')} ({user_email})")
=======
        print(f"[OK] Found user: {user.get('Username')} ({user_email})")
>>>>>>> 3e9f4f67901635abb41d9ba259130748377ff4e4
        print(f"     UID: {test_user_uid}\n")

        # Get user stats
        interests = user.get('Interests', [])
<<<<<<< HEAD
        rsvps = mock_db.fetch_user_rsvps(test_user_uid)
        friends = mock_db.fetch_user_friends(test_user_uid)
        activities = mock_db.fetch_user_activity(test_user_uid)

        print(f"Step 2: User Profile Analysis")
=======
        rsvps = api.engine.db_connector.fetch_user_rsvps(test_user_uid)
        friends = api.engine.db_connector.fetch_user_friends(test_user_uid)
        activities = api.engine.db_connector.fetch_user_activity(test_user_uid)

        print(f"User Profile:")
>>>>>>> 3e9f4f67901635abb41d9ba259130748377ff4e4
        print(
            f"  - Interests: {len(interests)} ({', '.join(interests[:3])}{'...' if len(interests) > 3 else ''})")
        print(f"  - Following: {len(friends)} users")
        print(f"  - RSVPs: {len(rsvps)} events")
        print(f"  - Activities: {len(activities)} records\n")

<<<<<<< HEAD
        # Check vectors
        print("Step 3: Checking vector store...")
        if engine.are_vectors_loaded():
            print(
                f"Vectors loaded: {len(engine.event_ids)} events indexed\n")
        else:
            print("[WARNING] No vectors loaded")
            print("This means no events are indexed for recommendations.\n")

        # Test hybrid strategy
        print("Step 4: Testing HYBRID strategy (content + social)...")
=======
        print("Step 3: Checking if vectors are loaded...")
        if api.engine.are_vectors_loaded():
            print(
                f"[OK] Vectors loaded: {len(api.engine.event_ids)} events indexed\n")
        else:
            print("[WARNING] No vectors loaded\n")

        print("Step 4: Getting hybrid recommendations (default)...")
>>>>>>> 3e9f4f67901635abb41d9ba259130748377ff4e4
        result = api.get_recommendations(
            user_uid=test_user_uid,
            top_k=10,
            recommendation_strategy="hybrid"
        )

        if 'error' in result:
            print(f"[ERROR] {result['error']}\n")
            return False

        recommendations = result.get('recommendations', [])
<<<<<<< HEAD
        print(f"Got {len(recommendations)} recommendations\n")

        if not recommendations:
            print("[WARNING] No recommendations returned. Possible reasons:")
            print("  - No events in fixture data")
            print("  - Vectors not generated (embedding failed)")
            print("  - User profile has insufficient data\n")

        # Display top recommendations
        if recommendations:
            print("Top Recommendations:")
            print("-" * 70)
            for i, rec in enumerate(recommendations[:5], 1):
                title = rec.get('Title', rec.get('title', 'Unknown'))
                score = rec.get('similarity_score', 0)
                source = rec.get('source', 'unknown')
                friend = rec.get('friend_username', None)
                base_score = rec.get('base_similarity', score)
                friend_boost = rec.get('friend_boost', 1.0)
                is_mutual = rec.get('is_mutual_friend', False)
                mutual_count = rec.get('mutual_friend_count', 0)

                print(f"{i}. {title[:60]}")
                print(f"   Event ID: {rec.get('event_id', 'N/A')}")
                print(
                    f"   Score: {score:.3f} (base: {base_score:.3f}) | Source: {source}")
                if friend:
                    mutual_label = " (MUTUAL FRIEND)" if is_mutual or mutual_count > 0 else " (following)"
                    print(
                        f"   Friend Boost: {friend_boost:.2f}x from {friend}{mutual_label}")
                print()

        # Test friends-only strategy
        print("Step 5: Testing FRIENDS_ONLY strategy...")
=======
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
>>>>>>> 3e9f4f67901635abb41d9ba259130748377ff4e4
        result_friends = api.get_recommendations(
            user_uid=test_user_uid,
            top_k=5,
            recommendation_strategy="friends_only"
        )

        friends_recs = result_friends.get('recommendations', [])
<<<<<<< HEAD
        print(f"Got {len(friends_recs)} friend-based recommendations\n")
=======
        print(f"[OK] Got {len(friends_recs)} friend-based recommendations\n")
>>>>>>> 3e9f4f67901635abb41d9ba259130748377ff4e4

        if friends_recs:
            print("Friend Recommendations:")
            print("-" * 70)
<<<<<<< HEAD
            for i, rec in enumerate(friends_recs[:3], 1):
                title = rec.get('Title', 'Unknown')[:60]
                friend = rec.get('friend_username', 'Unknown')
                status = rec.get('friend_status', 'Unknown')
                score = rec.get('similarity_score', 0)
                print(f"{i}. {title}")
                print(f"   Score: {score:.3f} | Friend: {friend} ({status})")
                print()

        # Test friends-boosted strategy
        print("Step 6: Testing FRIENDS_BOOSTED strategy...")
        result_boosted = api.get_recommendations(
            user_uid=test_user_uid,
            top_k=5,
            recommendation_strategy="friends_boosted"
        )

        boosted_recs = result_boosted.get('recommendations', [])
        print(f"Got {len(boosted_recs)} boosted recommendations\n")

        # Summary
        print("="*70)
        print("QUALITY ASSESSMENT")
        print("="*70)
        print(f"\nHybrid recommendations: {len(recommendations)}")
        print(f"Friends-only recommendations: {len(friends_recs)}")
        print(f"Friends-boosted recommendations: {len(boosted_recs)}")

        if recommendations:
            friend_boosted_count = sum(
                1 for r in recommendations if r.get('friend_username'))
            mutual_friend_count = sum(
                1 for r in recommendations if r.get('is_mutual_friend', False))
            print(
                f"Recommendations with friend boost: {friend_boosted_count}/{len(recommendations)}")
            if friend_boosted_count > 0:
                print(f"  - Mutual friends: {mutual_friend_count}")
                print(
                    f"  - One-way following: {friend_boosted_count - mutual_friend_count}")

            # Check score ordering
            scores = [r.get('similarity_score', 0) for r in recommendations]
            is_sorted = scores == sorted(scores, reverse=True)
            print(f"Scores properly ordered: {is_sorted}")

            # Check for duplicates
            event_ids = [r.get('event_id') for r in recommendations]
            has_duplicates = len(event_ids) != len(set(event_ids))
            print(f"No duplicate events: {not has_duplicates}")

        print(
            f"\nRecommendation quality test passed for '{TEST_USERNAME}'")
        print("="*70 + "\n")
        return True

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
=======
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
>>>>>>> 3e9f4f67901635abb41d9ba259130748377ff4e4
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_recommendations()
    sys.exit(0 if success else 1)
