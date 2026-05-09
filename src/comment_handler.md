# comment_handler.py

Monitors the subreddit comment stream and handles SS detection and LLM moderation.

## Functions

### `monitor_comments(subreddit, stop_threads)`

Streams new comments indefinitely. For each comment:
- Stores it in MongoDB.
- Delegates to `handle_comment()`.
- Uses exponential backoff on API errors.

### `handle_comment(comment)`

Processes top-level comments by the submission author:
1. Checks if the submission is in `awaiting_ss` state.
2. If the comment is a valid SS, atomically transitions the submission to `approved` and calls `approve_submission()`.

### `has_submission_statement(comment) -> bool`

Validates the comment as an SS. If invalid:
- Removes the comment and replies with the appropriate error message (too short or wrong format).

### `remove_and_reply(comment, reply_body)`

Removes and locks a comment, then posts a distinguished reply explaining the issue.

### `llm_comment(comment, mod_mail)`

Spawns a background thread to run LLM-based abuse detection on the comment.
