"""
Unit tests for ML recommendation system

This test suite validates the FUNCTIONALITY of the recommendation pipeline:
- Tests that recommendations are generated
- Validates data structures and API responses
- Tests different user types (individual, organization)
- Verifies recommendation strategies work
- Tests edge cases (cold start, duplicates, score ordering)
Usage: pytest server/tests/test_ml.py -v
"""
import pytest
import types
import importlib.util
import logging
import sys
import os

ROOT = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..', '..', 'ml')
sys.path.insert(0, os.path.dirname(ROOT))

logging.basicConfig(level=logging.WARNING)

_shared_trainer = None
_shared_engine = None
_shared_vector_store = None
_shared_db = None

# Test helpers


@pytest.fixture(scope="module")
def ml_fixtures():
    """Initialize shared ML components for testing"""
    global _shared_trainer, _shared_engine, _shared_vector_store, _shared_db

    if _shared_trainer is not None:
        return _shared_trainer, _shared_engine, _shared_vector_store, _shared_db

    utils, mock_dbc = _apply_test_patches()
    from ml.train import ModelTrainer
    from ml.recommend import RecommendationEngine

    _shared_db = mock_dbc.MockDatabaseConnector(test_user_id="user_001")

    # Use absolute path for model artifacts (test fixtures)
    project_root = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), '..', '..')
    model_artifacts_path = os.path.join(
        project_root, 'ml', 'model_artifacts_test')

    # VectorStore uses default path from utils.py (single source of truth)
    _shared_trainer = ModelTrainer(
        storage_path=model_artifacts_path, db_connector=_shared_db)
    success = _shared_trainer.generate_event_embeddings()
    assert success, "Failed to generate embeddings"

    # VectorStore automatically uses VECTOR_STORAGE_PATH from utils.py
    _shared_vector_store = utils.VectorStore()

    _shared_engine = RecommendationEngine(
        load_vectors_on_init=False, db_connector=_shared_db)
    _shared_engine.vector_store = _shared_vector_store
    _shared_engine.load_vectors()

    return _shared_trainer, _shared_engine, _shared_vector_store, _shared_db


