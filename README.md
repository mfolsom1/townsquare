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
6. **Set up an ODBC Data Source for the Azure SQL Server:**
   - Open **ODBC Data Sources (64-bit)** on your machine.
   - Go to the **System DSN** tab and click **Add**.
   - Choose **ODBC Driver 18 for SQL Server**, then click **Finish**.
   - In the setup window:
     - **Name:** `TownSquareDB`
     - **Server:** `townsquare.database.windows.net`
     - **Authentication:** SQL Server Authentication
     - **Login ID:** `townsquare_admin`
     - **Password:** provided by Aaron
   - Click **Next**, then select **Change the default database to:** `townsquare`
   - Continue through the prompts and click **Test Data Source**, it should report “Tests completed successfully.”
7. **Set up Firebase Admin credentials:**
    - In your `.env`, set:
      ```
      GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/firebase-service-account.json
      ```
    - To get this JSON file, look in the Discord or message Aaron.

---

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
    .\.venv\Scripts\activate   # Windows
    source .venv/bin/activate  # Linux/Mac

*Install dependencies*

    pip install -r requirements.txt

*Set up environment variables*

    cp ../.env.example ../.env

*Edit .env with your:*

    DB_SERVER=townsquare.database.windows.net
    DB_DATABASE=townsquare
    DB_USERNAME=townsquare_admin
    DB_PASSWORD=password_from_aaron
    GOOGLE_APPLICATION_CREDENTIALS=json_from_aaron

*Start the Flask server*

    cd ..
    python -m server.app

Or for hot reloading during development:

    cd server
    flask run


### 2. Frontend Setup (different CMD):

    cd client

*Install dependencies*

    npm install

*Start development server*

    npm start

The React app runs on port 3000 and proxies API requests to Flask on port 5000.


