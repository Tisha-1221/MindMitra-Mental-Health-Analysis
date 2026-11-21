
import sqlite3
import pandas as pd
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

CSV_PATH = PROJECT_ROOT / "data(Synthetic)" / "demo_wellness_data.csv"

DB_FOLDER = PROJECT_ROOT / "database(Synthetic)"
DB_FOLDER.mkdir(parents=True, exist_ok=True)

DB_PATH = DB_FOLDER / "mindmitra_demo.db"

# Check whether synthetic CSV exists
if not CSV_PATH.exists():
    raise FileNotFoundError(
        f"Synthetic CSV not found: {CSV_PATH}"
    )

# Read synthetic data
df = pd.read_csv(CSV_PATH)

# Convert sleep quality to numeric values
sleep_quality_map = {
    "Poor": 1,
    "Average": 2,
    "Good": 3
}

df["sleep_quality"] = df["sleep_quality"].map(
    sleep_quality_map
)

# Create a completely separate database
conn = sqlite3.connect(DB_PATH)

conn.execute("PRAGMA foreign_keys = ON")

# Create users table
conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
""")

# Create checkins table
conn.execute("""
    CREATE TABLE IF NOT EXISTS checkins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        feeling_text TEXT,
        positive_text TEXT,
        sleep_hours INTEGER,
        sleep_quality INTEGER,
        mood_score INTEGER,
        stress_score INTEGER,
        energy_score INTEGER,
        socializing INTEGER,
        anxiety_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        screen_time REAL,
        physically_active TEXT,
        social_media_hours REAL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")

# Create demo user accounts
user_mapping = {}

users = df[["user_id", "name"]].drop_duplicates()

for _, user in users.iterrows():

    demo_id = user["user_id"]
    demo_name = user["name"]

    demo_number = int(demo_id.split("_")[1])

    demo_email = f"demo{demo_number:03d}@example.com"

    cursor = conn.execute("""
        INSERT INTO users (name, email, password)
        VALUES (?, ?, ?)
    """, (
        demo_name,
        demo_email,
        "TEMPORARY_DEMO_PASSWORD"
    ))

    user_mapping[demo_id] = cursor.lastrowid

# Insert synthetic check-ins
for _, row in df.iterrows():

    conn.execute("""
        INSERT INTO checkins (
            user_id,
            feeling_text,
            positive_text,
            sleep_hours,
            sleep_quality,
            mood_score,
            stress_score,
            energy_score,
            socializing,
            anxiety_text,
            created_at,
            screen_time,
            physically_active,
            social_media_hours
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_mapping[row["user_id"]],
        row["feeling_text"],
        row["positive_text"],
        row["sleep_hours"],
        row["sleep_quality"],
        row["mood_score"],
        row["stress_score"],
        row["energy_score"],
        row["socializing"],
        row["anxiety_text"],
        str(row["created_at"]),
        row["screen_time"],
        row["physically_active"],
        row["social_media_hours"]
    ))

conn.commit()

# Verify inserted records
user_count = conn.execute(
    "SELECT COUNT(*) FROM users"
).fetchone()[0]

checkin_count = conn.execute(
    "SELECT COUNT(*) FROM checkins"
).fetchone()[0]

conn.close()

print("Synthetic database created successfully!")
print("Database location:", DB_PATH)
print("Demo users:", user_count)
print("Synthetic check-ins:", checkin_count)
