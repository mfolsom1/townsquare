# Machine Learning Recommendation System

## Overview

Hybrid recommendation engine combining content-based filtering (sentence embeddings), collaborative filtering (similar users), and social signals (friend activity) to provide personalized event recommendations.

**Location**: `ml/recommend.py`, `ml/train.py`, `ml/utils.py`

**User Type Support**: The recommendation system supports both individual and organization user types equally. Organization users can receive personalized recommendations, RSVP to events, follow other users, and have their event creation activity influence recommendations just like individual users. The system treats both user types identically for recommendation purposes.

## Architecture

The system generates recommendations through a multi-stage pipeline:
1. Generate user vector from interests and historical interactions
2. Search event vectors for content similarity
3. Apply social signal boosts based on friend activity
4. Filter and score results
5. Return top-K recommendations

Recommendations adapt based on user activity, with new users receiving interest-based suggestions and active users receiving personalized recommendations from their interaction history.

## Core Components

### RecommendationEngine
**Location**: `ml/recommend.py`

Main orchestrator for generating personalized recommendations. Supports three strategies:
- **Hybrid** (default): Content-based with moderate friend influence
- **Friends Only**: Pure social recommendations from friend activity
- **Friends Boosted**: Content-based with strong friend influence

Key methods handle user vector generation, content search, friend boost application, and recency weighting.

### User Vector Generation
User embeddings are created from either interest profiles (new users) or weighted averages of recent interactions (active users). Recent activity within the last 30 days is prioritized with different weights for various interaction types (Going, Interested, Viewed).

### Social Signal Boosting
Friend activity enhances recommendation scores based on how many friends are attending events. The boost multiplier scales with friend count and is strategy-dependent.

### Recency Weighting
Events happening in the near future (0-7 days) receive score boosts to prioritize immediate opportunities.

### ModelTrainer
**Location**: `ml/train.py`

Handles the complete training pipeline for generating and updating recommendation models:

**Event Embeddings**: Fetches future events, preprocesses text (title, description, category, tags), generates 384-dimension embeddings, and stores vectors with metadata.

**User Embeddings**: Creates user profile text from interests, bio, and location, generates vectors for personalization.

**Collaborative Filtering**: Computes user-user similarity matrix for collaborative recommendations.

**Evaluation**: Assesses event coverage, user coverage, and embedding quality, storing metrics for monitoring.

All artifacts saved to `ml/model_artifacts/` directory. Vector embeddings are stored in the centralized `ml/vector_store/` directory at the project root (single source of truth shared between training and server).

### Utility Classes
**Location**: `ml/utils.py`

**EmbeddingGenerator**: Uses sentence-transformers (all-MiniLM-L6-v2 model) to generate 384-dimension embeddings. Supports GPU acceleration and provides fallback dummy embeddings for testing.

**VectorStore**: Manages vector storage in Numpy arrays with JSON metadata. Handles vector similarity search using cosine similarity and validates data integrity with checksums.

**DatabaseConnector**: Abstracts all ML-related database queries. Supports test mode with fixture-based mock data for development without database dependencies.

**TextPreprocessor**: Cleans and normalizes text for embedding generation. Combines multiple event/user fields into unified text representations.

## Recommendation Strategies

**Hybrid** (Default): Balances content similarity with social signals using moderate friend boost multipliers.

**Friends Only**: Pure social discovery showing only events with friend activity.

**Friends Boosted**: Emphasizes social influence with stronger friend boost multipliers while maintaining content relevance.

## Interaction Weights

User interactions are weighted differently when generating user vectors. Stronger signals (Going, created events) receive higher weights than weaker signals (viewed, friend interested). These weights are defined in the recommendation engine and can be tuned based on system performance.

## Training Process

### When to Retrain
Retrain weekly or when more than 10% of events have changed. Training updates all embeddings and collaborative filtering models.

### Training Command
Execute `python train.py` from the `ml/` directory. Duration: 5-15 minutes for 1000+ events depending on hardware.

### Output Artifacts
Training produces vector files (events_vectors.npy), metadata files (JSON), version tracking, and evaluation metrics. Vector embeddings are stored in the centralized `ml/vector_store/` directory at the project root. Model artifacts and metrics are stored in `ml/model_artifacts/` directory.

## Configuration

