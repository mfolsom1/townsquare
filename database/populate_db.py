import pyodbc
from dotenv import load_dotenv
import os
from faker import Faker
import random
import uuid
from datetime import datetime, timedelta

# --- CONFIGURATION (MODIFIED) ---
# Numbers have been halved to reduce the amount of data
NUM_USERS = 25
NUM_EVENTS = 50
# These are now determined by the length of the Gainesville-specific lists below
NUM_INTERESTS = 10 
NUM_TAGS = 13
MAX_INTERESTS_PER_USER = 5
MAX_TAGS_PER_EVENT = 4
MAX_RSVPS_PER_EVENT = 20 # Halved
PERCENT_CONNECTIONS = 0.1 

# --- PREDEFINED GAINESVILLE DATA (MODIFIED) ---

# New Gainesville-themed event categories
EVENT_CATEGORIES = [
    {"Name": "Gator Sports", "Description": "Chomp chomp! Football, basketball, and all UF athletic events.", "Color": "#FA4616"},
    {"Name": "UF Campus Life", "Description": "Events happening on the University of Florida campus.", "Color": "#0021A5"},
    {"Name": "Local Music & Arts", "Description": "Concerts at local venues, art walks, and theater.", "Color": "#FFC300"},
    {"Name": "Outdoor & Nature", "Description": "Explore Gainesville's beautiful parks, prairies, and springs.", "Color": "#1A9956"},
    {"Name": "Food & Breweries", "Description": "From downtown food trucks to local craft breweries.", "Color": "#900C3F"},
    {"Name": "Community & Markets", "Description": "Farmers markets, volunteer meetups, and local festivals.", "Color": "#581845"},
    {"Name": "Tech & Innovation", "Description": "Meetups and workshops from Gainesville's growing tech scene.", "Color": "#2A6E99"},
]

# New list of real Gainesville venues for events
GAINESVILLE_VENUES = [
    "Ben Hill Griffin Stadium, 157 Gale Lemerand Dr, Gainesville, FL 32611",
    "Stephen C. O'Connell Center, 250 Gale Lemerand Dr, Gainesville, FL 32611",
    "Depot Park, 874 SE 4th St, Gainesville, FL 32601",
    "Paynes Prairie Preserve State Park, 100 Savannah Blvd, Micanopy, FL 32667",
    "Kanapaha Botanical Gardens, 4700 SW 58th Dr, Gainesville, FL 32608",
    "Florida Museum of Natural History, 3215 Hull Rd, Gainesville, FL 32611",
    "The Hippodrome Theatre, 25 SE 2nd Pl, Gainesville, FL 32601",
    "First Magnitude Brewing Company, 1220 SE Veitch St, Gainesville, FL 32601",
    "Swamp Head Brewery, 3650 SW 42nd Ave, Gainesville, FL 32608",
    "Bo Diddley Plaza, 111 E University Ave, Gainesville, FL 32601",
    "Heartwood Soundstage, 619 S Main St, Gainesville, FL 32601",
    "Celebration Pointe, Celebration Pointe Ave, Gainesville, FL 32608",
    "Cade Museum for Creativity and Invention, 811 S Main St, Gainesville, FL 32601",
    "Sweetwater Wetlands Park, 325 SW Williston Rd, Gainesville, FL 32601"
]

# New list of Gainesville-themed interests
GAINESVILLE_INTERESTS = [
    ("Gator Football", "Following the UF Gators football team."),
    ("Hiking", "Exploring local trails like those at Paynes Prairie or San Felasco."),
    ("Craft Beer", "Enjoying the local brewery scene like Swamp Head and First Magnitude."),
    ("Live Music", "Catching shows at venues like High Dive or Heartwood."),
    ("UF Basketball", "Supporting the Gators basketball team."),
    ("Art & Culture", "Visiting the Harn Museum or attending a show at the Hippodrome."),
    ("Gardening", "Interests in local flora, maybe visiting Kanapaha Gardens."),
    ("Startups", "Following the local tech and innovation scene."),
    ("Kayaking", "Paddling at Lake Wauburg or nearby springs."),
    ("Farmers Markets", "Shopping for local produce and goods.")
]

