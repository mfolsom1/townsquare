# init.py: Imports for ML functions
"""Townsquare ML Module"""

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
]
