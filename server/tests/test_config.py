"""
Unit tests for the Config class
"""
import os
from unittest.mock import patch
from app.config import Config

class TestConfig:
    def test_config_loads_environment_variables(self):
        """Test that Config loads environment variables correctly"""
        with patch.dict(os.environ, {
            'DB_SERVER': 'test-server.database.windows.net',
            'DB_DATABASE': 'test-database',
            'DB_USERNAME': 'test-username',
            'DB_PASSWORD': 'test-password',
            'GOOGLE_APPLICATION_CREDENTIALS': '/path/to/firebase-key.json'
        }):
            config = Config()

            assert config.AZURE_SQL_SERVER == 'test-server.database.windows.net'
            assert config.AZURE_SQL_DATABASE == 'test-database'
            assert config.AZURE_SQL_USERNAME == 'test-username'
            assert config.AZURE_SQL_PASSWORD == 'test-password'
            assert config.FIREBASE_SERVICE_ACCOUNT_KEY == '/path/to/firebase-key.json'

    def test_azure_sql_connection_string(self):
        """Test that the Azure SQL connection string is formatted correctly"""
        with patch.dict(os.environ, {
            'DB_SERVER': 'test-server.database.windows.net',
            'DB_DATABASE': 'test-database',
            'DB_USERNAME': 'test-username',
            'DB_PASSWORD': 'test-password'
        }):
            config = Config()
            connection_string = config.azure_sql_connection_string

            assert 'DRIVER={ODBC Driver 18 for SQL Server}' in connection_string
            assert 'SERVER=test-server.database.windows.net' in connection_string
            assert 'DATABASE=test-database' in connection_string
            assert 'UID=test-username' in connection_string
            assert 'PWD=test-password' in connection_string
    
    def test_config_handles_missing_environment_variables(self):
        """Test that Config handles missing environment variables gracefully"""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            
            assert config.AZURE_SQL_SERVER is None
            assert config.AZURE_SQL_DATABASE is None
            assert config.AZURE_SQL_USERNAME is None
            assert config.AZURE_SQL_PASSWORD is None
            assert config.FIREBASE_SERVICE_ACCOUNT_KEY is None
    
    def test_connection_string_with_none_values(self):
        """Test connection string construction with None values"""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            connection_string = config.azure_sql_connection_string
            
            # Should handle None values gracefully
            assert 'SERVER=None' in connection_string
            assert 'DATABASE=None' in connection_string
            assert 'UID=None' in connection_string
            assert 'PWD=None' in connection_string