"""
Comments Analytics page.
"""

import os

import streamlit as st
import pandas as pd
from pymongo import MongoClient

st.set_page_config(page_title="Comments - MBFC Bot", page_icon="💬", layout="wide")

MONGODB_URI = os.environ.get("MONGODB", "mongodb://localhost:27017")


@st.cache_resource
def get_db():
    client = MongoClient(MONGODB_URI)
    return client.reddit


db = get_db()

st.title("💬 Comment Analytics")

comments_collection = db["comments"]
comments_data = list(comments_collection.find())

if not comments_data:
    st.warning("No comments found in the database.")
    st.stop()

comments_df = pd.DataFrame(comments_data)

# Convert created_utc to datetime
comments_df["created_utc"] = pd.to_numeric(comments_df["created_utc"], errors="coerce")
comments_df["created_utc"] = pd.to_datetime(comments_df["created_utc"], unit="s", errors="coerce")
comments_df = comments_df.dropna(subset=["created_utc"])

# Metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Comments", len(comments_df))
with col2:
    st.metric("Unique Commenters", comments_df["author"].nunique())
with col3:
    avg = len(comments_df) / max(comments_df["author"].nunique(), 1)
    st.metric("Avg Comments/User", f"{avg:.1f}")

st.markdown("---")

# Comments over time
st.subheader("Comments Over Time")
comments_over_time = comments_df.set_index("created_utc").resample("D").size()
st.line_chart(comments_over_time)

# Most active commenters
st.subheader("Most Active Commenters")
most_active = comments_df["author"].value_counts().head(15)
st.bar_chart(most_active)

# Comment length distribution
st.subheader("Comment Length Distribution")
comments_df["word_count"] = comments_df["body"].apply(lambda x: len(str(x).split()))
st.bar_chart(comments_df["word_count"].value_counts().sort_index().head(50))

# Hourly activity
st.subheader("Hourly Comment Activity")
comments_df["hour"] = comments_df["created_utc"].dt.hour
hourly = comments_df["hour"].value_counts().sort_index()
st.bar_chart(hourly)

# AI moderation flags
if "ai_removal_reason" in comments_df.columns:
    flagged = comments_df[comments_df["ai_removal_reason"].notna()]
    st.subheader(f"🤖 AI-Flagged Comments ({len(flagged)})")
    if not flagged.empty:
        st.dataframe(
            flagged[["author", "body", "ai_removal_reason", "created_utc"]].head(20),
            use_container_width=True,
        )