### Environment Variables
- `ML_EMBEDDING_DEVICE`: Set to 'cpu' or 'cuda' for GPU acceleration
- `ML_TEST_MODE`: Enable mock database for testing (1) or use production database (0)
- `ML_EMBEDDING_STRICT`: Fail-fast mode for debugging embedding generation
- `ML_DUMMY_EMBED_DIM`: Dimension for test embeddings when not using real models

### Training Configuration
Training parameters control minimum event counts, embedding dimensions, similarity thresholds, and retraining frequency. These are defined in the training module and can be adjusted based on system scale and performance requirements.

## Testing

**Location**: `server/tests/test_ml.py`, `ml/mock_dbc.py`, `ml/fixtures/`, `test_recommendations.py`

### Test Mode
Set `ML_TEST_MODE=1` to use mock database connector with fixture data. This enables development and testing without database dependencies.

Run tests with: `pytest server/tests/test_ml.py -v`

### User-Specific Testing
**Location**: `test_recommendations.py`

Test recommendations for specific users:
```bash
python test_recommendations.py
```

Configure test user by editing `TEST_USERNAME` variable at top of file (default: 'test_user15'). The script:
1. Initializes recommendation engine
2. Looks up user by username
3. Displays user profile (interests, friends, RSVPs, activities)
4. Generates hybrid recommendations
5. Generates friends-only recommendations
6. Shows top results with scores and friend boosts

### Fixture Management
**Location**: `ml/scripts/export_fixture.py`

Export production data to fixture files for testing. Fixtures include events, users (with UserType and OrganizationName), RSVPs, and social connections in JSON format.

## API Integration

The recommendation engine is exposed via REST API endpoints:

**GET `/api/recommendations`** - Get personalized recommendations (requires authentication)
- Parameters:
  - `top_k` (optional, default 10): Number of recommendations (1-50)
  - `strategy` (optional, default 'hybrid'): Recommendation strategy ('hybrid', 'friends_only', 'friends_boosted')
- Response: Ranked event recommendations with similarity scores, friend boosts, and recommendation sources

**POST `/api/recommendations/refresh`** - Refresh recommendation models (requires authentication)
- Response: Confirmation of model refresh status

All recommendation endpoints require valid Firebase authentication token in Authorization header.

## File Structure

**Core Modules**: `ml/recommend.py`, `ml/train.py`, `ml/utils.py`  
**Testing**: `server/tests/test_ml.py`, `ml/mock_dbc.py`  
**Data Storage**: `ml/vector_store/` (centralized embeddings and metadata - single source of truth), `ml/model_artifacts/` (training outputs and metrics)  
**Fixtures**: `ml/fixtures/` (test data), `ml/scripts/` (utilities)

Note: The `ml/vector_store/` directory is the single authoritative location for all vector embeddings. Both training scripts and the server read/write to this location.

## Performance

### Embedding Generation
CPU processes ~100 events/second, GPU ~1000 events/second. Complete training for 1000 events takes 5-15 minutes.

### Recommendation Latency
Typical request latency ~200ms including user vector generation, content search, and friend boost queries.

### Optimization Strategies
- Cache user vectors with TTL
- Pre-compute recommendations for active users
- Use Redis for friend activity caching
- Add database indexes for RSVP and social connection queries

## Troubleshooting

### "No event vectors found"
Run training pipeline to generate initial embeddings: `python ml/train.py`

### "sentence-transformers not available"
Install required packages: `pip install sentence-transformers torch`. For testing without dependencies, use `ML_TEST_MODE=1`.

### "Database connections disabled in ML_TEST_MODE"
Set `ML_TEST_MODE=0` for production database connections, or continue using fixture-based testing.

### Generic/non-personalized recommendations
Verify user has interests or interaction history in database. Check vector files loaded correctly. Retrain if models older than 7 days.

### High recommendation latency
Add database indexes to RSVP and SocialConnections tables. Implement user vector caching with TTL. Apply filters to reduce search space.

### Corrupted vectors or metadata
Delete all files in `ml/vector_store/` directory and retrain from scratch.

## Key Metrics

### Quality Metrics
Monitor event coverage (% with embeddings), user coverage (% with personalized recommendations), click-through rates, and RSVP conversion rates to assess recommendation relevance.

### System Health
Track recommendation latency percentiles (p50, p95, p99), fallback rate to generic recommendations, vector store size, and training pipeline duration to ensure system performance.
