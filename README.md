# Townsquare

Web application with React frontend, Flask API, TensorFlow recommendations, and PostgreSQL database.

## Development Setup

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 12+
- Firebase account (for authentication)

### 1. Backend Setup (CMD):
cd server

### *Create and activate virtual environment*
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

### *Install dependencies*
pip install -r requirements.txt

### *Set up environment variables*
cp .env.example .env

Edit .env with your:
 - DATABASE_URL=postgresql://user:password@localhost:5432/townsquare
 - JWT_SECRET_KEY=your_random_string
 - FIREBASE_API_KEY=your_config

### Initialize DB
flask db upgrade
flask run

### 2. Frontend Setup (different CMD):
cd ../client

### *Install dependencies*
npm install

### *Configure Firebase*
cp .env.local.example .env.local

Add your Firebase config:
 - REACT_APP_FIREBASE_API_KEY=your_key
 - REACT_APP_AUTH_DOMAIN=your-project.firebaseapp.com

### *Start development server*
npm start

### 3. DB Setup
### 4. Model Setup
