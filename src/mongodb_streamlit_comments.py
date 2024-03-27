import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pymongo import MongoClient
from collections import Counter
from textblob import TextBlob

# Connect to MongoDB
client = MongoClient('mongodb://username:password@localhost:27017/')
db = client['your_database']

# Retrieve comments data from MongoDB
comments_collection = db['comments']
comments_data = list(comments_collection.find())
comments_df = pd.DataFrame(comments_data)

# Convert created_utc column to datetime
comments_df['created_utc'] = pd.to_datetime(comments_df['created_utc'])

# Comment Analytics Dashboard
st.title('Comment Analytics Dashboard')

# Total number of comments over time
st.header('Total Comments Over Time')
comments_count_over_time = comments_df.resample('D', on='created_utc').size()
st.line_chart(comments_count_over_time)

# Distribution of comments across different subreddits
st.header('Distribution of Comments Across Subreddits')
subreddit_distribution = comments_df['subreddit'].value_counts()
st.bar_chart(subreddit_distribution)

# Average number of comments per user
st.header('Average Comments Per User')
average_comments_per_user = len(comments_df) / comments_df['author'].nunique()
st.write("Average comments per user:", round(average_comments_per_user, 2))

# Most active users based on the number of comments
st.header('Most Active Users')
most_active_users = comments_df['author'].value_counts().head(10)
st.write(most_active_users)

# Analysis of comment sentiment over time
st.header('Analysis of Comment Sentiment Over Time')

# Function to calculate sentiment polarity of comments
def calculate_sentiment(text):
    return TextBlob(text).sentiment.polarity

# Apply sentiment analysis to comments
comments_df['sentiment'] = comments_df['body'].apply(calculate_sentiment)

# Group sentiment by date and calculate average sentiment polarity
sentiment_over_time = comments_df.groupby(comments_df['created_utc'].dt.date)['sentiment'].mean()

# Plot sentiment over time
st.line_chart(sentiment_over_time)

