# config.py: Load env variables
# TODO: Setup configuration class for DB, JWT, etc.

import os
from dotenv import load_dotenv

load_dotenv()

DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_SERVER = os.getenv('DB_SERVER')
DB_DATABASE = os.getenv('DB_DATABASE')

print(f"DB_SERVER={os.getenv('DB_SERVER')}, DB_DATABASE={os.getenv('DB_DATABASE')}")

class Config:
    # Database configuration
    SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc://{DB_USERNAME}:{DB_PASSWORD}@{DB_SERVER}/{DB_DATABASE}?driver=ODBC+Driver+18+for+SQL+Server"
    SQLALCHEMY_TRACK_MODIFICATIONS = False