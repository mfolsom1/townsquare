import pyodbc
from dotenv import load_dotenv
import os

# Load variables from .env
load_dotenv()

server = os.getenv("DB_SERVER")
database = os.getenv("DB_DATABASE")
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")

# Connection string
conn_str = (
    f'DRIVER={{ODBC Driver 18 for SQL Server}};'
    f'SERVER={server};DATABASE={database};'
    f'UID={username};PWD={password};'
    'Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
)

# Connect to the database
try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION;")
    row = cursor.fetchone()
    print("Connected! SQL Server version:", row[0])
    
    # Fetch and print all tables
    print("\nTables in the database:")
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME;")
    tables = cursor.fetchall()
    
    if tables:
        for table in tables:
            print(f"  - {table[0]}")
    else:
        print("  No tables found in the database.")
        
    conn.close()
    
except Exception as e:
    print("Connection failed:", e)
