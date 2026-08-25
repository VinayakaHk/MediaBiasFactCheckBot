"""
Subreddit Growth page.
"""

import os

import streamlit as st
import pandas as pd
from pymongo import MongoClient

st.set_page_config(page_title="Subreddit Growth - MBFC Bot", page_icon="📈", layout="wide")

MONGODB_URI = os.environ.get("MONGODB", "mongodb://localhost:27017")


@st.cache_resource
def get_db():
    client = MongoClient(MONGODB_URI)
    return client.reddit


db = get_db()

st.title("📈 Subreddit Growth")

submissions_collection = db["submissions"]
subreddit_data = list(submissions_collection.find({}, {"created": 1, "subreddit_subscribers": 1, "subreddit": 1}))

if not subreddit_data:
    st.warning("No data available.")
    st.stop()

df = pd.DataFrame(subreddit_data)
df["created"] = pd.to_numeric(df["created"], errors="coerce")
df["created"] = pd.to_datetime(df["created"], unit="s", errors="coerce")
df["subreddit_subscribers"] = pd.to_numeric(df["subreddit_subscribers"], errors="coerce")
df = df.dropna(subset=["created", "subreddit_subscribers"])
df = df.sort_values("created")

# Current stats
if not df.empty:
    latest = df.iloc[-1]
    earliest = df.iloc[0]
    growth = int(latest["subreddit_subscribers"] - earliest["subreddit_subscribers"])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Subscribers", f"{int(latest['subreddit_subscribers']):,}")
    with col2:
        st.metric("Growth (tracked period)", f"+{growth:,}")
    with col3:
        days = (latest["created"] - earliest["created"]).days or 1
        st.metric("Avg Daily Growth", f"+{growth / days:.1f}")

st.markdown("---")

# Growth chart
st.subheader("Subscriber Count Over Time")
chart_df = df.set_index("created")[["subreddit_subscribers"]].resample("D").last().dropna()
st.line_chart(chart_df)
