# weekly_discussion.py

Script to create and pin a weekly discussion thread on the subreddit.

## Overview

Generates a discussion post titled "Weekly Discussion Thread - {date}", fetches the latest geopolitical news via Perplexity AI (using Selenium), appends it to the post body, submits it, and pins it to the top of the subreddit.

## Functions

### `create_weekly_discussion()`

1. Initializes a Reddit instance.
2. Builds the post title with the current date.
3. Calls `get_latest_news()` to fetch a news summary.
4. Submits the post as a self-post with replies disabled.
5. Stickies the post to the top of the subreddit.
6. Returns the post URL, or `None` if no news was found.

## Usage

```bash
python weekly_discussion.py
```

Intended to be run on a weekly schedule (e.g., via cron).
