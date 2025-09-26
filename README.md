## Onboarding & Environment Setup

1. **Send Aaron your IP address and wait until you are added to the Azure SQL whitelist.**
2. **Pull the latest changes in your repo.**
3. **In the `server` directory, activate your virtual environment and install the new requirements:**
    ```bash
    cd server
    source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows
    pip install -r requirements.txt
    ```
4. **Go into the `.env.example` file and copy the relevant section into your `.env`:**
    - Set `DB_USERNAME=townsquare_admin`
    - Set `DB_PASSWORD` to the value provided by Aaron 
5. **Install the ODBC Driver 18 for SQL Server:**
    - [Download and install instructions (Microsoft Docs)](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server?view=sql-server-ver17)
6. **Set up Firebase Admin credentials:**
    - In your `.env`, set:
      ```
      GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/firebase-service-account.json
      ```
    - To get this JSON file, look in the Discord or message Aaron.



# Townsquare
Web application with a React frontend, Flask API, TensorFlow-based recommendations, Firebase Authentication, and Azure SQL Database.

## Development Setup


### Prerequisites
- Python 3.9+
- Node.js 16+
- Azure SQL Database (or local SQL Server for dev)
- Firebase account (for authentication)


### 1. Backend Setup (CMD):

    cd server

*Create and activate virtual environment*

    python -m venv .venv
    source .venv/bin/activate  # Linux/Mac
    .\.venv\Scripts\activate   # Windows

*Install dependencies*

    pip install -r requirements.txt

*Set up environment variables*

    cp ../.env.example ../.env

*Edit .env with your:*

    AZURE_SQL_SERVER=yourserver.database.windows.net
    AZURE_SQL_DATABASE=your_db_name
    AZURE_SQL_USERNAME=your_admin_user
    AZURE_SQL_PASSWORD=your_password
    JWT_SECRET_KEY=your_jwt_secret
    GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/firebase-adminsdk.json

*Start the Flask server*

    flask run --host=0.0.0.0 --port=5000


### 2. Frontend Setup (different CMD):

    cd ../client

*Install dependencies*

    npm install


*Start development server*

    npm start

*Proxy setup:*
Ensure your `package.json` in `client/` has:

    "proxy": "http://localhost:5000"

This allows API calls from React to Flask during development.


