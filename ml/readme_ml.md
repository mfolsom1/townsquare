# Running ML tests that use the production DB

## Dependencies
- Create and activate a virtual environment before installing packages:
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install --upgrade pip
  ```

- Install sentence-transformers support and a compatible `torch` build (minimal install):
  ```powershell
  pip install sentence-transformers
  # Install torch according to https://pytorch.org/get-started/locally/ for your platform
  ```

If you choose *not* to download sentence-transformers or the torch, the code will fall back to a deterministic dummy embedding generator. To make missing/invalid model loads fail fast, set `ML_EMBEDDING_STRICT=1`.

 - For running the tests, the production connector uses the ODBC Driver 18 string. Ensure an appropriate ODBC driver for SQL Server is installed.
    ```powershell
    # For SQL Server ODBC Driver 18
    winget install -e --id Microsoft.ODBC.Driver.18
    ```
  - You will need `pyodbc` installed for real DB tests.
    ```powershell
    pip install pyodbc
    ```
## Running Tests

- In order to use the mock DB fixture:

  Enter the following commands (PowerShell):
  ```powershell
  $env:ML_TEST_MODE = '1'
  python .\ml\test_mock.py
  ```

- To test against a real database, ensure DB env variables are set and run without `ML_TEST_MODE`:
  ```powershell
  # Run the test file (will attempt real DB connections)
  python .\ml\test_mock.py
  ```
## Exporting a fixture of DB or mock data (optional)

The ml folder includes a small exporter script that snapshots events/users/RSVPs/activities/friends into a JSON fixture for offline testing. 

By default it writes to `ml/fixtures/production_fixture.json` and sanitizes the output (currently still includes sensitive data)

- Export using dev generated mock data:

    ```powershell
    # Export using mock data (default behavior)
    python .\ml\scripts\export_fixture.py
    ```
- **Export fixture of live DB**: 
    ```powershell
    # Requires DB env vars and pyodbc, passes driver name to the connection string
    python .\ml\scripts\export_fixture.py --prefer-db --driver "ODBC Driver 18 for SQL Server"
    ```

Note: The exporter sanitizes output by default (removes synthetic "Test Event" titles and redacts obvious email/phone-like fields). Use `--no-sanitize` to disable sanitization.