# Streamlit Dashboard Pages

## mongodb_streamlit_user.py

**User Behavior Analysis** dashboard.

- Queries submissions and comments by username.
- Plots posting/commenting frequency over time (daily resampled line chart).
- Identifies peak activity hours.
- Shows breakdown of submissions vs. comments.

---

## mongodb_streamlit_subreddit_stats.py

**Subreddit Growth Trends** dashboard.

- Plots `subreddit_subscribers` over time from the submissions collection.
- Shows growth trajectory as a line chart.

---

## mongodb_streamlit_submissions.py

**Submission Analytics Dashboard**.

- Total submissions over time (daily line chart).
- Distribution across subreddits (bar chart).
- Average submissions per user.
- Top 10 most active users.
- Word frequency analysis of submission titles.
- Sentiment analysis of titles using TextBlob.

---

## mongodb_streamlit_comments.py

**Comment Analytics Dashboard**.

- Total comments over time (daily line chart).
- Distribution across subreddits (bar chart).
- Average comments per user.
- Top 10 most active commenters.
- Sentiment polarity trend over time using TextBlob.

---

## mongodb_streamlit_user_analytics.py

**User Engagement Analytics Dashboard**.

- User engagement patterns: comment counts grouped by author and subreddit.
- Power users: combined submission + comment activity ranking.

---

## mongodb_streamlit_content_analysis.py

**Content Analysis Dashboard**.

- Submission domain analysis (bar chart of most common domains).
- Submission type distribution (self-post vs. external link pie chart).
- Comment length distribution (histogram).
- Most frequently used words in submissions and comments (NLTK tokenization with stopword removal).
