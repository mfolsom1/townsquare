import pyodbc
from dotenv import load_dotenv
import os
from faker import Faker
import random
import uuid
from datetime import datetime, timedelta

# --- CONFIGURATION (MODIFIED) ---
NUM_USERS = 25
NUM_ORGANIZATIONS = 5
NUM_EVENTS = 50
NUM_INTERESTS = 10
NUM_TAGS = 13
MAX_INTERESTS_PER_USER = 5
MAX_TAGS_PER_EVENT = 4
MAX_RSVPS_PER_EVENT = 20
PERCENT_CONNECTIONS = 0.1

# --- PREDEFINED GAINESVILLE DATA (MODIFIED) ---

# New Gainesville-themed event categories
EVENT_CATEGORIES = [
    {"Name": "Gator Sports", "Description": "Chomp chomp! Football, basketball, and all UF athletic events.", "Color": "#FA4616"},
    {"Name": "UF Campus Life",
        "Description": "Events happening on the University of Florida campus.", "Color": "#0021A5"},
    {"Name": "Local Music & Arts",
        "Description": "Concerts at local venues, art walks, and theater.", "Color": "#FFC300"},
    {"Name": "Outdoor & Nature",
        "Description": "Explore Gainesville's beautiful parks, prairies, and springs.", "Color": "#1A9956"},
    {"Name": "Food & Breweries",
        "Description": "From downtown food trucks to local craft breweries.", "Color": "#900C3F"},
    {"Name": "Community & Markets",
        "Description": "Farmers markets, volunteer meetups, and local festivals.", "Color": "#581845"},
    {"Name": "Tech & Innovation",
        "Description": "Meetups and workshops from Gainesville's growing tech scene.", "Color": "#2A6E99"},
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
    "Downtown GNV", "Support Local", "Craft Fair"
]

GAINESVILLE_ORGANIZATIONS = [
    ("UF Student Government", "The official student government representing all University of Florida students and advocating for student interests."),
    ("Gator Gaming Guild", "A community of UF students and locals passionate about board games, video games, and tabletop RPGs."),
    ("Gainesville Tech Meetup",
     "Monthly gatherings for developers, entrepreneurs, and tech enthusiasts in the Gainesville area."),
    ("Alachua Audubon Society",
     "Dedicated to conservation and appreciation of birds and their habitats in North Central Florida."),
    ("Downtown Gainesville Merchants",
     "Local business owners working together to promote and enhance the downtown Gainesville experience.")
]

# --- SCRIPT START ---


