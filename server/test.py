from sqlalchemy import create_engine

engine = create_engine(
    'mssql+pyodbc://townsquare_admin:goGators123@@townsquare.database.windows.net/townsquare?driver=ODBC+Driver+18+for+SQL+Server'
)

try:
    with engine.connect() as connection:
        result = connection.execute("SELECT @@VERSION;")
        print("Connected! SQL Server version:", result.fetchone()[0])
except Exception as e:
    print("Connection failed:", e)