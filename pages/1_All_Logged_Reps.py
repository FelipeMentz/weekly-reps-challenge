import streamlit as st
import pandas as pd
from datetime import date
from app.py import load_from_sheets, connect_to_sheets  # import your functions

st.set_page_config(page_title="All Logged Reps")

st.title("📘 All Logged Reps")

# Load data
try:
    sheet = connect_to_sheets()
    df_sheets = pd.DataFrame(sheet.get_all_records())
except:
    st.error("Error loading data.")
    st.stop()

if df_sheets.empty:
    st.info("No reps logged yet.")
else:
    st.dataframe(df_sheets)
