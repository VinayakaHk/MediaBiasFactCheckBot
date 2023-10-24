# MediaBiasFactCheckBot
Reddit bot for Media bias Fact Check

## Overview
This script (`main.py`) is designed to monitor a specified subreddit for new submissions and comments, with the primary goal of ensuring that every submission has an accompanying "Submission Statement" in its comments. If a submission lacks a valid submission statement, it is automatically moved to the modqueue until a valid statement is added.

## Dependencies
- `praw`: The Python Reddit API Wrapper, used to interact with Reddit.
- `time`: Provides various time-related functions.
- `multiprocessing`: Enables the use of multiple processes.
- `dotenv`: Loads environment variables from a .env file.
- `os`: Provides a way of using operating system dependent functionality.
- `re`: Provides regular expression matching operations.
- `json`: Used for encoding and decoding JSON data.
- `linecache`: Used for random access to text lines.
- `sys`: Provides access to some variables used or maintained by the interpreter.

Make sure to install these dependencies using pip:
```
pip install praw python-dotenv
```

## Environment Variables
The script requires several environment variables for functionality:
- `CLIENT_ID`: Your Reddit app's client ID.
- `CLIENT_SECRET`: Your Reddit app's client secret.
- `REDDIT_USERNAME`: Your Reddit bot's username.
- `PASSWORD`: Your Reddit bot's password.
- `SUBREDDIT`: The subreddit you want to monitor.

Store these in a `.env` file in the same directory as `main.py`.

## Features & Functions
1. **Initialization**: The script initializes the PRAW instance with the provided environment variables and selects the desired subreddit for monitoring.
2. **Exception Printing**: `PrintException()` prints details about the exceptions, aiding in debugging.
3. **MBFC Rating**: `mbfc_political_bias()` provides the Media Bias Fact Check rating for a given domain. This data is read from an external `MBFC.json` file.
4. **Submission Statements**: The script checks for a valid "Submission Statement" (or "SS") in the comments of each submission. A valid statement must start with "SS" or "Submission Statement" and be at least 150 characters long.
5. **Monitoring**: The script continuously monitors for new submissions and comments on the subreddit. If a submission doesn't have a valid submission statement, it's sent to the modqueue.
6. **Multiprocessing**: The script uses multiple processes to monitor both submissions and comments simultaneously.

## How to Run
1. Make sure you have all the dependencies installed.
2. Fill in the `.env` file with the necessary environment variables.
3. Run the script:
```
python main.py
```
4. The script will start monitoring the specified subreddit. It will send posts to the modqueue if they lack a valid submission statement. When a valid statement is added, the post will be approved.

## Notes
- Ensure your bot account has the necessary permissions in the subreddit you're monitoring.

Remember to always follow Reddit's bot guidelines and terms of service when operating the bot.
