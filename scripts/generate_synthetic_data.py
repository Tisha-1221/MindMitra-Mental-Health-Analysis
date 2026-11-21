import pandas as pd
import numpy as np
import os
from pathlib import Path

# Reproducible synthetic data
np.random.seed(42)

# Create output folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FOLDER = PROJECT_ROOT / "data(Synthetic)"

DATA_FOLDER.mkdir(parents=True, exist_ok=True)

records = []

age_groups = ["15 - 20", "21 - 30", "31 - 40"]
genders = ["Male", "Female", "Prefer not to say"]
occupations = ["Student", "Employee", "Other"]

feelings = [
    "I had a productive day",
    "I felt a little stressed today",
    "I had a calm and peaceful day",
    "I felt tired and low on energy",
    "I felt happy and motivated",
    "I had difficulty concentrating"
]

positive_texts = [
    "I spent time with friends",
    "I completed my daily tasks",
    "I enjoyed listening to music",
    "I went for a walk",
    "I spent time with family",
    "I learned something new"
]

anxiety_texts = [
    "No major concerns today",
    "I felt slightly anxious",
    "I had some work-related stress",
    "I felt worried about upcoming tasks",
    "I felt relaxed today"
]

remarks = [
    "Feeling positive",
    "Need better sleep",
    "Had a busy day",
    "Feeling relaxed",
    "Want to reduce screen time",
    "Planning to exercise more"
]

# Generate 100 independent synthetic check-ins
for i in range(100):

    user_number = (i % 10) + 1
    day_number = i // 10

    sleep_hours = round(
        np.clip(np.random.normal(7, 1.3), 3, 10), 1
    )

    screen_time = round(
        np.clip(np.random.normal(5.5, 1.8), 1, 12), 1
    )

    social_media_hours = round(
        np.clip(np.random.normal(2.5, 1.2), 0, screen_time), 1
    )

    physically_active = np.random.choice(
        ["Yes", "No"], p=[0.65, 0.35]
    )

    # Illustrative scores with mild behavioral relationships
    stress_score = int(np.clip(
        round(5 + (screen_time - 5) * 0.5
              - (sleep_hours - 7) * 0.6
              + np.random.normal(0, 1.5)),
        1, 10
    ))

    mood_score = int(np.clip(
        round(7 - (stress_score - 5) * 0.4
              + np.random.normal(0, 1.5)),
        1, 10
    ))

    energy_score = int(np.clip(
        round(5 + (sleep_hours - 7) * 0.7
              + (physically_active == "Yes") * 1
              + np.random.normal(0, 1.5)),
        1, 10
    ))

    sleep_quality = (
        "Good" if sleep_hours >= 7
        else "Average" if sleep_hours >= 5
        else "Poor"
    )

    exercise = (
        1 if physically_active == "Yes" else 0
    )

    socializing = np.random.randint(1, 6)
    sociallyconnected_score = np.random.randint(1, 11)

    timestamp = (
        pd.Timestamp("2026-10-01")
        + pd.Timedelta(days=day_number)
    )

    records.append({
        "time_stamp": timestamp,
        "created_at": timestamp,
        "date": timestamp.date(),
        "week": timestamp.isocalendar().week,
        "user_id": f"demo_{user_number:03d}",
        "name": f"Demo User {user_number:02d}",
        "age_group": np.random.choice(age_groups),
        "gender": np.random.choice(genders),
        "occupation": np.random.choice(occupations),
        "feeling_text": np.random.choice(feelings),
        "positive_text": np.random.choice(positive_texts),
        "anxiety_text": np.random.choice(anxiety_texts),
        "sleep_hours": sleep_hours,
        "sleep_quality": sleep_quality,
        "screen_time": screen_time,
        "social_media_hours": social_media_hours,
        "socialmedia_hours>3": int(social_media_hours > 3),
        "physically_active": physically_active,
        "exercise": exercise,
        "mood_score": mood_score,
        "stress_score": stress_score,
        "energy_score": energy_score,
        "socializing": socializing,
        "sociallyconnected_score": sociallyconnected_score,
        "user_remark": np.random.choice(remarks)
    })

# Convert records into a DataFrame
df = pd.DataFrame(records)

# Save synthetic CSV
output_path = DATA_FOLDER / "demo_wellness_data.csv"
df.to_csv(output_path, index=False)

print("Synthetic dataset created successfully!")
print("Number of records:", len(df))
print("Number of columns:", len(df.columns))
print("Saved to:", output_path)

print("\nFirst 5 records:")
print(df.head())