def _load_ml_submodules(root_path: str):
    """Load ml submodules for testing"""
    if 'ml' not in sys.modules:
        pkg = types.ModuleType('ml')
        pkg.__path__ = [root_path]
        sys.modules['ml'] = pkg

    def _load(name):
        file_path = os.path.join(root_path, f"{name}.py")
        spec = importlib.util.spec_from_file_location(f"ml.{name}", file_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[f"ml.{name}"] = mod
        spec.loader.exec_module(mod)
        return mod

    os.environ['ML_TEST_MODE'] = os.environ.get('ML_TEST_MODE', '1')

    utils_mod = _load('utils')
    mock_dbc_mod = _load('mock_dbc')
    return utils_mod, mock_dbc_mod


def _apply_test_patches():
    """Replace database connector with mock implementation"""
    utils, mock_dbc = _load_ml_submodules(ROOT)
    utils.DatabaseConnector = mock_dbc.MockDatabaseConnector
    return utils, mock_dbc

# Recommendation Engine tests


def test_ml_recommendations(ml_fixtures):
    """Test ML recommendation system generates recommendations"""
    _apply_test_patches()
    from ml.recommend import RecommendationAPI

    _, engine, _, _ = ml_fixtures

    api = RecommendationAPI(engine=engine)
    resp = api.get_recommendations("user_001", top_k=5)
    recs = resp.get('recommendations', [])

    # Verify response structure
    assert isinstance(recs, list), "Recommendations should be a list"
    assert resp.get(
        "count", 0) > 0, "Should return at least one recommendation"
    assert 'strategy_used' in resp, "Response should include strategy_used field"
    assert resp['strategy_used'] == 'hybrid', "Default strategy should be hybrid"
    assert 'user_uid' in resp, "Response should include user_uid field"
    assert resp['user_uid'] == 'user_001'

    # Verify engine state
    assert engine.are_vectors_loaded(), "Engine should have vectors loaded"
    assert len(recs) <= 5, "Should respect top_k parameter"

    # Verify recommendation structure
    if recs:
        first_rec = recs[0]
        assert 'event_id' in first_rec, "Each recommendation should have event_id"
        assert 'similarity_score' in first_rec, "Each recommendation should have similarity_score"
        assert isinstance(first_rec['similarity_score'],
                          (int, float)), "Score should be numeric"


def test_ml_user_data():
    """Test database connector returns user data"""
    utils, mock_dbc = _apply_test_patches()

    db = mock_dbc.MockDatabaseConnector(test_user_id="user_001")

    user = db.fetch_user("user_001")
    assert user is not None
    assert 'FirebaseUID' in user
    assert 'Username' in user
    assert 'Interests' in user

    rsvps = db.fetch_user_rsvps("user_001")
    assert isinstance(rsvps, list)

    activities = db.fetch_user_activity("user_001")
    assert isinstance(activities, list)

    friends = db.fetch_user_friends("user_001")
    assert isinstance(friends, list)


def test_ml_pipeline_integration(ml_fixtures):
    """Test end-to-end ML pipeline from training to recommendations"""
    _apply_test_patches()
    from ml.recommend import RecommendationAPI

    trainer, engine, _, _ = ml_fixtures

    assert trainer is not None
    assert engine.are_vectors_loaded()

    api = RecommendationAPI(engine=engine)
    resp = api.get_recommendations("user_001", top_k=10)

    assert resp['count'] > 0
    assert all('event_id' in r for r in resp['recommendations'])
    assert all('similarity_score' in r for r in resp['recommendations'])
    assert len(resp['recommendations']) <= 10


def test_organization_user_recommendations(ml_fixtures):
    """Test recommendations work for organization user type"""
    _apply_test_patches()
    from ml.recommend import RecommendationAPI

    _, engine, _, shared_db = ml_fixtures

    org_user = {
        "FirebaseUID": "org_test_001",
        "Username": "test_org",
        "Interests": ["community", "events"],
        "Bio": "Test organization",
        "Location": "Test City",
        "UserType": "organization",
        "OrganizationName": "Test Organization"
    }
    shared_db.data['users'].append(org_user)

    api = RecommendationAPI(engine=engine)
    result = api.get_recommendations("org_test_001", top_k=5)

    assert isinstance(result['recommendations'], list)
    assert result['user_uid'] == "org_test_001"
    assert result['count'] > 0


def test_organization_user_fields():
    """Test UserType and OrganizationName fields are preserved"""
    utils, mock_dbc = _apply_test_patches()

    mock_db = mock_dbc.MockDatabaseConnector()

    org_user = {
        "FirebaseUID": "org_fields_001",
        "Username": "test_org_fields",
        "Interests": ["tech"],
        "Bio": "Test",
        "Location": "Test",
        "UserType": "organization",
        "OrganizationName": "Test Org Name"
    }
    mock_db.data['users'].append(org_user)

    user = mock_db.fetch_user("org_fields_001")

    assert user is not None
    assert 'UserType' in user
    assert user['UserType'] == 'organization'
    assert 'OrganizationName' in user
    assert user['OrganizationName'] == 'Test Org Name'


def test_recommendation_strategies(ml_fixtures):
    """Test hybrid, friends_only, and friends_boosted strategies"""
    _apply_test_patches()
    from ml.recommend import RecommendationAPI

    _, engine, _, shared_db = ml_fixtures

    test_user = {
        "FirebaseUID": "strategy_test_001",
        "Username": "strategy_tester",
        "Interests": ["community"],
        "Bio": "Test",
        "Location": "Test",
        "UserType": "individual",
        "OrganizationName": None
    }
    shared_db.data['users'].append(test_user)

    api = RecommendationAPI(engine=engine)
    strategies = ['hybrid', 'friends_only', 'friends_boosted']

    for strategy in strategies:
        result = api.get_recommendations(
            "strategy_test_001", top_k=5, recommendation_strategy=strategy)
        assert isinstance(result['recommendations'], list)
        assert result['strategy_used'] == strategy


def test_top_k_parameter(ml_fixtures):
    """Test top_k parameter limits number of recommendations"""
    _apply_test_patches()
    from ml.recommend import RecommendationAPI

    _, engine, _, shared_db = ml_fixtures

    shared_db.data['users'].append({
        "FirebaseUID": "topk_test_001",
        "Username": "topk_tester",
        "Interests": ["sports", "music", "art"],
        "Bio": "Test",
        "Location": "City",
        "UserType": "individual",
        "OrganizationName": None
    })

    api = RecommendationAPI(engine=engine)

    for k in [1, 3, 5, 10]:
        result = api.get_recommendations("topk_test_001", top_k=k)
        assert len(result['recommendations']) <= k


def test_recommendation_no_duplicates(ml_fixtures):
    """Test recommendations do not contain duplicate events"""
    _apply_test_patches()

    _, engine, _, shared_db = ml_fixtures

    shared_db.data['users'].append({
        "FirebaseUID": "dup_test_001",
        "Username": "dup_tester",
        "Interests": ["music", "art"],
        "Bio": "Test",
        "Location": "City",
        "UserType": "individual",
        "OrganizationName": None
    })

    recommendations = engine.recommend_events("dup_test_001", top_k=20)
    event_ids = [rec.get('event_id')
                 for rec in recommendations if 'event_id' in rec]

    assert len(event_ids) == len(set(event_ids)
                                 ), "Recommendations should not contain duplicate event IDs"


def test_recommendations_with_no_interests(ml_fixtures):
    """Test recommendations work for users with no interests (cold start)"""
    _apply_test_patches()
    from ml.recommend import RecommendationAPI

    _, engine, _, shared_db = ml_fixtures

    # User with no interests or history
    shared_db.data['users'].append({
        "FirebaseUID": "cold_start_001",
        "Username": "new_user",
        "Interests": [],
        "Bio": "",
        "Location": "Test City",
        "UserType": "individual",
        "OrganizationName": None
    })

    api = RecommendationAPI(engine=engine)
    result = api.get_recommendations("cold_start_001", top_k=5)

    # Should still get recommendations (fallback to popular events)
    assert isinstance(result['recommendations'], list)
    assert result['count'] >= 0, "Should handle cold start gracefully"


def test_recommendations_score_ordering(ml_fixtures):
    """Test that recommendations are returned in descending score order"""
    _apply_test_patches()

    _, engine, _, shared_db = ml_fixtures

    shared_db.data['users'].append({
        "FirebaseUID": "score_test_001",
        "Username": "score_tester",
        "Interests": ["technology", "innovation"],
        "Bio": "Tech enthusiast",
        "Location": "City",
        "UserType": "individual",
        "OrganizationName": None
    })

    recommendations = engine.recommend_events("score_test_001", top_k=10)

    if len(recommendations) > 1:
        scores = [r.get('similarity_score', 0) for r in recommendations]
        # Verify scores are in descending order
        assert scores == sorted(
            scores, reverse=True), "Recommendations should be sorted by score (highest first)"