# New list of Gainesville-themed event tags
GAINESVILLE_TAGS = [
    "Free Food", "Family Friendly", "21+", "Outdoor", "UF Sponsored",
    "Dog Friendly", "Live Band", "Networking", "Student Discount", "Go Gators",
    "Downtown GNV", "Craft Fair"
]

# Gainesville-themed organizations
GAINESVILLE_ORGANIZATIONS = [
    ("UF Student Government", "The official student government representing all University of Florida students and advocating for student interests."),
    ("Gator Gaming Guild", "A community of UF students and locals passionate about board games, video games, and tabletop RPGs."),
    ("Gainesville Tech Meetup", "Monthly gatherings for developers, entrepreneurs, and tech enthusiasts in the Gainesville area."),
    ("Alachua Audubon Society", "Dedicated to conservation and appreciation of birds and their habitats in North Central Florida."),
    ("Downtown Gainesville Merchants", "Local business owners working together to promote and enhance the downtown Gainesville experience.")
]

# --- SCRIPT START ---

def clear_database(cursor):
    """
    Clears all data from the tables and resets IDENTITY columns for a clean slate.
    """
    print("🗑️  Clearing existing data from tables...")
    tables_to_clear = [
        "UserActivity", "RSVPs", "SocialConnections", "UserInterests",
        "EventTagAssignments", "UserOrgMemberships", "UserOrgFollows", "Events", "Users", "Interests", "EventTags",
        "EventCategories", "Organizations"
    ]
    tables_with_identity = [
        "Events", "Interests", "EventTags", "EventCategories", "Organizations"
    ]

    for table in tables_to_clear:
        try:
            cursor.execute(f"DELETE FROM {table}")
            print(f"  - Cleared {table}")

            if table in tables_with_identity:
                cursor.execute(f"DBCC CHECKIDENT ('{table}', RESEED, 0)")
                print(f"  - Reset IDENTITY for {table}")

        except pyodbc.ProgrammingError as e:
            print(f"  - Could not clear {table}: {e}")
    print("✅ All tables cleared and identities reset.\n")

