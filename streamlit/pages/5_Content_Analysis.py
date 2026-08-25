import os

import streamlit as st
import pandas as pd
from pymongo import MongoClient
from collections import Counter

st.set_page_config(page_title="Content Analysis - MBFC Bot", page_icon="🔍", layout="wide")

MONGODB_URI = os.environ.get("MONGODB", "mongodb://localhost:27017")


@st.cache_resource
def get_db():
    client = MongoClient(MONGODB_URI)
    return client.reddit


db = get_db()

st.title("🔍 Content Analysis")

submissions_data = list(db["submissions"].find())
comments_data = list(db["comments"].find())

if not submissions_data:
    st.warning("No submissions data found.")
    st.stop()

submissions_df = pd.DataFrame(submissions_data)
comments_df = pd.DataFrame(comments_data) if comments_data else pd.DataFrame()

# Domain analysis
st.subheader("Top Link Domains")
if "domain" in submissions_df.columns:
    domain_counts = submissions_df["domain"].value_counts().head(25)
    st.bar_chart(domain_counts)

st.markdown("---")

# Self-post vs link ratio
st.subheader("Self-Post vs Link Post Ratio")
if "is_self" in submissions_df.columns:
    self_count = submissions_df["is_self"].apply(lambda x: str(x).lower() == "true").sum()
    link_count = len(submissions_df) - self_count
    ratio_df = pd.DataFrame({"Type": ["Self-Post", "Link Post"], "Count": [self_count, link_count]})
    st.bar_chart(ratio_df.set_index("Type"))

st.markdown("---")

# Comment length stats
if not comments_df.empty and "body" in comments_df.columns:
    st.subheader("Comment Length Statistics")
    comments_df["word_count"] = comments_df["body"].apply(lambda x: len(str(x).split()))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Avg Words/Comment", f"{comments_df['word_count'].mean():.0f}")
    with col2:
        st.metric("Median Words", f"{comments_df['word_count'].median():.0f}")
    with col3:
        st.metric("Max Words", f"{comments_df['word_count'].max()}")

st.markdown("---")

# Most frequent words in titles
st.subheader("Most Frequent Title Words")
stop_words = {
    "the", "a", "an", "is", "in", "to", "of", "and", "for", "on", "with",
    "at", "by", "from", "that", "this", "it", "as", "are", "was", "be",
    "has", "its", "or", "not", "but", "india", "indian", "s", "will", "have",
}
titles = submissions_df["title"].str.lower().str.split()
words = [w for sublist in titles.dropna() for w in sublist if w.isalpha() and w not in stop_words and len(w) > 2]
word_freq = Counter(words).most_common(30)
word_df = pd.DataFrame(word_freq, columns=["Word", "Count"])
st.bar_chart(word_df.set_index("Word"))
