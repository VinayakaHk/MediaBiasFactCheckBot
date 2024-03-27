import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pymongo import MongoClient
from collections import Counter
from textblob import TextBlob
import numpy as np

# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    return MongoClient('mongodb://localhost:27017')

client = init_connection()

db = client['reddit']
# Pull data from the collection.
# Uses st.cache_data to only rerun when the query changes or after 10 min.

# Retrieve submissions data from MongoDB
submissions_collection = db['submissions']
submissions_data = list(submissions_collection.find())
submissions_df = pd.DataFrame(submissions_data)

# Convert created column to datetime
submissions_df['created'] = pd.to_datetime(submissions_df['created'], unit='s')

# Submission Analytics Dashboard
st.title('Submission Analytics Dashboard')

# Total number of submissions over time
st.header('Total Submissions Over Time')
submissions_count_over_time = submissions_df.resample('D', on='created').size()
st.line_chart(submissions_count_over_time)

# Distribution of submissions across different subreddits
st.header('Distribution of Submissions Across Subreddits')
subreddit_distribution = submissions_df['subreddit'].value_counts()
st.bar_chart(subreddit_distribution)

# Average number of submissions per user
st.header('Average Submissions Per User')
average_submissions_per_user = len(submissions_df) / submissions_df['author'].nunique()
st.write("Average submissions per user:", round(average_submissions_per_user, 2))

# Most active users based on the number of submissions
st.header('Most Active Users')
most_active_users = submissions_df['author'].value_counts().head(10)
st.write(most_active_users)

# Analysis of submission titles (word frequency)
st.header('Analysis of Submission Titles (Word Frequency)')
titles = submissions_df['title'].str.lower().str.split()
titles_flat = [word for sublist in titles for word in sublist]
word_freq = Counter(titles_flat)
word_freq_df = pd.DataFrame(list(word_freq.items()), columns=['Word', 'Frequency'])
word_freq_df = word_freq_df.sort_values(by='Frequency', ascending=False).reset_index(drop=True)
st.write(word_freq_df.head(10))

# Sentiment analysis of submission titles
st.header('Sentiment Analysis of Submission Titles')
titles_sentiment = submissions_df['title'].apply(lambda x: TextBlob(x).sentiment.polarity)
plt.hist(titles_sentiment, bins=np.arange(-1, 1.1, 0.1), edgecolor='black')
plt.xlabel('Sentiment Polarity')
plt.ylabel('Frequency')
st.pyplot()
