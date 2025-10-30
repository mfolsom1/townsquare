import types
import importlib.util
import logging
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
# Ensure package root (parent of ml/) is on sys.path so `import ml` works
sys.path.insert(0, os.path.dirname(ROOT))

logging.basicConfig(level=logging.INFO)


def _load_ml_submodules(root_path: str):
    """
    Load ml submodules (utils and mock_dbc) directly from files into sys.modules
    Avoids executing package __init__ to prevent heavy side-effects at import time
    """
    import sys

    # Ensure a package entry exists for 'ml' so relative imports work
    if 'ml' not in sys.modules:
        pkg = types.ModuleType('ml')
        pkg.__path__ = [root_path]
        sys.modules['ml'] = pkg

    # Helper to load a module file as ml.<name>
    def _load(name):
        file_path = os.path.join(root_path, f"{name}.py")
        spec = importlib.util.spec_from_file_location(f"ml.{name}", file_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[f"ml.{name}"] = mod
        spec.loader.exec_module(mod)
        return mod

    # Make sure test mode is enabled for lightweight fallbacks
    os.environ['ML_TEST_MODE'] = os.environ.get('ML_TEST_MODE', '1')

    utils_mod = _load('utils')
    mock_dbc_mod = _load('mock_dbc')
    return utils_mod, mock_dbc_mod


def apply_test_patches():
    """Replace utils.DatabaseConnector with the mock and ensure lightweight components."""
    utils, mock_dbc = _load_ml_submodules(ROOT)

    # Replace DB connector with mock implementation
    utils.DatabaseConnector = mock_dbc.MockDatabaseConnector
    # Expose for test runtime
    return utils, mock_dbc


def run_tests():
    utils, mock_dbc = apply_test_patches()

    print("Starting mock tests...")

    # Now import trainer and recommendation engine AFTER patching utils
    from ml.train import ModelTrainer
    from ml.recommend import RecommendationEngine, RecommendationAPI

    # Simple training run (generate event embeddings only)
    # Create one shared MockDatabaseConnector and inject it into both the trainer and the engine
    shared_db = mock_dbc.MockDatabaseConnector(test_user_id="user_001")
    trainer = ModelTrainer(
        storage_path="ml/model_artifacts_test", db_connector=shared_db)
    success = trainer.generate_event_embeddings()
    print(f"Event embeddings generation: {'PASS' if success else 'FAIL'}")

    # Load recommendation engine and get recs for the mock user
    engine = RecommendationEngine(
        load_vectors_on_init=False, db_connector=shared_db)

    # Ensure vector store loads vectors saved by trainer
    engine.vector_store = utils.VectorStore(storage_path="ml/vector_store")
    engine.load_vectors()

    # Use the API layer to produce recommendations
    api = RecommendationAPI(engine=engine)
    resp = api.get_recommendations("user_001", top_k=5)
    recs = resp.get('recommendations', [])
    print(f"Recommendations returned: {len(recs)}")

    # VISUALIZATION: Print small bits of info for the test account
    def print_user_summary(db: object, user_id: str):
        user = db.fetch_user(user_id)
        rsvps = db.fetch_user_rsvps(user_id)
        activities = db.fetch_user_activity(user_id)
        friends = db.fetch_user_friends(user_id)

        print("\n=== Test User Summary ===")
        if user:
            print(f"User ID: {user.get('FirebaseUID')}")
            print(f"Username: {user.get('Username')}")
            print(f"Interests: {', '.join(user.get('Interests', []))}")
            print(f"Location: {user.get('Location', '')}")
        else:
            print("User: <not found>")

        print("\nRecent RSVPs:")
        for r in rsvps[:5]:
            print(
                f"  - Event {r.get('EventID')} | Status: {r.get('Status')} | CreatedAt: {r.get('CreatedAt')}")

        print("\nRecent Activities:")
        for a in activities[:5]:
            print(
                f"  - {a.get('ActivityType')} -> Target {a.get('TargetID')} @ {a.get('CreatedAt')}")

        print("\nFriends (top):")
        for f in friends[:5]:
            print(f"  - {f.get('Username') or f.get('FirebaseUID')}")

    def print_recommendations_table(recommendations: list, engine_obj: object, strategy_used: str = None):
        # Show final score and approximate split into content vs friend contributions
        if not recommendations:
            print("\n=== Recommendations (top k) ===")
            print("  <no recommendations>")
            return []
        # Print which strategy produced these recommendations when available
        strategy_note = f" (strategy: {strategy_used})" if strategy_used else ""
        breakdowns = []
        # Print header for the consolidated table
        print(f"\n=== Recommendations (top k){strategy_note} ===")
        print(f"{'Rank':>4} | {'EventID':>7} | {'Final':>6} | {'Content-Based':>13} | {'Friend-Based':>12} | {'Source':>12} | {'Title'}")
        print('-' * 100)

        for idx, rec in enumerate(recommendations[:20], start=1):
            event_id = rec.get('event_id') or rec.get(
                'EventID') or rec.get('eventId')
            final = float(rec.get('similarity_score', 0.0) or 0.0)
            source = rec.get('source', '')
            friend_boost = rec.get('friend_boost')

            # Set title
            title = rec.get('Title') or ''
            if not title and hasattr(engine_obj, 'get_event_details'):
                details = engine_obj.get_event_details(event_id)
                title = details.get('Title') if details else ''

            # Attribution logic (approximate)
            if source in ('friend_based', 'friend_primary'):
                content_comp = 0.0
                friend_comp = final
            else:
                if friend_boost:
                    try:
                        content_comp = final / float(friend_boost)
                    except Exception:
                        content_comp = final
                    friend_comp = max(0.0, final - content_comp)
                else:
                    content_comp = final
                    friend_comp = 0.0

            breakdowns.append({
                'event_id': event_id,
                'title': title,
                'final_score': final,
                'content_score': content_comp,
                'friend_score': friend_comp,
                'source': source,
            })

            print(
                f"{idx:4} | {str(event_id):>7} | {final:6.3f} | {content_comp:7.3f} | {friend_comp:6.3f} | {source:12} | {title[:60]}")

        return breakdowns

    # Show test account summary and recommendations table
    print_user_summary(engine.db_connector, "user_001")
    breakdowns = print_recommendations_table(
        recs, engine, strategy_used=resp.get('strategy_used'))

    # API test
    # Reuse the API response from the single API call above to avoid a second
    # recommendation generation run.
    print(f"API response keys: {list(resp.keys())}")

    # Simple assertions (not using unittest to keep lightweight)
    all_pass = True
    if not success:
        all_pass = False
    if not isinstance(recs, list):
        all_pass = False
    if resp.get("count", 0) == 0:
        all_pass = False

    print("\nFinal result: {}".format(
        "ALL TESTS PASS" if all_pass else "SOME TESTS FAILED"))


if __name__ == "__main__":
    run_tests()
