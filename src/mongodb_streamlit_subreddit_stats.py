import streamlit as st
import pandas as pd
from pymongo import MongoClient
import matplotlib.pyplot as plt

# Connect to MongoDB
client = MongoClient('mongodb://username:password@localhost:27017/')
db = client['your_database']

# Function to retrieve subreddit growth data
def get_subreddit_growth(subreddit_name):
    collection = db['submissions']
    subreddit_data = list(collection.find({'subreddit': subreddit_name}, {'created': 1, 'subreddit_subscribers': 1}))
    subreddit_df = pd.DataFrame(subreddit_data)
    subreddit_df['created'] = pd.to_datetime(subreddit_df['created'])
    subreddit_df.set_index('created', inplace=True)
    subreddit_df.sort_index(inplace=True)
    return subreddit_df

# Streamlit app
st.title('Subreddit Growth Trends')

# Get user input for subreddit name
subreddit_name = st.text_input('Enter subreddit name:', 'your_subreddit')

# Retrieve subreddit growth data
subreddit_df = get_subreddit_growth(subreddit_name)

# Plot subreddit growth over time
st.subheader('Subreddit Growth Over Time')
if not subreddit_df.empty:
    st.line_chart(subreddit_df['subreddit_subscribers'])
else:
    st.write('No data available for the specified subreddit.')
