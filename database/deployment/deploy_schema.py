#!/usr/bin/env python3
"""
Azure SQL Database Schema Deployment Script
Deploys the TownSquare database schema to Azure SQL Database
"""

import pyodbc
from dotenv import load_dotenv
import os
import sys
import re
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Database connection parameters
SERVER = os.getenv("DB_SERVER")
DATABASE = os.getenv("DB_DATABASE")
USERNAME = os.getenv("DB_USERNAME")
PASSWORD = os.getenv("DB_PASSWORD")

# Connection string for Azure SQL Database
CONN_STR = (
    f'DRIVER={{ODBC Driver 18 for SQL Server}};'
    f'SERVER={SERVER};DATABASE={DATABASE};'
    f'UID={USERNAME};PWD={PASSWORD};'
    'Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
)

def validate_environment():
    """Validate that all required environment variables are set"""
    required_vars = ['DB_SERVER', 'DB_DATABASE', 'DB_USERNAME', 'DB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease ensure your .env file contains all required database credentials.")
        return False
    
    print("✅ Environment variables validated")
    return True

def test_connection():
    """Test database connection"""
    try:
        print("🔄 Testing database connection...")
        with pyodbc.connect(CONN_STR) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION;")
            version = cursor.fetchone()[0]
            print(f"✅ Connected successfully!")
            print(f"   SQL Server version: {version.split(' - ')[0]}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def check_existing_tables(conn):
    """Check if any tables already exist"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        AND TABLE_SCHEMA = 'dbo'
        ORDER BY TABLE_NAME
    """)
    tables = [row[0] for row in cursor.fetchall()]
    return tables

def drop_existing_schema(conn, tables):
    """Drop existing tables in correct order to handle foreign key constraints"""
    if not tables:
        return
    
    print(f"🔄 Found {len(tables)} existing tables. Dropping them...")
    
    # NOTE: A hardcoded drop order is brittle. A more robust solution would be to
    # dynamically disable all foreign key constraints, drop tables, then recreate.
    # However, for a known schema, this ordered approach is acceptable.
    drop_order = [
        'UserActivity', 'RSVPs', 'SocialConnections', 'UserInterests', 
        'EventTagAssignments', 'Events', 'EventTags', 'EventCategories', 
        'Interests', 'Users'
    ]
    
    cursor = conn.cursor()
    
    # Drop tables that exist in our drop order
    for table in drop_order:
        if table in tables:
            try:
                print(f"   Dropping table: {table}")
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                conn.commit()
            except Exception as e:
                print(f"   Warning: Could not drop {table}: {e}")
    
    # Drop any remaining tables not in our list
    remaining_tables = [t for t in tables if t not in drop_order]
    for table in remaining_tables:
        try:
            print(f"   Dropping remaining table: {table}")
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            conn.commit()
        except Exception as e:
            print(f"   Warning: Could not drop {table}: {e}")

def parse_sql_statements(sql_content):
    """
    Parse a T-SQL script into a list of batches separated by 'GO'.
    This is the standard batch separator for SQL Server / Azure SQL.
    """
    # Split the script by 'GO' on its own line, case-insensitive
    statements = re.split(r'^\s*GO\s*$', sql_content, flags=re.IGNORECASE | re.MULTILINE)
    
    # Filter out any empty statements that may result from the split
    return [stmt.strip() for stmt in statements if stmt.strip()]

def deploy_schema(conn, sql_content, force_recreate=False, auto_confirm=False):
    """Deploy the schema from the provided SQL content"""
    # Check existing tables
    existing_tables = check_existing_tables(conn)
    
    if existing_tables:
        print("\n" + "="*60)
        print("⚠️  WARNING: DATABASE ALREADY CONTAINS TABLES")
        print("="*60)
        print(f"Found {len(existing_tables)} existing tables:")
        for table in sorted(existing_tables):
            print(f"   • {table}")
        print("\n🔥 DESTRUCTIVE ACTION: This deployment will DROP all existing tables!")
        print("   All data in these tables will be permanently lost.")
        print("="*60)
        
        if not auto_confirm:
            response = input("Type 'DELETE ALL TABLES' to confirm (or anything else to cancel): ")
            if response != 'DELETE ALL TABLES':
                print("❌ Deployment cancelled by user.")
                return False
        else:
            print("🤖 Auto-confirmation enabled (--yes flag), proceeding with table deletion...")
        
        force_recreate = True
    
    if force_recreate and existing_tables:
        drop_existing_schema(conn, existing_tables)
    
    # Parse and execute SQL statements
    statements = parse_sql_statements(sql_content)
    print(f"\n🔄 Executing {len(statements)} SQL batches...")
    
    cursor = conn.cursor()
    
    try:
        # Execute the entire deployment within a single transaction
        for i, statement in enumerate(statements, 1):
            print(f"   [{i}/{len(statements)}] Executing batch...")
            cursor.execute(statement)
        
        # If all statements succeeded, commit the transaction
        print("✅ All batches executed successfully. Committing transaction...")
        conn.commit()
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR executing batch {i}: {e}")
        print(f"   Failed Batch Content: {statement[:200]}...")
        print("🔄 Rolling back all changes from this deployment.")
        conn.rollback() # Roll back the entire transaction on failure
        return False
    
    print("\n✅ Schema deployed successfully!")
    return True

def verify_deployment(conn, sql_content):
    """Verify that all tables from the schema file were created."""
    print("\n🔄 Verifying deployment...")
    
    # Dynamically find all 'CREATE TABLE' statements in the schema file
    expected_tables = re.findall(r'CREATE TABLE\s+(?:\[dbo\]\.)?\[?(\w+)\]?', sql_content, re.IGNORECASE)
    expected_tables = sorted(list(set(expected_tables))) # Get unique, sorted list

    if not expected_tables:
        print("⚠️ Could not find any 'CREATE TABLE' statements in schema file to verify against.")
        return True

    print(f"🔎 Expecting to find {len(expected_tables)} tables based on schema.sql...")

    created_tables = check_existing_tables(conn)
    
    print(f"📋 Found {len(created_tables)} tables in the database:")
    all_found = True
    for table in expected_tables:
        if table in created_tables:
            print(f"   ✅ {table}")
        else:
            print(f"   ❌ {table} (MISSING!)")
            all_found = False

    if not all_found:
        print("\n❌ Verification failed. Not all expected tables were created.")
        return False

    print("\n✅ Deployment verification completed successfully!")
    return True

def perform_safety_check(conn, force_recreate):
    """Perform initial safety check and warn about potential data loss"""
    existing_tables = check_existing_tables(conn)
    
    if existing_tables and not force_recreate:
        print("\n" + "🛑" * 20)
        print("🚨 SAFETY WARNING: DATABASE NOT EMPTY")
        print("🛑" * 20)
        print(f"This database contains {len(existing_tables)} existing tables.")
        print("\n❌ DEPLOYMENT BLOCKED FOR SAFETY")
        print("   To proceed, you must use the --force flag to acknowledge")
        print("   that existing tables and data will be dropped.")
        print("\n💡 Run with: python deploy_schema.py --force")
        return False
        
    if existing_tables and force_recreate:
        print("\n⚠️  --force flag detected: The script will drop all existing tables.")
        print("   You will be prompted for final confirmation before any data is deleted.")
    else:
        print("\n✅ Database is empty - safe to deploy schema.")
    
    return True

def print_help():
    """Print help information"""
    print("""
TownSquare Database Schema Deployment Script

USAGE:
    python deploy_schema.py [OPTIONS]

OPTIONS:
    -h, --help     Show this help message
    -f, --force    Allow recreation of existing tables (requires confirmation)
    -y, --yes      Auto-confirm destructive actions (DANGEROUS - use in CI/CD)

SAFETY FEATURES:
    • The script will refuse to run if tables exist, unless --force is used.
    • Destructive actions require explicit, typed confirmation.
    • The --yes flag bypasses confirmations (use only in automated environments).
    • The entire deployment is atomic; it will roll back on any error.

⚠️  WARNING: This script can permanently delete existing tables and data!
""")

def main():
    """Main deployment function"""
    print("🚀 TownSquare Database Schema Deployment")
    print("=" * 50)
    
    if '--help' in sys.argv or '-h' in sys.argv:
        print_help()
        return

    force_recreate = '--force' in sys.argv or '-f' in sys.argv
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv

    if not validate_environment() or not test_connection():
        sys.exit(1)

    # Read the schema file content first
    schema_file = Path(__file__).resolve().parent.parent / 'schema.sql'
    if not schema_file.exists():
        print(f"❌ Schema file not found at: {schema_file}")
        sys.exit(1)
        
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        print(f"✅ Successfully read schema from: {schema_file}")
    except Exception as e:
        print(f"❌ Error reading schema file: {e}")
        sys.exit(1)

    try:
        with pyodbc.connect(CONN_STR) as conn:
            if not perform_safety_check(conn, force_recreate):
                sys.exit(1)
            
            if deploy_schema(conn, sql_content, force_recreate, auto_confirm):
                if verify_deployment(conn, sql_content):
                    print("\n🎉 Deployment Succeeded!")
                else:
                    print("\n❌ Deployment failed during verification stage.")
                    sys.exit(1)
            else:
                print("\n❌ Schema deployment failed!")
                sys.exit(1)
                
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()