import streamlit as st
import pandas as pd
from app import connect_to_sheets
import altair as alt

st.set_page_config(page_title="Profiles")

st.title("🏆 Profiles — Felipe & Kaden")

# Load sheet
sheet = connect_to_sheets()
df = pd.DataFrame(sheet.get_all_records())

if df.empty:
    st.info("No reps logged yet.")
    st.stop()

# Weekly summary
df["week_index"] = df["week_index"].astype(int)

# Summary table per person
summary = df.groupby(["name", "exercise"]).agg(
    total=("reps", "sum")
).reset_index()

# Weekly totals
weekly_totals = df.groupby(["name", "week_index"]).agg(
    total=("reps", "sum")
).reset_index()

# --- Layout ---
col1, col2 = st.columns(2)

# ------------------------
# FELIPE
# ------------------------
with col1:
    st.header("Felipe")

    fel = df[df["name"] == "Felipe"]

    st.subheader("Total Reps by Exercise")
    chart_data = summary[summary["name"] == "Felipe"]
    bar = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X("total:Q", title="Total reps"),
        y=alt.Y("exercise:N", title="Exercise"),
        color="exercise"
    )
    st.altair_chart(bar, use_container_width=True)

    st.subheader("Weekly History")
    weekly = weekly_totals[weekly_totals["name"] == "Felipe"]
    st.table(weekly.sort_values("week_index"))

# ------------------------
# KADEN
# ------------------------
with col2:
    st.header("Kaden")

    kad = df[df["name"] == "Kaden"]

    st.subheader("Total Reps by Exercise")
    chart_data = summary[summary["name"] == "Kaden"]
    bar2 = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X("total:Q", title="Total reps"),
        y=alt.Y("exercise:N", title="Exercise"),
        color="exercise"
    )
    st.altair_chart(bar2, use_container_width=True)

    st.subheader("Weekly History")
    weekly2 = weekly_totals[weekly_totals["name"] == "Kaden"]
    st.table(weekly2.sort_values("week_index"))
