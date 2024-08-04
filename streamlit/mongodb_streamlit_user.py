import streamlit as st
import pandas as pd
from pymongo import MongoClient
import matplotlib.pyplot as plt

# Connect to MongoDB
client = MongoClient('mongodb://username:password@localhost:27017/')
db = client['your_database']

# Function to retrieve user behavior data
def get_user_behavior(user_name):
    submissions_collection = db['submissions']
    comments_collection = db['comments']
    
    # Retrieve user submission data
    submissions_data = list(submissions_collection.find({'author': user_name}, {'created': 1}))
    submissions_df = pd.DataFrame(submissions_data)
    submissions_df['created'] = pd.to_datetime(submissions_df['created'])
    submissions_df['type'] = 'Submission'
    
    # Retrieve user comment data
    comments_data = list(comments_collection.find({'author': user_name}, {'created_utc': 1}))
    comments_df = pd.DataFrame(comments_data)
    comments_df['created_utc'] = pd.to_datetime(comments_df['created_utc'], unit='s')
    comments_df['type'] = 'Comment'
    
    # Combine submission and comment data
    user_behavior_df = pd.concat([submissions_df, comments_df])
    user_behavior_df.set_index('created', inplace=True)
    user_behavior_df.sort_index(inplace=True)
    return user_behavior_df

# Streamlit app
st.title('User Behavior Analysis')

# Get user input for username
user_name = st.text_input('Enter username:', 'your_username')

# Retrieve user behavior data
user_behavior_df = get_user_behavior(user_name)

# Plot user posting/commenting frequency over time
st.subheader('User Posting/Commenting Frequency Over Time')
if not user_behavior_df.empty:
    st.line_chart(user_behavior_df.resample('D').size())
else:
    st.write('No data available for the specified user.')

# Identify user behavior patterns
st.subheader('User Behavior Patterns')
if not user_behavior_df.empty:
    st.write('Peak posting/commenting hours:', user_behavior_df.groupby(user_behavior_df.index.hour).size().idxmax())
else:
    st.write('No data available for the specified user.')

# Analysis of user interaction with different types of content
st.subheader('User Interaction with Different Types of Content')
if not user_behavior_df.empty:
    st.write(user_behavior_df['type'].value_counts())
else:
    st.write('No data available for the specified user.')
