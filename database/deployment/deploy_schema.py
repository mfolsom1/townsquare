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
        conn = pyodbc.connect(CONN_STR)
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION;")
        version = cursor.fetchone()[0]
        print(f"✅ Connected successfully!")
        print(f"   SQL Server version: {version.split(' - ')[0]}")
        conn.close()
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
    
    # Drop order to handle foreign key constraints
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
    """Parse SQL file into individual statements, handling multi-line statements properly"""
    # Remove SQL comments but preserve the structure
    lines = []
    for line in sql_content.split('\n'):
        # Remove comments but keep the line structure
        if '--' in line:
            line = line[:line.index('--')]
        line = line.rstrip()
        if line:  # Keep non-empty lines
            lines.append(line)
    
    # Rejoin with spaces, preserving line breaks where needed
    sql_content = '\n'.join(lines)
    
    # Split by semicolon, but be careful with quoted strings and brackets
    statements = []
    current_statement = ""
    in_single_quotes = False
    in_double_quotes = False
    paren_depth = 0
    
    i = 0
    while i < len(sql_content):
        char = sql_content[i]
        
        # Handle quotes
        if char == "'" and not in_double_quotes:
            if i == 0 or sql_content[i-1] != '\\':
                in_single_quotes = not in_single_quotes
        elif char == '"' and not in_single_quotes:
            if i == 0 or sql_content[i-1] != '\\':
                in_double_quotes = not in_double_quotes
        
        # Handle parentheses depth
        if not in_single_quotes and not in_double_quotes:
            if char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
        
        # Split on semicolon only when not in quotes and at root level
        if char == ';' and not in_single_quotes and not in_double_quotes and paren_depth == 0:
            if current_statement.strip():
                statements.append(current_statement.strip())
            current_statement = ""
        else:
            current_statement += char
        
        i += 1
    
    # Add the last statement if it doesn't end with semicolon
    if current_statement.strip():
        statements.append(current_statement.strip())
    
    # Filter out empty statements
    return [stmt for stmt in statements if stmt.strip()]

def deploy_schema(conn, force_recreate=False, auto_confirm=False):
    """Deploy the schema from schema.sql file"""
    schema_file = Path(__file__).parent.parent / 'schema.sql'
    
    if not schema_file.exists():
        print(f"❌ Schema file not found: {schema_file}")
        return False
    
    print(f"🔄 Reading schema from: {schema_file}")
    
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
    except Exception as e:
        print(f"❌ Error reading schema file: {e}")
        return False
    
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
            if force_recreate:
                print("⚠️  --force flag detected, but confirmation still required for safety.")
            
            print("\nTo proceed, you must explicitly confirm this destructive action.")
            response = input("Type 'DELETE ALL TABLES' to confirm (or anything else to cancel): ")
            if response != 'DELETE ALL TABLES':
                print("❌ Deployment cancelled - tables were not deleted")
                print("💡 To deploy safely, either:")
                print("   • Manually drop tables first, or")
                print("   • Use a fresh database, or") 
                print("   • Run with --yes flag for automated deployment")
                return False
        else:
            print("🤖 Auto-confirmation enabled (--yes flag), proceeding with table deletion...")
        
        force_recreate = True
    
    if force_recreate and existing_tables:
        drop_existing_schema(conn, existing_tables)
    
    # Parse and execute SQL statements
    statements = parse_sql_statements(sql_content)
    print(f"🔄 Executing {len(statements)} SQL statements...")
    
    cursor = conn.cursor()
    
    for i, statement in enumerate(statements, 1):
        try:
            # Show progress for table creation
            if statement.upper().startswith('CREATE TABLE'):
                table_name = re.search(r'CREATE TABLE\s+(\w+)', statement, re.IGNORECASE)
                if table_name:
                    print(f"   [{i}/{len(statements)}] Creating table: {table_name.group(1)}")
            elif statement.upper().startswith('CREATE INDEX'):
                index_name = re.search(r'CREATE.*INDEX\s+(\w+)', statement, re.IGNORECASE)
                if index_name:
                    print(f"   [{i}/{len(statements)}] Creating index: {index_name.group(1)}")
            else:
                print(f"   [{i}/{len(statements)}] Executing statement...")
            
            cursor.execute(statement)
            conn.commit()
            
        except Exception as e:
            print(f"❌ Error executing statement {i}: {e}")
            print(f"   Statement: {statement[:100]}...")
            conn.rollback()
            return False
    
    print("✅ Schema deployed successfully!")
    return True

