# export_fixture.py: exports ML fixture for offline testing
"""
This script attempts to export events, users, RSVPs, activities and friends
from a live database using pyodbc when connection env vars are provided.
If pyodbc is not available or env vars are missing, it falls back to the
in-repo MockDatabaseConnector to produce a sample fixture.

The fixture is written to the following file by default: ml/fixtures/production_fixture.json

By default the exporter will sanitize (remove synthetic test events and redact obvious
PII-like fields). Use --no-sanitize only when you explicitly need unsanitized output
and understand the privacy risks.
Sanitization does not remove sensitive data.

"""
import os
import sys
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Allow running the script from repository anywhere
sys.path.insert(0, str(ROOT))

DEFAULT_OUT = ROOT / 'ml' / 'fixtures' / 'production_fixture.json'


def write_fixture(path, fixture):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf8') as fh:
        json.dump(fixture, fh, default=str, indent=2)
    print(f"Wrote fixture to: {path}")


def export_from_db(limit: int, driver_name: str = None):
    """Export data from production DB using pyodbc"""
    try:
        import pyodbc
    except Exception as e:
        raise RuntimeError("pyodbc not available")

    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_DATABASE')
    username = os.getenv('DB_USERNAME')
    password = os.getenv('DB_PASSWORD')
    if not all([server, database, username, password]):
        raise RuntimeError("Missing DB connection environment variables")

    # Allow an explicit full connection string via env (force DRIVER braces)
    env_conn = os.getenv('DB_CONN_STRING')
    if env_conn:
        conn_str = env_conn
    else:
        # Use provided driver name or default and wrap in braces
        drv = driver_name or 'ODBC Driver 18 for SQL Server'
        conn_str = (
            f"DRIVER={{{drv}}};"
            f"SERVER={server};DATABASE={database};UID={username};PWD={password};"
            "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        )
    # pyodbc.connect will raise if the connection string is malformed or the driver is not available
    conn = pyodbc.connect(conn_str)
    cur = conn.cursor()

    def fetch(q):
        cur.execute(q)
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return rows

    # Simple queries; adapt as needed
    events_q = f"SELECT TOP ({limit}) EventID, Title, Description, StartTime, EndTime, Location FROM Events ORDER BY StartTime DESC"
    users_q = f"SELECT TOP ({limit}) FirebaseUID, Username, Location, Bio FROM Users"
    rsvps_q = f"SELECT TOP ({limit}) RSVPID, UserUID, EventID, Status, CreatedAt FROM RSVPs ORDER BY CreatedAt DESC"
    activities_q = f"SELECT TOP ({limit}) ActivityID, UserUID, ActivityType, TargetID, Description, CreatedAt FROM UserActivity ORDER BY CreatedAt DESC"
    friends_q = f"SELECT TOP ({limit}) FollowerUID, FollowingUID, CreatedAt FROM SocialConnections"

    events = fetch(events_q)
    users = fetch(users_q)
    rsvps = fetch(rsvps_q)
    activities = fetch(activities_q)
    friends = fetch(friends_q)

    fixture = {
        'events': events,
        'users': users,
        'rsvps': rsvps,
        'activities': activities,
        'friends': friends,
    }
    return fixture


def export_from_mock(limit: int):
    """Produce a fixture by using the in-repo MockDatabaseConnector"""
    try:
        from ml.mock_dbc import MockDatabaseConnector
    except Exception:
        # Fallback: try importing as module path
        import importlib.util
        p = Path(__file__).resolve().parents[1] / 'mock_dbc.py'
        spec = importlib.util.spec_from_file_location('ml.mock_dbc', str(p))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        MockDatabaseConnector = mod.MockDatabaseConnector

    m = MockDatabaseConnector()
    fixture = {
        'events': m.data.get('events', []),
        'users': m.data.get('users', []),
        'rsvps': m.data.get('rsvps', []),
        'activities': m.data.get('activities', []),
        'friends': m.data.get('friends', []),
        'friend_recommendations': m.data.get('friend_recs', []),
    }
    return fixture


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--out', '-o', default=str(DEFAULT_OUT), help='Output fixture path')
    parser.add_argument('--limit', '-n', type=int,
                        default=500, help='Max rows per table')
    parser.add_argument('--prefer-db', action='store_true',
                        help='Prefer using live DB; fall back to mock if not available')
    parser.add_argument('--driver', default='ODBC Driver 18 for SQL Server',
                        help='ODBC driver name to use when building the connection string (wraps the name in { } automatically)')
    # Sanitize by default; provide --no-sanitize to explicitly disable
    parser.add_argument('--no-sanitize', dest='sanitize', action='store_false',
                        help='Do NOT sanitize the fixture before writing (dangerous; may include PII)')
    parser.set_defaults(sanitize=True)
    args = parser.parse_args()

    fixture = None
    if args.prefer_db:
        try:
            # Call export_from_db with the requested driver name to force a driver-based connection string
            fixture = export_from_db(args.limit, driver_name=args.driver)
            print("Exported fixture from live DB")
        except Exception as e:
            print(
                f"Could not export from DB: {e}; falling back to mock generator")

    if fixture is None:
        fixture = export_from_mock(args.limit)
        print("Exported fixture from in-repo mock data")

    # Optionally sanitize the fixture before writing (remove synthetic test events, redact emails/phones)
    if args.sanitize:
        print("Sanitizing fixture: removing synthetic test events and redacting PII-like fields")
        # Remove events with titles that look like synthetic test events

        def looks_like_test_event(ev):
            t = (ev.get('Title') or ev.get('title') or '')
            if isinstance(t, str) and 'test event' in t.lower():
                return True
            return False

        events = [e for e in fixture.get(
            'events', []) if not looks_like_test_event(e)]
        fixture['events'] = events

        # Redact email/phone-like keys from users and activities
        def redact_record(rec):
            for k in list(rec.keys()):
                if 'email' in k.lower() or 'phone' in k.lower():
                    rec[k] = None
            return rec

        fixture['users'] = [redact_record(dict(u))
                            for u in fixture.get('users', [])]
        fixture['activities'] = [redact_record(
            dict(a)) for a in fixture.get('activities', [])]

    write_fixture(args.out, fixture)


if __name__ == '__main__':
    main()
