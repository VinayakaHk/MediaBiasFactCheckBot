"""
Submissions Analytics page.
"""

import os

import streamlit as st
import pandas as pd
from pymongo import MongoClient
from collections import Counter

st.set_page_config(page_title="Submissions - MBFC Bot", page_icon="📝", layout="wide")

MONGODB_URI = os.environ.get("MONGODB", "mongodb://localhost:27017")


@st.cache_resource
def get_db():
    client = MongoClient(MONGODB_URI)
    return client.reddit


db = get_db()

st.title("📝 Submission Analytics")

# Retrieve submissions data
submissions_collection = db["submissions"]
submissions_data = list(submissions_collection.find())

if not submissions_data:
    st.warning("No submissions found in the database.")
    st.stop()

submissions_df = pd.DataFrame(submissions_data)

# Convert created column to datetime
submissions_df["created"] = pd.to_numeric(submissions_df["created"], errors="coerce")
submissions_df["created"] = pd.to_datetime(submissions_df["created"], unit="s", errors="coerce")
submissions_df = submissions_df.dropna(subset=["created"])

# Metrics row
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Submissions", len(submissions_df))
with col2:
    st.metric("Unique Authors", submissions_df["author"].nunique())
with col3:
    avg_per_user = len(submissions_df) / max(submissions_df["author"].nunique(), 1)
    st.metric("Avg Submissions/User", f"{avg_per_user:.1f}")

st.markdown("---")

# Submissions over time
st.subheader("Submissions Over Time")
submissions_count_over_time = submissions_df.set_index("created").resample("D").size()
st.line_chart(submissions_count_over_time)

# Most active users
st.subheader("Most Active Submitters")
most_active_users = submissions_df["author"].value_counts().head(15)
st.bar_chart(most_active_users)

# Domain analysis
st.subheader("Top Domains")
if "domain" in submissions_df.columns:
    domain_counts = submissions_df["domain"].value_counts().head(20)
    st.bar_chart(domain_counts)

# Submission type
st.subheader("Submission Type Distribution")
if "is_self" in submissions_df.columns:
    type_counts = submissions_df["is_self"].value_counts()
    type_counts.index = type_counts.index.map({"True": "Self-Post", "False": "Link Post", True: "Self-Post", False: "Link Post"})
    st.bar_chart(type_counts)

# Title word frequency
st.subheader("Top Words in Submission Titles")
stop_words = {"the", "a", "an", "is", "in", "to", "of", "and", "for", "on", "with", "at", "by", "from", "that", "this", "it", "as", "are", "was", "be", "has", "its", "or", "not", "but"}
titles = submissions_df["title"].str.lower().str.split()
titles_flat = [word for sublist in titles.dropna() for word in sublist if word.isalpha() and word not in stop_words and len(word) > 2]
word_freq = Counter(titles_flat).most_common(20)
word_freq_df = pd.DataFrame(word_freq, columns=["Word", "Frequency"])
st.bar_chart(word_freq_df.set_index("Word"))
