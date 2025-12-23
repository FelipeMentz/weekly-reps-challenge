import streamlit as st
import pandas as pd
from datetime import date
from datetime import datetime
from config import challenge_timezone
from config import CHALLENGE_CONFIG
from config import MODE
from pathlib import Path

# Google Sheets imports
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -----------------------------
# CONFIG
# -----------------------------
BASELINE_WEEK_START = date(2025, 12, 15)

GOOGLE_SHEET_NAME = "weekly-reps"   # Production sheet name

# -----------------------------
# WEEK INDEX CALCULATION
# -----------------------------
def get_custom_week_index(d: date) -> int:
    delta_days = (d - BASELINE_WEEK_START).days
    if delta_days < 0:
        return 0
    return (delta_days // 7) + 1



# -----------------------------
# GOOGLE SHEETS FUNCTIONS
# -----------------------------
def connect_to_sheets():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    service_account_info = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
    client = gspread.authorize(creds)

    return client.open(GOOGLE_SHEET_NAME).sheet1


def load_from_sheets(sheet):
    data = sheet.get_all_records()
    if not data:
        return pd.DataFrame(columns=["name", "exercise", "reps", "date", "week_index"])

    df = pd.DataFrame(data)
    df["reps"] = df["reps"].astype(int)
    # Normalize exercise names to lowercase (matches config keys)
    df["exercise"] = df["exercise"].str.lower()
    df["week_index"] = df["week_index"].astype(int)
    return df


def append_to_sheets(sheet, row_dict):
    sheet.append_row([
        row_dict["name"],
        row_dict["exercise"],
        row_dict["reps"],
        row_dict["date"],
        row_dict["week_index"]
    ])


# -----------------------------
# LOAD MAIN DATA (Sheets only)
# -----------------------------
try:
    if MODE == "prod":
        sheet = connect_to_sheets()
        df = load_from_sheets(sheet)
    else:
        df = pd.DataFrame(
            [
                {
                    "name": "Felipe",
                    "exercise": "squat",
                    "reps": 120,
                    "date": "2025-12-15",
                    "week_index": 1,
                },
                {
                    "name": "Kaden",
                    "exercise": "push-up",
                    "reps": 80,
                    "date": "2025-12-15",
                    "week_index": 1,
                },
            ]
        )

except Exception as e:
    st.error(f"Google Sheets error: {e}")
    df = pd.DataFrame()

# Weekly reps per person per exercise
weekly_exercise_reps = (
    df.groupby(["name", "week_index", "exercise"])["reps"]
    .sum()
    .reset_index()
)

# ----------------
# function
# ---------------

def evaluate_week_status(weekly_df, config):

    exercise_status = {}

    for exercise_key, cfg in config.items():
        target = cfg["weekly_target"]

        reps_done = (
            weekly_df.loc[weekly_df["exercise"] == exercise_key, "reps"]
            .sum()
        )

        progress = min(reps_done / target, 1.0)

        exercise_status[exercise_key] = {
            "reps": int(reps_done),
            "target": target,
            "completed": reps_done >= target,
            "progress": progress,
        }

    week_completed = all(
        ex["completed"] for ex in exercise_status.values()
    )

    return {
        "exercise_status": exercise_status,
        "week_completed": week_completed,
    }


# -----------------------------
# PAGE SETUP
# -----------------------------
st.set_page_config(page_title="Weekly Reps Challenge")
st.title("1000 CHALLENGE")
st.write("400 Squats, 300 Push-Ups, 200 Dips, and 100 Pull-Ups WEEKLY is what it takes to turn boys into men!")

# -----------------------------
# FORM
# -----------------------------
st.subheader("Log your reps")

with st.form("log_form"):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        name = st.selectbox("Who are you?", ["Felipe", "Kaden"])

    with col2:
        exercise = st.selectbox(
            "Exercise",
            [cfg["display_name"] for cfg in CHALLENGE_CONFIG.values()]
        )

    with col3:
        reps = st.number_input(
            "Reps",
            min_value=1,
            step=1,
            value=10
        )

    with col4:
        st.write("\n")
        st.write("\n")

        submitted = st.form_submit_button("Submit")


if submitted:
    now = datetime.now(challenge_timezone)
    today = now.date()
    week_index = get_custom_week_index(today)

    new_row = {
        "name": name,
        "exercise": exercise,
        "reps": int(reps),
        "date": today.isoformat(),
        "week_index": int(week_index),
        }

    # Update in-memory df
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # Save ONLY to Google Sheets
    append_to_sheets(sheet, new_row)

    st.success(f"Saved: {name} – {reps} x {exercise} on {today} 💪")

if df.empty:
    current_week = 0
else:
    current_week = int(df["week_index"].max())

# -----------------------------
# WEEKLY STANDINGS
# -----------------------------

st.markdown(f"## Week {current_week} standings")

col_left, col_right = st.columns(2)

def render_person_week(person, weekly_df, week_index):
    st.markdown(f"## {person}")

    person_week_df = weekly_df[
        (weekly_df["name"] == person) &
        (weekly_df["week_index"] == week_index)
        ]

    status = evaluate_week_status(person_week_df, CHALLENGE_CONFIG)

    for exercise_key, cfg in sorted(
        CHALLENGE_CONFIG.items(),
        key=lambda x: x[1]["order"]
        ):
        info = status["exercise_status"][exercise_key]

        st.write(
            f"**{cfg['display_name']}** — "
            f"{info['reps']} / {info['target']}"
        )
        st.progress(info["progress"])

    if status["week_completed"]:
        st.success("✅ Week completed")
    else:
        st.warning("❌ Week not completed")

with col_left:
    render_person_week("Felipe", weekly_exercise_reps, current_week)

with col_right:
    render_person_week("Kaden", weekly_exercise_reps, current_week)




