import streamlit as st
from pymongo import MongoClient
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk
nltk.download('punkt')
nltk.download('stopwords')

# Connect to MongoDB
client = MongoClient('mongodb://username:password@localhost:27017/')
db = client['your_database']

# Retrieve submissions and comments data from MongoDB collections
submissions_collection = db['submissions']
comments_collection = db['comments']

submissions_data = list(submissions_collection.find())
comments_data = list(comments_collection.find())

# Convert data to DataFrames for easier manipulation
submissions_df = pd.DataFrame(submissions_data)
comments_df = pd.DataFrame(comments_data)

# Content Analysis Functions
def submission_domain_analysis(submissions_df):
    domain_counts = submissions_df['domain'].value_counts()
    return domain_counts

def submission_type_distribution(submissions_df):
    submission_types = submissions_df['is_self'].replace({'True': 'Self-Post', 'False': 'External Link'}).value_counts()
    return submission_types

def comment_length_distribution(comments_df):
    comments_df['comment_length'] = comments_df['body'].apply(lambda x: len(x.split()))
    return comments_df['comment_length']

def most_frequent_words(texts):
    stop_words = set(stopwords.words('english'))
    words = ' '.join(texts)
    tokens = word_tokenize(words)
    filtered_tokens = [word.lower() for word in tokens if word.isalnum() and word.lower() not in stop_words]
    word_freq = Counter(filtered_tokens)
    return word_freq.most_common(10)

# Streamlit app
st.title('Content Analysis Dashboard')

# Submission Domain Analysis
st.header('Submission Domain Analysis')
domain_counts = submission_domain_analysis(submissions_df)
st.bar_chart(domain_counts)

# Submission Type Distribution
st.header('Submission Type Distribution')
submission_types = submission_type_distribution(submissions_df)
st.pie_chart(submission_types)

# Comment Length Distribution
st.header('Comment Length Distribution')
comment_lengths = comment_length_distribution(comments_df)
st.hist(comment_lengths, bins=20)

# Most Frequently Used Words in Submissions and Comments
st.header('Most Frequently Used Words')
submission_words = most_frequent_words(submissions_df['title'])
comment_words = most_frequent_words(comments_df['body'])
st.subheader('Most Frequently Used Words in Submissions')
st.write(submission_words)
st.subheader('Most Frequently Used Words in Comments')
st.write(comment_words)