def populate_data(conn, cursor):
    """Main function to orchestrate the data population."""
    fake = Faker()

    # --- HELPER FUNCTIONS (MODIFIED) ---
    def random_hex_color():
        return f"#{random.randint(0, 0xFFFFFF):06X}"

    def generate_gainesville_event_title():
        """Generates a plausible, themed event title."""
        activities = ["Live Music", "Gators Watch Party", "Yoga Session", "Farmers Market", "Art Walk", "Brewery Tour", "Tech Meetup", "Outdoor Movie Night", "Volunteer Day", "Food Truck Rally"]
        venues = ["at Depot Park", "at The High Dive", "at Ben Hill Griffin Stadium", "at Bo Diddley Plaza", "at First Magnitude", "at Celebration Pointe", "on UF Campus", "at Paynes Prairie"]
        return f"{random.choice(activities)} {random.choice(venues)}"
        
    try:
        clear_database(cursor)

        # 1. Populate tables with no dependencies
        print("🌱 Populating independent tables (Gainesville Themed)...")
        cursor.executemany(
            "INSERT INTO EventCategories (Name, Description, Color) VALUES (?, ?, ?)",
            [(cat['Name'], cat['Description'], cat['Color']) for cat in EVENT_CATEGORIES]
        )
        cursor.execute("SELECT CategoryID FROM EventCategories")
        category_ids = [row.CategoryID for row in cursor.fetchall()]
        print("  - Populated EventCategories")

        # Interests (MODIFIED)
        cursor.executemany("INSERT INTO Interests (Name, Description) VALUES (?, ?)", GAINESVILLE_INTERESTS)
        cursor.execute("SELECT InterestID FROM Interests")
        interest_ids = [row.InterestID for row in cursor.fetchall()]
        print("  - Populated Interests")
        
        # EventTags (MODIFIED)
        tags_data = [(name, f"Events related to {name} in Gainesville.", random_hex_color()) for name in GAINESVILLE_TAGS]
        cursor.executemany(
            "INSERT INTO EventTags (Name, Description, Color) VALUES (?, ?, ?)",
            tags_data
        )
        cursor.execute("SELECT TagID FROM EventTags")
        tag_ids = [row.TagID for row in cursor.fetchall()]
        print("  - Populated EventTags")
        
        # Organizations
        cursor.executemany("INSERT INTO Organizations (Name, Description) VALUES (?, ?)", GAINESVILLE_ORGANIZATIONS)
        cursor.execute("SELECT OrgID FROM Organizations")
        org_ids = [row.OrgID for row in cursor.fetchall()]
        print("  - Populated Organizations")
        print("✅ Independent tables populated.\n")

        # 2. Populate Users
        print("👤 Populating Users...")
        users_data = []
        for _ in range(NUM_USERS):
            first_name = fake.first_name()
            last_name = fake.last_name()
            users_data.append((
                str(uuid.uuid4()),
                f"{first_name.lower()}{last_name.lower()}{random.randint(10, 999)}",
                fake.unique.email(),
                first_name,
                last_name,
                f"Gainesville, FL {fake.zipcode_in_state(state_abbr='FL')}", # MODIFIED: Gainesville location
                fake.text(max_nb_chars=250)
            ))
        cursor.executemany(
            "INSERT INTO Users (FirebaseUID, Username, Email, FirstName, LastName, Location, Bio) VALUES (?, ?, ?, ?, ?, ?, ?)",
            users_data
        )
        cursor.execute("SELECT FirebaseUID FROM Users")
        user_uids = [row.FirebaseUID for row in cursor.fetchall()]
        print(f"✅ Populated {len(user_uids)} Users.\n")

        # 3. Populate Events
        print("🎉 Populating Events...")
        events_data = []
        for _ in range(NUM_EVENTS):
            start_time = fake.future_datetime(end_date="+60d")
            end_time = start_time + timedelta(hours=random.randint(1, 5))
            # Assign most events (80%) to an organization, leave 20% without org affiliation
            org_id = random.choice(org_ids) if random.random() < 0.8 else None
            events_data.append((
                random.choice(user_uids),
                generate_gainesville_event_title(), # MODIFIED: Themed title
                fake.text(max_nb_chars=800),
                start_time,
                end_time,
                random.choice(GAINESVILLE_VENUES), # MODIFIED: Themed location
                random.choice(category_ids),
                random.choice([None, 25, 50, 100]), # MODIFIED: Smaller capacities
                f"https://picsum.photos/seed/{uuid.uuid4()}/800/400",
                org_id
            ))
        cursor.executemany(
            "INSERT INTO Events (OrganizerUID, Title, Description, StartTime, EndTime, Location, CategoryID, MaxAttendees, ImageURL, OrgID) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            events_data
        )
        cursor.execute("SELECT EventID FROM Events")
        event_ids = [row.EventID for row in cursor.fetchall()]
        print(f"✅ Populated {len(event_ids)} Events.\n")

        # 4. Populate Many-to-Many join tables
        print("🔗 Populating relationship tables...")
        # UserInterests
        user_interests_data = set()
        for uid in user_uids:
            num_interests = random.randint(1, min(len(interest_ids), MAX_INTERESTS_PER_USER))
            for interest in random.sample(interest_ids, k=num_interests):
                 user_interests_data.add((uid, interest))
        cursor.executemany("INSERT INTO UserInterests (UserUID, InterestID) VALUES (?, ?)", list(user_interests_data))
        print(f"  - Populated {len(user_interests_data)} UserInterests")

        # EventTagAssignments
        event_tags_data = set()
        for eid in event_ids:
            num_tags = random.randint(1, min(len(tag_ids), MAX_TAGS_PER_EVENT))
            for tag in random.sample(tag_ids, k=num_tags):
                event_tags_data.add((eid, tag))
        cursor.executemany("INSERT INTO EventTagAssignments (EventID, TagID) VALUES (?, ?)", list(event_tags_data))
        print(f"  - Populated {len(event_tags_data)} EventTagAssignments")

        # SocialConnections
        connections_data = set()
        num_connections_to_create = int(NUM_USERS * (NUM_USERS - 1) * PERCENT_CONNECTIONS)
        if len(user_uids) > 1:
            while len(connections_data) < num_connections_to_create:
                follower, following = random.sample(user_uids, 2)
                connections_data.add((follower, following))
            cursor.executemany("INSERT INTO SocialConnections (FollowerUID, FollowingUID) VALUES (?, ?)", list(connections_data))
            print(f"  - Populated {len(connections_data)} SocialConnections")

        # RSVPs
        rsvps_data = set()
        for eid in event_ids:
            attendees = random.sample(user_uids, k=min(len(user_uids), random.randint(2, MAX_RSVPS_PER_EVENT)))
            for uid in attendees:
                status = random.choice(['Going', 'Going', 'Going', 'Interested', 'Not Going'])
                rsvps_data.add((uid, eid, status))
        cursor.executemany("INSERT INTO RSVPs (UserUID, EventID, Status) VALUES (?, ?, ?)", list(rsvps_data))
        print(f"  - Populated {len(rsvps_data)} RSVPs")

        # UserOrgMemberships - assign ALL users to at least one organization
        org_memberships_data = set()
        for uid in user_uids:
            # Each user joins 1-3 organizations
            num_orgs = random.randint(1, min(3, len(org_ids)))
            for org_id in random.sample(org_ids, k=num_orgs):
                org_memberships_data.add((uid, org_id))
        cursor.executemany("INSERT INTO UserOrgMemberships (UserUID, OrgID) VALUES (?, ?)", list(org_memberships_data))
        print(f"  - Populated {len(org_memberships_data)} UserOrgMemberships")
        
        # UserOrgFollows - some users also follow additional organizations beyond their memberships
        org_follows_data = set()
        # Get organizations each user is a member of
        user_member_orgs = {}
        for uid, org_id in org_memberships_data:
            if uid not in user_member_orgs:
                user_member_orgs[uid] = set()
            user_member_orgs[uid].add(org_id)
        
        # About a third of users follow additional organizations they're not members of
        users_to_follow = random.sample(user_uids, k=len(user_uids) // 3)
        for uid in users_to_follow:
            # Get organizations this user is NOT a member of
            available_orgs = [org_id for org_id in org_ids if org_id not in user_member_orgs.get(uid, set())]
            if available_orgs:
                # Follow 1-2 additional organizations
                num_follows = random.randint(1, min(2, len(available_orgs)))
                for org_id in random.sample(available_orgs, k=num_follows):
                    org_follows_data.add((uid, org_id))
        cursor.executemany("INSERT INTO UserOrgFollows (UserUID, OrgID) VALUES (?, ?)", list(org_follows_data))
        print(f"  - Populated {len(org_follows_data)} UserOrgFollows")
        print("✅ Relationship tables populated.\n")

        conn.commit()
        print("💾 Transaction committed successfully!")

    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        print(f"❌ Database Error Occurred: {sqlstate}")
        print(ex)
        print("Rolling back transaction...")
        conn.rollback()
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        print("Rolling back transaction...")
        conn.rollback()

def main():
    """Connects to the database and runs the population script."""
    load_dotenv()
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_DATABASE")
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")

    if not all([server, database, username, password]):
        print("Error: Missing one or more required environment variables.")
        exit(1)

    print("🚨" * 3 + " WARNING " + "🚨" * 3)
    print("This script will DELETE ALL DATA from the specified database tables.")
    print(f"Target Server:   {server}")
    print(f"Target Database: {database}")
    confirmation = input("To proceed, you must type 'YES' exactly as shown: ")

    if confirmation != 'YES':
        print("\n❌ Operation aborted by user. No changes were made to the database.")
        exit()
    
    print("\nUser confirmed. Proceeding with database population...\n")

    conn_str = (
        f'DRIVER={{ODBC Driver 18 for SQL Server}};'
        f'SERVER={server};DATABASE={database};'
        f'UID={username};PWD={password};'
        'Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
    )

    try:
        with pyodbc.connect(conn_str) as conn:
            print("🚀 Successfully connected to the database.")
            cursor = conn.cursor()
            populate_data(conn, cursor)
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    main()