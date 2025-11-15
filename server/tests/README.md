# Running Tests

## Setup

Ensure you have pytest installed:
```bash
pip install pytest pytest-mock
```

## Run All Tests

From the server directory (important for correct path resolution):
```bash
cd server
python -m pytest tests/ -v
```

Or from project root:
```bash
python -m pytest server/tests/ -v
```

## Run Specific Test Files

From the server directory:
```bash
cd server

# Authentication tests
python -m pytest tests/test_auth_utils.py -v

# Database models tests
python -m pytest tests/test_models.py -v

# API routes tests
python -m pytest tests/test_routes.py -v

# Event archiving tests
python -m pytest tests/test_archiving.py -v

# User type permissions tests
python -m pytest tests/test_user.py -v

# ML recommendation system tests
python -m pytest tests/test_ml.py -v
```

## Run Specific Test Classes or Functions

From the server directory:
```bash
cd server

# Run a specific test class
python -m pytest tests/test_archiving.py::TestEventArchiving -v

# Run a specific test function
python -m pytest tests/test_routes.py::test_home_route -v
```

## Test Coverage

Generate coverage report (from server directory):
```bash
cd server
python -m pytest tests/ --cov=app --cov-report=html
```

View coverage report in browser:
```bash
open htmlcov/index.html  # Mac/Linux
start htmlcov/index.html  # Windows
```

## ML-Specific Testing

### Unit Tests with Mock Data
From the server directory:
```bash
cd server
# Use ML_TEST_MODE=1 to run with fixture data (no database required)
set ML_TEST_MODE=1  # Windows CMD
$env:ML_TEST_MODE=1  # Windows PowerShell
export ML_TEST_MODE=1  # Linux/Mac

python -m pytest tests/test_ml.py -v
```

### Test Recommendations for Specific User
From the server directory:
```bash
cd server

# Run as pytest test with output
python -m pytest tests/test_recommendations.py -s

# Or run directly
python tests/test_recommendations.py
```

Edit `TEST_USERNAME` variable in `tests/test_recommendations.py` to test different users (default: 'test_user15'). This script tests the full recommendation pipeline with real user data and displays detailed results.

## Test Organization

- `test_auth_utils.py` - Authentication decorator tests
- `test_models.py` - Database model CRUD operations
- `test_routes.py` - API endpoint integration tests
- `test_archiving.py` - Event archiving system tests
- `test_user.py` - User type permissions and hybrid model tests
- `test_ml.py` - ML recommendation engine unit tests
- `test_recommendations.py` - End-to-end recommendation testing for specific users

## Notes

- Tests must be run using `python -m pytest` from the server directory for correct module path resolution
- All tests use mocks and don't require a live database connection
- Firebase authentication is mocked in tests
- Organization user permissions are tested in `test_routes.py` and `test_user.py`
- ML tests can run in test mode with fixtures or against production database
- If you get import errors, make sure you're running from the server directory with `python -m pytest`
