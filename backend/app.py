from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify, session, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from pathlib import Path
import sqlite3
import os

# Load environment variables from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

app = Flask(__name__)

# Secure Flask session key
app.secret_key = os.getenv("FLASK_SECRET_KEY")

if not app.secret_key:
    raise RuntimeError(
        "FLASK_SECRET_KEY is missing. "
        "Please configure it in the root .env file."
    )

CORS(
    app,
    origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    supports_credentials=True
)
# -----------------------------
# DATABASE CONNECTION
# -----------------------------

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

DATABASE_FOLDER = PROJECT_ROOT / "database(Synthetic)"
DATABASE_FOLDER.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATABASE_FOLDER / "mindmitra.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# -----------------------------
# CREATE USERS TABLE
# -----------------------------
def create_users_table():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

create_users_table()


# -----------------------------
# CREATE CHECKINS TABLE
# -----------------------------
def create_checkins_table():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            feeling_text TEXT,
            positive_text TEXT,
            sleep_hours REAL,
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

    conn.commit()
    conn.close()

create_checkins_table()



# -----------------------------
# SIGNUP ROUTE
# -----------------------------
@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    # Generate a secure password hash
    hashed_password = generate_password_hash(password)

    try:
        conn = get_db_connection()

        conn.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, hashed_password)
        )

        conn.commit()
        conn.close()

        return jsonify({"message": "Signup successful"})

    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Email already exists"}), 400



# -----------------------------
# LOGIN ROUTE
# -----------------------------
@app.route("/login", methods=["POST", "OPTIONS"])
def login():

    if request.method == "OPTIONS":
        return jsonify({"ok": True}), 200

    data = request.get_json(force=True)

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Missing credentials"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name, email, password
        FROM users
        WHERE email = ? OR name = ?
        """,
        (email, email)
    )

    user = cursor.fetchone()
    conn.close()

    # Verify the entered password against the stored hash
    if user and check_password_hash(user["password"], password):

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]

        return jsonify({"message": "Login successful"})

    else:
        return jsonify({"error": "Invalid email or password"}), 401

    




@app.route("/check-session")
def check_session():
    if "user_id" in session:
        return jsonify({
            "logged_in": True,
            "name": session["user_name"]
        })
    else:
        return jsonify({"logged_in": False})
    
@app.route("/current-user", methods=["GET"])
def get_current_user():
    if "user_id" in session:
        return jsonify({
            "user_id": session["user_id"],
            "name": session["user_name"]
        })
    else:
        return jsonify({"error": "Not logged in"}), 401

# -----------------------------
# SAVE DAILY CHECK-IN
# -----------------------------
@app.route("/save-checkin", methods=["POST"])
def save_checkin():
    print("SAVE CHECKIN HIT")   # 👈 must be here
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()

    conn = get_db_connection()
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
            screen_time,
            physically_active,
            social_media_hours
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session["user_id"],
        data.get("feeling_text"),
        data.get("positive_text"),
        data.get("sleep_hours"),
        data.get("sleep_quality"),
        data.get("mood_score"),
        data.get("stress_score"),
        data.get("energy_score"),
        data.get("socializing"),
        data.get("anxiety_text"),
        data.get("screen_time"),
        data.get("physically_active"),
        data.get("social_media_hours")
        
    ))

    conn.commit()
    conn.close()

    return jsonify({"message": "Check-in saved successfully"})



# -----------------------------
# RUN APP (ALWAYS LAST)
# -----------------------------
if __name__ == "__main__":
    app.run(debug=False)
