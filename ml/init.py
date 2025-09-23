# init.py: Imports for ML functions
"""Townsquare ML Module"""

__version__ = "0.1.0"
__author__ = "Townsquare Team"

from .recommend import RecommendationEngine, RecommendationAPI
from .train import ModelTrainer
from .utils import DatabaseConnector, EmbeddingGenerator

__all__ = [
    'RecommendationEngine',
    'RecommendationAPI', 
    'ModelTrainer',
    'DatabaseConnector',
    'EmbeddingGenerator'
]