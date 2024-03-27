import streamlit as st
from pymongo import MongoClient
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Connect to MongoDB
client = MongoClient('mongodb://username:password@localhost:27017/')
db = client['your_database']

# Retrieve data from MongoDB collections
def get_data(collection_name):
    collection = db[collection_name]
    data = list(collection.find())
    return data

submissions_data = get_data('submissions')
comments_data = get_data('comments')

# Convert data to DataFrames
submissions_df = pd.DataFrame(submissions_data)
comments_df = pd.DataFrame(comments_data)

# User Engagement Analytics

# Correlation between submissions and comments
submissions_comments_corr = submissions_df['num_comments'].corr(comments_df['link_id'].value_counts())

# Analysis of user engagement patterns
user_engagement_patterns = comments_df.groupby(['author', 'subreddit'])['comment_id'].count().reset_index()
user_engagement_patterns = user_engagement_patterns.rename(columns={'comment_id': 'comment_count'})

# Identification of power users
power_users = pd.concat([submissions_df['author'], comments_df['author']]).value_counts().reset_index()
power_users.columns = ['author', 'activity_count']

# Streamlit app
st.title('User Engagement Analytics Dashboard')

# Correlation between submissions and comments
st.header('Correlation between Submissions and Comments')
st.write(f"Correlation coefficient: {submissions_comments_corr}")

# Analysis of user engagement patterns
st.header('User Engagement Patterns')
st.write(user_engagement_patterns)

# Identification of power users
st.header('Power Users')
st.write(power_users)
