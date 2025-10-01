# database.py: Database connection verification for existing Azure SQL schema
import pyodbc
from .config import Config

def init_database():
    """Verify connection to existing Azure SQL database"""
    config = Config()
    try:
        conn = pyodbc.connect(config.azure_sql_connection_string)
        cursor = conn.cursor()
        
        # Just verify we can connect and the Users table exists
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Users'")
        table_exists = cursor.fetchone()[0] > 0
        
        if table_exists:
            print("✅ Successfully connected to Azure SQL Database")
            print("✅ Users table found - schema is compatible")
        else:
            print("⚠️  Connected to Azure SQL but Users table not found")
            print("Please ensure your schema.sql has been deployed to the database")
        
        conn.close()
    except Exception as e:
        print(f"❌ Error connecting to Azure SQL Database: {e}")
        print("Please check your connection string and database credentials")
        raise e