import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import joblib
import numpy as np
from pathlib import Path

# ==================================================
# DATABASE PATH
# ==================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "database(Synthetic)" / "mindmitra.db"

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="MindMitra Dashboard", layout="wide")

# ==================================================
# PASTEL UI CSS
# ==================================================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(120deg, #fdfbfb 0%, #ebedee 100%);
}

.metric-card {
    padding: 22px;
    border-radius: 18px;
    text-align: center;
    box-shadow: 0 12px 30px rgba(0,0,0,0.06);
}

.sleep { background: #E8F0FE; }
.mood { background: #FFF4E6; }
.stress { background: #FFECEC; }
.energy { background: #E8FFF3; }
.exercise { background: #F1ECFF; }

.metric-value {
    font-size: 34px;
    font-weight: 700;
    margin-top: 8px;
}
.metric-label {
    font-size: 16px;
    color: #444;
}

.reco-box {
    background: #ffffff;
    padding: 18px;
    border-radius: 16px;
    border-left: 6px solid #8ecae6;
    box-shadow: 0 6px 20px rgba(0,0,0,0.06);
}
</style>
""", unsafe_allow_html=True)

# ======================
# Get user_id from URL
# =======================
query_params = st.query_params
user_id = query_params.get("user_id")

if not user_id:
    st.error("No user specified.")
    st.stop()

user_id = int(user_id)


# ==================================================
# LOAD DATA
# ==================================================
@st.cache_data(ttl=10)
def load_data(user_id):
    import os
    import sqlite3
    import pandas as pd

    conn = sqlite3.connect(DB_PATH)

    if user_id is None:
        st.error("User ID missing.")
        st.stop()


    query = """
    SELECT
        sleep_hours,
        sleep_quality,
        mood_score,
        stress_score,
        energy_score,
        socializing,
        screen_time,
        social_media_hours,
        physically_active,
        created_at AS timestamp
    FROM checkins
    WHERE user_id = ?
    """

    df = pd.read_sql_query(query, conn, params=(user_id,))

    conn.close()

    if df.empty:
        return df   # return empty df safely

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])

    numeric_cols = [
        "sleep_hours",
        "sleep_quality",
        "mood_score",
        "stress_score",
        "energy_score",
        "socializing",
        "screen_time",
        "social_media_hours",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df

@st.cache_resource
def load_model():
    import os
    model_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "model", "mental_health_demo_model.pkl")
    )
    return joblib.load(model_path)

model = load_model()


# ==================================================
# FETCH USERNAME
# ==================================================
@st.cache_data(ttl=10)
def get_username(user_id):
    import os
    import sqlite3

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]
    else:
        return "User"


df = load_data(user_id)
username = get_username(user_id)


if df.empty:
    st.warning("No wellness check-ins found yet.")
    st.stop()

latest = df.sort_values("timestamp").iloc[-1]

# Convert activity
physically_active_encoded = 1 if latest["physically_active"] == "Yes" else 0

# Convert social media hours >3
socialmedia_hours_encoded = 1 if latest["social_media_hours"] > 3 else 0

# Create feature vector matching model training
features = np.array([[

    latest["sleep_hours"],        # sleep_hours
    latest["sleep_quality"],      # sleep_quality
    latest["screen_time"],        # screen_time
    socialmedia_hours_encoded,    # socialmedia_hours>3_encoded
    physically_active_encoded,    # physically_active_encoded
    0,                            # exercise (not collected)
    latest["mood_score"],         # mood_score
    latest["stress_score"],       # stress_score
    latest["energy_score"],       # energy_score
    latest["socializing"],        # socializing
    0,                            # sociallyconnected_score
    1,                            # age_group_encoded
    1,                            # gender_encoded
    0,                            # feeling_sentiment
    0,                            # positive_sentiment
    0,                            # anxiety_sentiment
    0                             # remark_sentiment

]])
prediction = model.predict(features)[0]
risk_labels = {
    0: "Low Risk",
    1: "Moderate Risk",
    2: "High Risk"
}

predicted_risk = risk_labels.get(prediction, "Unknown")

# ==================================================
# TIME FEATURES
# ==================================================
df['date'] = df['timestamp'].dt.date
df['week'] = df['timestamp'].dt.to_period('W').astype(str)
df['month'] = df['timestamp'].dt.to_period('M').astype(str)
df['year'] = df['timestamp'].dt.year

# ==================================================
# HEADER
# ==================================================
st.title("🧠 MindMitra – Mental Wellness Dashboard")
st.caption("A calm, supportive space to understand your wellbeing 🌿")

# ==================================================
# PERIOD SELECTOR
# ==================================================
period = st.radio("View insights by", ["Daily", "Weekly", "Monthly", "Yearly"], horizontal=True)

group_col = {
    "Daily": "date",
    "Weekly": "week",
    "Monthly": "month",
    "Yearly": "year"
}[period]

agg_df = df.groupby(group_col, as_index=False).mean(numeric_only=True)
latest = agg_df.sort_values(by=group_col).iloc[-1]


# ==================================================
# METRIC CARD FUNCTION
# ==================================================
def metric_card(col, label, value, cls):
    col.markdown(f"""
    <div class="metric-card {cls}">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# ==================================================
# WELLNESS SNAPSHOT
# ==================================================
st.subheader("📌 Wellness Snapshot")

c1, c2, c3, c4, c5 = st.columns(5)

metric_card(c1, "😴 Sleep (hrs)", round(latest['sleep_hours'], 2), "sleep")
metric_card(c2, "🙂 Mood", round(latest['mood_score'], 2), "mood")
metric_card(c3, "😰 Stress", round(latest['stress_score'], 2), "stress")
metric_card(c4, "⚡ Energy", round(latest['energy_score'], 2), "energy")


exercise_col = next((c for c in ['exercise', 'physical_activity', 'physically_active'] if c in agg_df.columns), None)

# ---- Exercise / Physical Activity Snapshot (ALIGNED WITH TIME FILTER) ----
# if 'physically_active_encoded' in latest.index:
#     metric_card(
#         c5,
#         "🏃 Avg Physical Activity",
#         round(latest['physically_active_encoded'], 2),
#         "exercise"
#     )
# else:
#     metric_card(c5, "🏃 Exercise", "N/A", "exercise")


# ==================================================
# PASTEL CHART STYLE
# ==================================================
def pastel_layout(fig):
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#444"),
        xaxis=dict(showgrid=True, gridcolor="#eaeaea"),
        yaxis=dict(showgrid=True, gridcolor="#eaeaea")
    )
    return fig

# ==================================================
# WELLNESS TRENDS
# ==================================================
st.subheader(f"📊 {period} Wellness Trends")

colA, colB = st.columns(2)

colA.plotly_chart(
    pastel_layout(px.line(agg_df, x=group_col, y='mood_score', markers=True,
                           color_discrete_sequence=["#F4A261"])),
    use_container_width=True,
    key="mood_trend"
)

colB.plotly_chart(
    pastel_layout(px.line(agg_df, x=group_col, y='stress_score', markers=True,
                           color_discrete_sequence=["#E76F51"])),
    use_container_width=True,
    key="stress_trend"
)

colC, colD = st.columns(2)

colC.plotly_chart(
    pastel_layout(px.bar(agg_df, x=group_col, y='sleep_hours',
                          color_discrete_sequence=["#90DBF4"])),
    use_container_width=True,
    key="sleep_trend"
)

colD.plotly_chart(
    pastel_layout(px.bar(agg_df, x=group_col, y='energy_score',
                          color_discrete_sequence=["#2A9D8F"])),
    use_container_width=True,
    key="energy_trend"
)

# ==================================================
# SCREEN & STRESS ANALYSIS
# ==================================================
st.subheader("📱 Screen Time & Stress Analysis")

col1, col2 = st.columns(2)

with col1:
    fig1 = px.line(
        df,
        x="timestamp",
        y=["screen_time", "social_media_hours"],
        markers=True,
        title="Screen Time & Social Media"
    )
    st.plotly_chart(pastel_layout(fig1), use_container_width=True, key="screen_usage")

with col2:
    fig2 = px.scatter(
        df,
        x="screen_time",
        y="stress_score",
        trendline="ols",
        title="Stress vs Screen Time"
    )
    st.plotly_chart(pastel_layout(fig2), use_container_width=True, key="stress_screen")

# ==================================================
# ENERGY & ACTIVITY ANALYSIS
# ==================================================
df["physically_active"] = df["physically_active"].map({"Yes": 1, "No": 0})

st.subheader("⚡ Energy & Activity Analysis")

col3, col4 = st.columns(2)

with col3:
    fig3 = px.scatter(
        df,
        x="physically_active",
        y="energy_score",
        trendline="ols",
        title="Energy vs Physical Activity"
    )
    st.plotly_chart(pastel_layout(fig3), use_container_width=True, key="energy_activity")

with col4:
    fig4 = px.box(
        df,
        x="physically_active",
        y="energy_score",
        title="Energy Distribution by Activity"
    )
    st.plotly_chart(pastel_layout(fig4), use_container_width=True, key="energy_distribution")


# ==================================================
# PROFESSIONAL WELLNESS SUMMARY
# ==================================================

st.markdown("""
<style>
.insight-card {
    background-color: #F8F9FB;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 18px;
    border-left: 6px solid #4A90E2;
}

.insight-title {
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 8px;
}

.insight-text {
    font-size: 16px;
    font-weight: 500;
    color: #333333;
}

.recommendation {
    margin-top: 10px;
    font-size: 15px;
    font-weight: 600;
    color: #111111;
}
</style>
""", unsafe_allow_html=True)


st.markdown("## 🧠 Your Wellness Overview")

if len(df) > 1:

    corr1 = df["screen_time"].corr(df["stress_score"])
    corr2 = df["physically_active"].corr(df["energy_score"])

    # ===============================
    # SCREEN TIME CARD
    # ===============================
    if corr1 > 0.5:
        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-title">📱 Screen Time & Stress</div>
            <div class="insight-text">
                High positive relationship detected between screen time and stress levels.
            </div>
            <div class="recommendation">
                ✔ Recommendation: Reduce screen exposure in evenings and before sleep.
            </div>
        </div>
        """, unsafe_allow_html=True)

    elif corr1 < -0.5:
        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-title">📱 Screen Time & Stress</div>
            <div class="insight-text">
                Screen time does not appear to significantly increase stress.
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-title">📱 Screen Time & Stress</div>
            <div class="insight-text">
                Moderate relationship observed between screen time and stress.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ===============================
    # ENERGY CARD
    # ===============================
    if corr2 > 0.5:
        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-title">⚡ Physical Activity & Energy</div>
            <div class="insight-text">
                Strong positive impact of physical activity on energy levels.
            </div>
        </div>
        """, unsafe_allow_html=True)

    elif corr2 < -0.5:
        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-title">⚡ Physical Activity & Energy</div>
            <div class="insight-text">
                Unexpected negative pattern between activity and energy.
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-title">⚡ Physical Activity & Energy</div>
            <div class="insight-text">
                Physical activity shows mild impact on your energy levels.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ===============================
    # RISK SCORE SECTION
    # ===============================

    avg_stress = df["stress_score"].mean()
    avg_screen = df["screen_time"].mean()
    avg_sleep = df["sleep_hours"].mean()
    avg_energy = df["energy_score"].mean()
    avg_activity = df["physically_active"].mean()

    # Use AI prediction to determine gauge score
    if predicted_risk == "Low Risk":
        risk_score = 2

    elif predicted_risk == "Moderate Risk":
        risk_score = 5

    else:
        risk_score = 8

    import plotly.graph_objects as go

    st.markdown("## 🧠 Mental Wellness Risk Score")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        number={
            'suffix': " / 10",
            'font': {'size': 30}
        },
        gauge={
            'axis': {'range': [0, 10]},
            'bar': {'color': "#4A90E2"},
            'steps': [
                {'range': [0, 3], 'color': "#C8E6C9"},     # Green
                {'range': [3, 6], 'color': "#FFF3CD"},     # Yellow
                {'range': [6, 10], 'color': "#F8D7DA"}     # Red
            ],
        }
    ))

    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Risk label
    if predicted_risk == "High Risk":
        st.error(f"⚠️ Predicted Risk Level: {predicted_risk}")
    elif predicted_risk == "Moderate Risk":
        st.warning(f"⚠️ Predicted Risk Level: {predicted_risk}")
    else:
        st.success(f"✅ Predicted Risk Level: {predicted_risk}")

else:
    st.warning("Not enough data to generate insights yet.")


# ==================================================
# PHYSICAL ACTIVITY TREND
# # ==================================================
# st.subheader("🏃 Physical Activity Trend")

# st.plotly_chart(
#     px.line(agg_df, x=group_col, y='exercise_score', markers=True),
#     use_container_width=True
# )

# ==================================================
# SMART PERSONALIZED WELLBEING INSIGHTS
# ==================================================

st.markdown("## 🧠 Personalized Wellbeing Insights")

avg_stress = df["stress_score"].mean()
avg_screen = df["screen_time"].mean()
avg_sleep = df["sleep_hours"].mean()
avg_energy = df["energy_score"].mean()
avg_activity = df["physically_active"].map({"Yes": 1, "No": 0}).mean()

recommendations = []

# --------------------------------------------------
# COLOR BASED ON STRESS LEVEL
# --------------------------------------------------

if avg_stress >= 6:
    card_color = "#F8D7DA"  # light red
    border_color = "#DC3545"
    heading_emoji = "😟"
    intro_text = f"Oh {username}, you look stressed this week."
elif 4 <= avg_stress < 6:
    card_color = "#FFF3CD"  # light yellow
    border_color = "#FFC107"
    heading_emoji = "🙂"
    intro_text = f"{username}, you seem slightly stressed."
else:
    card_color = "#D4EDDA"  # light green
    border_color = "#28A745"
    heading_emoji = "😊"
    intro_text = f"Great job {username}! You look stable and balanced."

# --------------------------------------------------
# TRIGGER-BASED RECOMMENDATIONS
# --------------------------------------------------

if avg_screen > 5:
    recommendations.append(f"Reduce screen time (currently {round(avg_screen,1)} hrs/day)")

if avg_sleep < 6.5:
    recommendations.append("Aim for at least 7 hours of sleep tonight")

if avg_energy < 5:
    recommendations.append("Take a short 15-minute walk to boost energy")

if avg_activity < 0.5:
    recommendations.append("Add light physical activity like stretching")

# Always ensure minimum 3 suggestions
if len(recommendations) < 3:
    recommendations.append("Practice 5 minutes of deep breathing")
if len(recommendations) < 3:
    recommendations.append("Write down 3 positive thoughts before bed")

# --------------------------------------------------
# DISPLAY CARD
# --------------------------------------------------

st.markdown(f"""
<div style="
    background-color:{card_color};
    padding:22px;
    border-radius:18px;
    border-left:8px solid {border_color};
    box-shadow:0 6px 18px rgba(0,0,0,0.08);
">
    <h3>{heading_emoji} {intro_text}</h3>
    <p>Your average stress score is <b>{round(avg_stress,1)} / 10</b>.</p>
    <p><b>Here are a few simple things you can try:</b></p>
    <ul>
        {''.join([f"<li>{rec}</li>" for rec in recommendations])}
    </ul>
</div>
""", unsafe_allow_html=True)