def clear_database(cursor):
    """
    Clears all data from the tables and resets IDENTITY columns for a clean slate.
    """
    print("🗑️  Clearing existing data from tables...")
    tables_to_clear = [
        "UserActivity", "RSVPs", "SocialConnections", "UserInterests",
        "EventTagAssignments", "Events", "Users", "Interests", "EventTags",
        "EventCategories"
    ]
    tables_with_identity = [
        "Events", "Interests", "EventTags", "EventCategories"
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
        activities = ["Live Music", "Gators Watch Party", "Yoga Session", "Farmers Market", "Art Walk",
                      "Brewery Tour", "Tech Meetup", "Outdoor Movie Night", "Volunteer Day", "Food Truck Rally"]
        venues = ["at Depot Park", "at The High Dive", "at Ben Hill Griffin Stadium", "at Bo Diddley Plaza",
                  "at First Magnitude", "at Celebration Pointe", "on UF Campus", "at Paynes Prairie"]
        return f"{random.choice(activities)} {random.choice(venues)}"
    
    def generate_gainesville_event_description(title):
        """Generates realistic event descriptions based on the event title and type."""
        descriptions = {
            "Live Music": [
                "Join us for an evening of incredible live music featuring local and touring artists. Come early to grab the best seats and enjoy our full bar and food menu. This venue is known for its intimate atmosphere and excellent acoustics.",
                "Experience the vibrant Gainesville music scene with performances by talented local musicians. The night will feature a mix of genres including indie rock, folk, and electronic music. Don't miss this opportunity to discover your new favorite band.",
                "Local bands take the stage for a night of original music and creative energy. The lineup includes both emerging artists and established acts from the North Florida music community. Come support live music in Gainesville!"
            ],
            "Gators Watch Party": [
                "Cheer on the Florida Gators with fellow fans! We'll have the game on multiple big screens with surround sound, plus game day specials on food and drinks. Wear your orange and blue and let's go Gators!",
                "Join the Gator Nation for an exciting watch party! We'll have giveaways, trivia during halftime, and the best game day atmosphere in town. Free appetizers during the first quarter. In all kinds of weather, we're all together!",
                "Come watch the Gators dominate on the field while you enjoy great company, cold drinks, and game day favorites. This is the place to be for every UF fan. Kick-off specials and post-game celebrations included."
            ],
            "Yoga Session": [
                "Start your day with mindfulness and movement in this beginner-friendly yoga class. We'll focus on gentle stretches, breathing techniques, and relaxation. All levels welcome - mats and props provided.",
                "Join us for an outdoor yoga session surrounded by Gainesville's natural beauty. This vinyasa flow class will help you connect with nature while improving flexibility and strength. Bring water and a towel.",
                "Unwind from your week with this restorative yoga practice. We'll use props to support deep relaxation and gentle stretching. Perfect for stress relief and improving sleep quality. No experience necessary."
            ],
            "Farmers Market": [
                "Shop local and support area farmers and artisans! Find fresh produce, homemade goods, artisan crafts, and delicious prepared foods. Live music and activities for kids make this a perfect family outing.",
                "Discover the best of North Florida agriculture and craftsmanship at our weekly market. From organic vegetables to handmade soaps, locally roasted coffee to fresh flowers - you'll find unique treasures every week.",
                "Support sustainable agriculture and local businesses while enjoying the community atmosphere. Talk directly with farmers about their growing practices and get tips for preparing seasonal produce."
            ],
            "Art Walk": [
                "Explore Gainesville's thriving arts scene during our monthly art walk. Visit galleries, meet local artists, and enjoy live demonstrations. Many venues offer refreshments and special exhibition openings.",
                "Downtown comes alive with creativity! Stroll through participating galleries and studios, enjoy street performances, and discover emerging and established artists. Free and family-friendly event.",
                "Immerse yourself in local culture with this self-guided tour of Gainesville's art community. From traditional paintings to contemporary installations, there's something to inspire everyone."
            ],
            "Brewery Tour": [
                "Take a behind-the-scenes look at craft beer production and enjoy tastings of signature brews. Learn about the brewing process from grain to glass while sampling a variety of styles from IPAs to stouts.",
                "Discover the art and science of craft brewing with our guided tour. Meet the brewers, see the equipment in action, and taste fresh beer straight from the source. Tours include a souvenir glass.",
                "Join fellow beer enthusiasts for an educational and delicious experience. Learn about local ingredients, brewing techniques, and the history of craft beer in Gainesville. Designated driver options available."
            ],
            "Tech Meetup": [
                "Network with local developers, entrepreneurs, and tech enthusiasts. Tonight's presentation covers the latest trends in web development, followed by open networking and discussion. Pizza and drinks provided.",
                "Join Gainesville's growing tech community for presentations on emerging technologies, startup stories, and collaborative discussions. Whether you're a student, professional, or curious beginner, all are welcome.",
                "Connect with like-minded innovators and learn about the latest developments in technology. This month's focus is on artificial intelligence and its applications in local businesses."
            ],
            "Outdoor Movie Night": [
                "Bring blankets and chairs for a classic movie under the stars! We'll be screening a family-friendly film with free popcorn and concessions available for purchase. Gates open at sunset.",
                "Experience cinema in a whole new way with our outdoor screening. The movie starts at dusk, but come early to claim your spot and enjoy pre-show activities and live music.",
                "Pack a picnic and enjoy a beloved classic film in the great outdoors. This free community event includes activities for kids before the movie and food trucks on site."
            ],
            "Volunteer Day": [
                "Make a difference in the Gainesville community! Join us for a day of service including park cleanup, habitat restoration, and community garden maintenance. Tools and lunch provided.",
                "Give back to the community that gives us so much. Today's volunteer activities focus on environmental conservation and supporting local families in need. All ages and skill levels welcome.",
                "Be part of something bigger than yourself. We'll be working on projects that directly benefit Gainesville residents, from trail maintenance to food distribution. Come ready to work and make new friends."
            ],
            "Food Truck Rally": [
                "Taste the best mobile cuisine Gainesville has to offer! Over a dozen food trucks will be serving everything from gourmet tacos to artisan ice cream. Live music and seating areas provided.",
                "Satisfy your cravings with diverse food options from local culinary entrepreneurs. From BBQ to vegan options, fusion cuisines to comfort food classics - there's something for every palate.",
                "Enjoy a feast for all your senses with great food, live entertainment, and community atmosphere. Support local food businesses while discovering new flavors and meeting your neighbors."
            ]
        }
        
        # Extract the main activity from the title
        for activity in descriptions.keys():
            if activity in title:
                return random.choice(descriptions[activity])
        
        # Default description if no match found
        return "Join us for this exciting community event in Gainesville! Connect with neighbors, enjoy great activities, and experience what makes our city special. All are welcome to participate in this fun and engaging gathering."

    try:
        clear_database(cursor)

        # 1. Populate tables with no dependencies
        print("🌱 Populating independent tables (Gainesville Themed)...")
        cursor.executemany(
            "INSERT INTO EventCategories (Name, Description, Color) VALUES (?, ?, ?)",
            [(cat['Name'], cat['Description'], cat['Color'])
             for cat in EVENT_CATEGORIES]
        )
        cursor.execute("SELECT CategoryID FROM EventCategories")
        category_ids = [row.CategoryID for row in cursor.fetchall()]
        print("  - Populated EventCategories")

        # Interests (MODIFIED)
        cursor.executemany(
            "INSERT INTO Interests (Name, Description) VALUES (?, ?)", GAINESVILLE_INTERESTS)
        cursor.execute("SELECT InterestID FROM Interests")
        interest_ids = [row.InterestID for row in cursor.fetchall()]
        print("  - Populated Interests")

        # EventTags (MODIFIED)
        tags_data = [(name, f"Events related to {name} in Gainesville.", random_hex_color(
        )) for name in GAINESVILLE_TAGS]
        cursor.executemany(
            "INSERT INTO EventTags (Name, Description, Color) VALUES (?, ?, ?)",
            tags_data
        )
        cursor.execute("SELECT TagID FROM EventTags")
        tag_ids = [row.TagID for row in cursor.fetchall()]
        print("  - Populated EventTags")
        print("✅ Independent tables populated.\n")

        # 2. Populate Users with mix of individual and organization types
        # 2. Populate Users with mix of individual and organization types
        print("👤 Populating Users...")
        users_data = []

        # Create organization users first (one for each predefined organization)
        for idx, (org_name, org_desc) in enumerate(GAINESVILLE_ORGANIZATIONS):
            username = org_name.lower().replace(' ', '_')
            users_data.append((
                str(uuid.uuid4()),
                username,
                fake.unique.email(),
                org_name,
                None,
                f"Gainesville, FL {fake.zipcode_in_state(state_abbr='FL')}",
                org_desc,
                'organization',
                org_name
            ))

        # Create remaining users as individuals
        remaining_users = NUM_USERS - NUM_ORGANIZATIONS
        for _ in range(remaining_users):
            first_name = fake.first_name()
            last_name = fake.last_name()
            users_data.append((
                str(uuid.uuid4()),
                f"{first_name.lower()}{last_name.lower()}{random.randint(10, 999)}",
                fake.unique.email(),
                first_name,
                last_name,
                f"Gainesville, FL {fake.zipcode_in_state(state_abbr='FL')}",
                fake.text(max_nb_chars=250),
                'individual',
                None
            ))

        cursor.executemany(
            "INSERT INTO Users (FirebaseUID, Username, Email, FirstName, LastName, Location, Bio, UserType, OrganizationName) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            users_data
        )
        cursor.execute("SELECT FirebaseUID, UserType FROM Users")
        user_rows = cursor.fetchall()
        user_uids = [row.FirebaseUID for row in user_rows]
        org_user_uids = [
            row.FirebaseUID for row in user_rows if row.UserType == 'organization']
        print(
            f"✅ Populated {len(user_uids)} Users ({len(org_user_uids)} organizations, {len(user_uids) - len(org_user_uids)} individuals).\n")

        # 3. Populate Events (only organization users can create events)
        print("🎉 Populating Events...")
        events_data = []
        for _ in range(NUM_EVENTS):
            start_time = fake.future_datetime(end_date="+60d")
            end_time = start_time + timedelta(hours=random.randint(1, 5))
            title = generate_gainesville_event_title()
            description = generate_gainesville_event_description(title)
            events_data.append((
                random.choice(org_user_uids),
                title,
                description,
                start_time,
                end_time,
                random.choice(GAINESVILLE_VENUES),
                random.choice(category_ids),
                random.choice([None, 25, 50, 100]),
                f"https://picsum.photos/seed/{uuid.uuid4()}/800/400"
            ))
        cursor.executemany(
            "INSERT INTO Events (OrganizerUID, Title, Description, StartTime, EndTime, Location, CategoryID, MaxAttendees, ImageURL) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            events_data
        )
        cursor.execute("SELECT EventID FROM Events")
        event_ids = [row.EventID for row in cursor.fetchall()]
        print(
            f"✅ Populated {len(event_ids)} Events (all created by organization users).\n")

        # 4. Populate Many-to-Many join tables
        print("🔗 Populating relationship tables...")
        # UserInterests
        user_interests_data = set()
        for uid in user_uids:
            num_interests = random.randint(
                1, min(len(interest_ids), MAX_INTERESTS_PER_USER))
            for interest in random.sample(interest_ids, k=num_interests):
                user_interests_data.add((uid, interest))
        cursor.executemany(
            "INSERT INTO UserInterests (UserUID, InterestID) VALUES (?, ?)", list(user_interests_data))
        print(f"  - Populated {len(user_interests_data)} UserInterests")

        # EventTagAssignments
        event_tags_data = set()
        for eid in event_ids:
            num_tags = random.randint(1, min(len(tag_ids), MAX_TAGS_PER_EVENT))
            for tag in random.sample(tag_ids, k=num_tags):
                event_tags_data.add((eid, tag))
        cursor.executemany(
            "INSERT INTO EventTagAssignments (EventID, TagID) VALUES (?, ?)", list(event_tags_data))
        print(f"  - Populated {len(event_tags_data)} EventTagAssignments")

        # SocialConnections
        connections_data = set()
        num_connections_to_create = int(
            NUM_USERS * (NUM_USERS - 1) * PERCENT_CONNECTIONS)
        if len(user_uids) > 1:
            while len(connections_data) < num_connections_to_create:
                follower, following = random.sample(user_uids, 2)
                connections_data.add((follower, following))
            cursor.executemany(
                "INSERT INTO SocialConnections (FollowerUID, FollowingUID) VALUES (?, ?)", list(connections_data))
            print(f"  - Populated {len(connections_data)} SocialConnections")

        # RSVPs
        rsvps_data = set()
        for eid in event_ids:
            attendees = random.sample(user_uids, k=min(
                len(user_uids), random.randint(2, MAX_RSVPS_PER_EVENT)))
            for uid in attendees:
                status = random.choice(
                    ['Going', 'Going', 'Going', 'Interested', 'Not Going'])
                rsvps_data.add((uid, eid, status))
        cursor.executemany(
            "INSERT INTO RSVPs (UserUID, EventID, Status) VALUES (?, ?, ?)", list(rsvps_data))
        print(f"  - Populated {len(rsvps_data)} RSVPs")
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
