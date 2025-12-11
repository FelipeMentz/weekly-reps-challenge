import streamlit as st
import pandas as pd
from datetime import date, timedelta
from pathlib import Path

# Google Sheets imports
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# -----------------------------
# CONFIG
# -----------------------------
BASELINE_WEEK_START = date(2025, 12, 8)

CSV_PATH = Path("data/logs.csv")
CSV_PATH.parent.mkdir(exist_ok=True)

GOOGLE_SHEET_NAME = "weekly-reps"   # Your sheet name
SERVICE_ACCOUNT_FILE = "service_account.json"


# -----------------------------
# WEEK INDEX CALCULATION
# -----------------------------
def get_custom_week_index(d: date) -> int:
    delta_days = (d - BASELINE_WEEK_START).days
    week_number = delta_days // 7
    return max(week_number + 1, 1)


# -----------------------------
# STORAGE LAYER — CSV
# -----------------------------
def load_from_csv():
    if CSV_PATH.exists() and CSV_PATH.stat().st_size > 0:
        return pd.read_csv(
            CSV_PATH,
            dtype={
                "week_index": "Int64",
                "reps": "Int64",
                "pullup_reps": "Int64",
            }
        )
    return pd.DataFrame(columns=["name", "exercise", "reps", "pullup_reps", "date", "week_index"])


def save_to_csv(df):
    df.to_csv(CSV_PATH, index=False)


# -----------------------------
# STORAGE LAYER — GOOGLE SHEETS
# -----------------------------
def connect_to_sheets():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        SERVICE_ACCOUNT_FILE, scope
    )
    client = gspread.authorize(creds)

    return client.open(GOOGLE_SHEET_NAME).sheet1


def load_from_sheets(sheet):
    data = sheet.get_all_records()
    if not data:
        return pd.DataFrame(columns=["name", "exercise", "reps", "pullup_reps", "date", "week_index"])
    df = pd.DataFrame(data)
    df["reps"] = df["reps"].astype(int)
    df["pullup_reps"] = df["pullup_reps"].astype(int)
    df["week_index"] = df["week_index"].astype(int)
    return df


def append_to_sheets(sheet, row_dict):
    """Append a new row to Google Sheets."""
    sheet.append_row([
        row_dict["name"],
        row_dict["exercise"],
        row_dict["reps"],
        row_dict["pullup_reps"],
        row_dict["date"],
        row_dict["week_index"]
    ])


# -----------------------------
# LOAD DATA FROM BOTH SOURCES
# -----------------------------
try:
    sheet = connect_to_sheets()
    df_sheets = load_from_sheets(sheet)
except Exception as e:
    st.error(f"Google Sheets error: {e}")
    df_sheets = pd.DataFrame()

df_csv = load_from_csv()

# Merge both (CSV is local backup)
df = pd.concat([df_csv, df_sheets], ignore_index=True).drop_duplicates()


# -----------------------------
# PAGE SETUP
# -----------------------------
st.set_page_config(page_title="Weekly Reps Challenge")
st.title("🏋️ Weekly Reps Challenge")
st.write("Now syncing with **CSV + Google Sheets**!")

left_col, right_col = st.columns([1.2, 2.5])


# -----------------------------
# FORM
# -----------------------------
with left_col:
    st.subheader("Log your reps")

    with st.form("reps_form"):
        name = st.selectbox("Who are you?", ["Felipe", "Kaden"])
        exercise = st.selectbox(
            "Exercise",
            ["Pull-up", "Push-up", "Squat", "Dip", "Other"]
        )
        reps = st.number_input(
            "How many reps?",
            min_value=1, step=1, value=10
        )

        submitted = st.form_submit_button("Submit")

    if submitted:
        today = date.today()
        week_index = get_custom_week_index(today)

        new_row = {
            "name": name,
            "exercise": exercise,
            "reps": int(reps),
            "pullup_reps": int(reps) if exercise == "Pull-up" else 0,
            "date": today.isoformat(),
            "week_index": int(week_index),
        }

        # Update local DataFrame
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        # Save to CSV
        save_to_csv(df)

        # Save to Google Sheets
        append_to_sheets(sheet, new_row)

        st.success(f"Saved: {name} – {reps} x {exercise} on {today} 💪")


# -----------------------------
# WEEKLY STANDINGS
# -----------------------------
with right_col:
    if not df.empty:
        person_week = df.groupby(["week_index", "name"]).agg(
            total_reps=("reps", "sum"),
            total_pullups=("pullup_reps", "sum")
        ).reset_index()

        current_week = int(person_week["week_index"].max())
        current_week_data = person_week[person_week["week_index"] == current_week]

        current_week_data["completed"] = (
            (current_week_data["total_reps"] >= 500) &
            (current_week_data["total_pullups"] >= 100)
        )
        current_week_data["status"] = current_week_data["completed"].apply(
            lambda x: "Completed" if x else "Not yet"
        )

        st.subheader(f"Week {current_week} standings")

        st.table(
            current_week_data[["name", "total_reps", "total_pullups", "status"]]
            .sort_values("total_reps", ascending=False)
        )
    else:
        st.write("No logs yet.")

    st.subheader("All logged reps (merged CSV + Sheets)")
    st.table(df[["name", "exercise", "reps", "date", "week_index"]])
