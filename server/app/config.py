
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        # Azure SQL Database configuration
        self.AZURE_SQL_SERVER = os.environ.get('DB_SERVER')
        self.AZURE_SQL_DATABASE = os.environ.get('DB_DATABASE')
        self.AZURE_SQL_USERNAME = os.environ.get('DB_USERNAME')
        self.AZURE_SQL_PASSWORD = os.environ.get('DB_PASSWORD')
        
        # Firebase configuration
        self.FIREBASE_SERVICE_ACCOUNT_KEY = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')

    
    # Connection string for Azure SQL
    @property
    def azure_sql_connection_string(self):
        return (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={self.AZURE_SQL_SERVER};"
            f"DATABASE={self.AZURE_SQL_DATABASE};"
            f"UID={self.AZURE_SQL_USERNAME};"
            f"PWD={self.AZURE_SQL_PASSWORD};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            "Connection Timeout=30;"
        )