def verify_deployment(conn):
    """Verify that all tables were created successfully"""
    print("🔄 Verifying deployment...")
    
    expected_tables = [
        'Users', 'EventCategories', 'Events', 'EventTags', 
        'EventTagAssignments', 'Interests', 'UserInterests', 
        'SocialConnections', 'RSVPs', 'UserActivity'
    ]
    
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        AND TABLE_SCHEMA = 'dbo'
        ORDER BY TABLE_NAME
    """)
    
    created_tables = [row[0] for row in cursor.fetchall()]
    
    print(f"📋 Created tables ({len(created_tables)}):")
    for table in created_tables:
        status = "✅" if table in expected_tables else "⚠️"
        print(f"   {status} {table}")
    
    # Check for missing tables
    missing_tables = [table for table in expected_tables if table not in created_tables]
    if missing_tables:
        print(f"\n❌ Missing tables:")
        for table in missing_tables:
            print(f"   - {table}")
        return False
    
    # Check indexes
    cursor.execute("""
        SELECT COUNT(*) 
        FROM sys.indexes 
        WHERE object_id IN (
            SELECT object_id 
            FROM sys.tables 
            WHERE schema_id = SCHEMA_ID('dbo')
        )
        AND type > 0  -- Exclude heaps
    """)
    
    index_count = cursor.fetchone()[0]
    print(f"📊 Created indexes: {index_count}")
    
    print("✅ Deployment verification completed successfully!")
    return True

def perform_safety_check(conn, force_recreate, auto_confirm):
    """Perform initial safety check and warn about potential data loss"""
    existing_tables = check_existing_tables(conn)
    
    if existing_tables:
        print("\n" + "🛑" * 20)
        print("🚨 SAFETY WARNING: DATABASE NOT EMPTY")
        print("🛑" * 20)
        print(f"This database contains {len(existing_tables)} existing tables:")
        for table in sorted(existing_tables):
            print(f"   • {table}")
        
        if not force_recreate:
            print("\n❌ DEPLOYMENT BLOCKED FOR SAFETY")
            print("   The database is not empty. To proceed, you must use the --force flag.")
            print("   This ensures you explicitly acknowledge that existing data will be lost.")
            print("\n💡 Options:")
            print("   • Use '--force' flag to allow table recreation (will prompt for confirmation)")
            print("   • Use '--force --yes' for automated deployment (DANGEROUS)")
            print("   • Use a different/empty database")
            print("   • Manually drop existing tables first")
            return False
        
        print(f"\n⚠️  --force flag detected: Deployment will DELETE all {len(existing_tables)} tables!")
        if not auto_confirm:
            print("   You will be prompted for confirmation before any changes are made.")
        else:
            print("   🤖 --yes flag detected: NO CONFIRMATION PROMPTS (automated mode)")
    else:
        print("\n✅ Database is empty - safe to deploy schema")
    
    return True

def main():
    """Main deployment function"""
    print("🚀 TownSquare Database Schema Deployment")
    print("=" * 50)
    
    # Parse command line arguments
    force_recreate = '--force' in sys.argv or '-f' in sys.argv
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv
    
    if '--help' in sys.argv or '-h' in sys.argv:
        print_help()
        return
    
    # Show usage information
    if force_recreate or auto_confirm:
        print("🔧 Command line flags detected:")
        if force_recreate:
            print("   --force: Will recreate existing tables (with confirmation)")
        if auto_confirm:
            print("   --yes: Will skip confirmation prompts (DANGEROUS)")
        print()
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Test connection
    if not test_connection():
        sys.exit(1)
    
    # Perform safety check
    try:
        conn = pyodbc.connect(CONN_STR)
        
        if not perform_safety_check(conn, force_recreate, auto_confirm):
            sys.exit(1)
        
        if deploy_schema(conn, force_recreate, auto_confirm):
            verify_deployment(conn)
            print("\n🎉 Schema deployment completed successfully!")
        else:
            print("\n❌ Schema deployment failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

def print_help():
    """Print help information"""
    print("""
TownSquare Database Schema Deployment Script

USAGE:
    python deploy_schema.py [OPTIONS]

OPTIONS:
    -h, --help     Show this help message
    -f, --force    Allow recreation of existing tables (requires confirmation)
    -y, --yes      Auto-confirm destructive actions (DANGEROUS - use only in CI/CD)

EXAMPLES:
    python deploy_schema.py                    # Safe deployment, prompts before any changes
    python deploy_schema.py --force            # Allow table recreation with manual confirmation  
    python deploy_schema.py --force --yes      # Automated deployment (CI/CD use only)

SAFETY FEATURES:
    • Script will refuse to run if tables exist (unless --force is used)
    • Requires explicit typed confirmation before deleting existing tables
    • --yes flag bypasses confirmations (use only in automated environments)
    • Each database operation commits immediately with rollback on errors

⚠️  WARNING: This script will permanently delete existing tables and data!
    Always backup your database before running this script on production data.
    """)

if __name__ == "__main__":
    main()
