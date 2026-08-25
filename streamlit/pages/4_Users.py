"""
User Analytics page.
"""

import os

import streamlit as st
import pandas as pd
from pymongo import MongoClient

st.set_page_config(page_title="Users - MBFC Bot", page_icon="👥", layout="wide")

MONGODB_URI = os.environ.get("MONGODB", "mongodb://localhost:27017")


@st.cache_resource
def get_db():
    client = MongoClient(MONGODB_URI)
    return client.reddit


db = get_db()

st.title("👥 User Analytics")

submissions_data = list(db["submissions"].find({}, {"author": 1, "created": 1}))
comments_data = list(db["comments"].find({}, {"author": 1, "created_utc": 1, "body": 1}))

if not submissions_data and not comments_data:
    st.warning("No data available.")
    st.stop()

submissions_df = pd.DataFrame(submissions_data) if submissions_data else pd.DataFrame(columns=["author"])
comments_df = pd.DataFrame(comments_data) if comments_data else pd.DataFrame(columns=["author"])

# Power users
st.subheader("Power Users (Most Active)")
all_authors = pd.concat([submissions_df["author"], comments_df["author"]])
power_users = all_authors.value_counts().head(20).reset_index()
power_users.columns = ["Author", "Total Activity"]
st.bar_chart(power_users.set_index("Author"))

st.markdown("---")

# User lookup
st.subheader("🔍 User Lookup")
user_name = st.text_input("Enter a Reddit username:", placeholder="e.g. CalmlyPassionate")

if user_name:
    user_submissions = submissions_df[submissions_df["author"] == user_name]
    user_comments = comments_df[comments_df["author"] == user_name]

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Submissions", len(user_submissions))
    with col2:
        st.metric("Comments", len(user_comments))

    if not user_comments.empty:
        user_comments["created_utc"] = pd.to_numeric(user_comments["created_utc"], errors="coerce")
        user_comments["created_utc"] = pd.to_datetime(user_comments["created_utc"], unit="s", errors="coerce")
        user_comments = user_comments.dropna(subset=["created_utc"])

        if not user_comments.empty:
            st.subheader("Comment Activity Over Time")
            activity = user_comments.set_index("created_utc").resample("D").size()
            st.line_chart(activity)

            st.subheader("Peak Activity Hours")
            hourly = user_comments["created_utc"].dt.hour.value_counts().sort_index()
            st.bar_chart(hourly)

    if not user_submissions.empty:
        user_submissions["created"] = pd.to_numeric(user_submissions["created"], errors="coerce")
        user_submissions["created"] = pd.to_datetime(user_submissions["created"], unit="s", errors="coerce")
        st.subheader("Recent Submissions")
        st.dataframe(user_submissions[["created", "author"]].sort_values("created", ascending=False).head(10))
