# __init__.py: utilities and classes used by ML package
__version__ = "0.1.0"
__author__ = "Townsquare Team"

from .recommend import RecommendationEngine, RecommendationAPI
from .train import ModelTrainer
from .utils import (
    DatabaseConnector,
    EmbeddingGenerator,
    VectorStore,
    TextPreprocessor,
    DataValidator,
    get_interaction_weight,
)

# Expose mock DB for easier testing
try:
    from .mock_dbc import MockDatabaseConnector
except Exception:
    MockDatabaseConnector = None

__all__ = [
    "RecommendationEngine",
    "RecommendationAPI",
    "ModelTrainer",
    "DatabaseConnector",
    "EmbeddingGenerator",
    "VectorStore",
    "TextPreprocessor",
    "DataValidator",
    "get_interaction_weight",
    "MockDatabaseConnector",
]
