"""
Integration tests for database operations
"""
import pytest
from unittest.mock import Mock, patch
import pyodbc
from app.database import init_database

class TestDatabaseInit:
    """Test database initialization functionality"""
    
    @patch('pyodbc.connect')
    @patch('app.database.Config')
    def test_init_database_success_with_users_table(self, mock_config_class, mock_connect):
        """Test successful database initialization when Users table exists"""
        # Setup mocks
        mock_config = Mock()
        mock_config.azure_sql_connection_string = 'test-connection-string'
        mock_config_class.return_value = mock_config
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [1]  # Table exists
        
        # Capture print output
        with patch('builtins.print') as mock_print:
            init_database()
        
        # Verify database operations
        mock_connect.assert_called_once_with('test-connection-string')
        mock_cursor.execute.assert_called_once_with(
            "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Users'"
        )
        mock_conn.close.assert_called_once()
        
        # Verify success messages
        mock_print.assert_any_call("✅ Successfully connected to Azure SQL Database")
        mock_print.assert_any_call("✅ Users table found - schema is compatible")
    
    @patch('pyodbc.connect')
    @patch('app.database.Config')
    def test_init_database_success_without_users_table(self, mock_config_class, mock_connect):
        """Test database initialization when Users table doesn't exist"""
        # Setup mocks
        mock_config = Mock()
        mock_config.azure_sql_connection_string = 'test-connection-string'
        mock_config_class.return_value = mock_config
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [0]  # Table doesn't exist
        
        # Capture print output
        with patch('builtins.print') as mock_print:
            init_database()
        
        # Verify database operations
        mock_connect.assert_called_once_with('test-connection-string')
        mock_cursor.execute.assert_called_once_with(
            "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Users'"
        )
        mock_conn.close.assert_called_once()
        
        # Verify warning messages
        mock_print.assert_any_call("⚠️  Connected to Azure SQL but Users table not found")
        mock_print.assert_any_call("Please ensure your schema.sql has been deployed to the database")
    
    @patch('pyodbc.connect')
    @patch('app.database.Config')
    def test_init_database_connection_error(self, mock_config_class, mock_connect):
        """Test database initialization with connection error"""
        # Setup mocks
        mock_config = Mock()
        mock_config.azure_sql_connection_string = 'invalid-connection-string'
        mock_config_class.return_value = mock_config
        
        # Make connection raise an exception
        connection_error = Exception("Connection failed")
        mock_connect.side_effect = connection_error
        
        # Capture print output and test exception handling
        with patch('builtins.print') as mock_print:
            with pytest.raises(Exception) as exc_info:
                init_database()
        
        # Verify the exception is re-raised
        assert exc_info.value == connection_error
        
        # Verify error messages
        mock_print.assert_any_call("❌ Error connecting to Azure SQL Database: Connection failed")
        mock_print.assert_any_call("Please check your connection string and database credentials")
    
    @patch('pyodbc.connect')
    @patch('app.database.Config')
    def test_init_database_sql_error(self, mock_config_class, mock_connect):
        """Test database initialization with SQL execution error"""
        # Setup mocks
        mock_config = Mock()
        mock_config.azure_sql_connection_string = 'test-connection-string'
        mock_config_class.return_value = mock_config
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Make cursor execution raise an exception
        sql_error = Exception("SQL execution failed")
        mock_cursor.execute.side_effect = sql_error
        
        # Capture print output and test exception handling
        with patch('builtins.print') as mock_print:
            with pytest.raises(Exception) as exc_info:
                init_database()
        
        # Verify the exception is re-raised
        assert exc_info.value == sql_error
        
        # Verify error messages
        mock_print.assert_any_call("❌ Error connecting to Azure SQL Database: SQL execution failed")
        mock_print.assert_any_call("Please check your connection string and database credentials")