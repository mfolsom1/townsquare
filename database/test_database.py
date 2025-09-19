import pyodbc
from dotenv import load_dotenv
import os

# Load variables from .env
load_dotenv()

server = os.getenv("DB_SERVER")
database = os.getenv("DB_DATABASE")
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")

# Validate that all required environment variables are set
required_vars = {
    "DB_SERVER": server,
    "DB_DATABASE": database,
    "DB_USERNAME": username,
    "DB_PASSWORD": password
}

missing_vars = [var_name for var_name, var_value in required_vars.items() if not var_value]

if missing_vars:
    print("Error: Missing required environment variables:")
    for var in missing_vars:
        print(f"  - {var}")
    print("\nPlease ensure all required variables are set in your .env file.")
    exit(1)

# Validate that credentials are not set to default placeholder values
default_values = {
    "DB_USERNAME": "yourusername",
    "DB_PASSWORD": "yourpassword"
}

default_vars = [var_name for var_name, default_val in default_values.items() 
                if required_vars[var_name] == default_val]

if default_vars:
    print("Error: Database credentials are still set to default placeholder values:")
    for var in default_vars:
        print(f"  - {var} = '{default_values[var]}'")
    print("\nPlease update these values in your .env file with actual credentials.")
    exit(1)

print("All required environment variables are set and configured with proper values.")

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
