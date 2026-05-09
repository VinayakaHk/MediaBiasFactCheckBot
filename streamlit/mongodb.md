# mongodb.py (streamlit)

MongoDB data layer for the Streamlit dashboard application.

## Overview

Provides CRUD operations for the dashboard's analytics pages. Connects to MongoDB using the `MONGODB` environment variable. Includes retry logic (10 attempts, 10s delay).

## Functions

### `PrintException()`

Prints detailed exception info for debugging.

### `connect_to_mongo()`

Establishes a MongoDB connection with retries. Creates indexes on success. Exits the process if all attempts fail.

### `create_indexes()`

Creates unique indexes:
- `comments`: compound index on `(comment_id, parent_id)`
- `submissions`: index on `submission_id`

### `store_submission_in_mongo(submission)`

Inserts a submission document if it doesn't already exist (check-then-insert pattern).

### `store_comment_in_mongo(comment)`

Inserts a comment document if it doesn't already exist.

### `store_llm_in_comments(reason, comment_id)`

Updates a comment document with an `ai_removal_reason` field.

### `comment_body(comment_id) -> str | None`

Retrieves the body of the parent comment for a given comment ID. Returns `None` for top-level comments or if the parent isn't found.

## Note

This is a standalone copy of the MongoDB layer used by the Streamlit dashboard, separate from `src/mongodb.py` which uses a singleton pattern.
