# submission_handler.py

Monitors the subreddit submission stream and enforces SS requirements.

## Functions

### `monitor_submission(subreddit, stop_threads)`

Streams new submissions indefinitely. For each submission:
- Stores it in MongoDB.
- Auto-approves AutoModerator posts.
- Delegates non-approved posts to `handle_new_submission()`.
- Uses exponential backoff on API errors.

### `handle_new_submission(submission)`

Processes a new submission through the state machine:
1. Initializes state in MongoDB (`pending_review`).
2. If it's a long self-post (>200 chars), auto-approves without requiring an SS.
3. Otherwise, removes the post (sends to modqueue) and transitions to `awaiting_ss`.
4. Scans existing comments in case an SS was posted before the bot processed the submission.

### `scan_existing_comments_for_ss(submission)`

Checks all top-level comments by OP for a valid submission statement. Returns the matching comment or `None`.
