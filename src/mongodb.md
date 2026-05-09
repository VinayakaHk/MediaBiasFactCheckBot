# mongodb.py

MongoDB data layer with a thread-safe singleton connection and submission state machine.

## Connection

Uses a singleton `MongoDB` class with thread-safe initialization. Retries connection up to 10 times with 10s delays. Creates indexes on first connect.

## Collections & Indexes

| Collection | Index | Unique |
|------------|-------|--------|
| `comments` | `(comment_id DESC, parent_id DESC)` | Yes |
| `submissions` | `(submission_id DESC)` | Yes |
| `submission_state` | `(submission_id DESC)` | Yes |
| `submission_state` | `(state DESC, updated_at DESC)` | No |

## Submission State Machine

States: `pending_review` → `awaiting_ss` → `approved`

Transitions are atomic (MongoDB `update_one` with state precondition) to prevent race conditions between threads.

## Class: `MongoDB`

### `store_comment(comment)`
Upserts a Reddit comment document (insert-only semantics via `$setOnInsert`).

### `store_submission(submission)`
Upserts a Reddit submission document.

### `store_llm_in_comments(reason, comment_id)`
Attaches an `ai_removal_reason` field to an existing comment.

### `get_comment_body(comment_id)`
Returns the body of the parent comment (for LLM context). Returns `None` for top-level comments.

### `init_submission_state(submission_id)`
Creates the initial `pending_review` state. Returns the current state document.

### `transition_to_awaiting_ss(submission_id)`
Atomic transition: `pending_review` → `awaiting_ss`.

### `transition_to_approved(submission_id, ss_comment_id=None)`
Atomic transition: `pending_review|awaiting_ss` → `approved`.

### `get_submission_state(submission_id)`
Returns the state document for a submission.

### `get_stale_awaiting_ss(max_age_seconds=300)`
Finds submissions stuck in `awaiting_ss` longer than the threshold (used by retry sweep).

## Module-Level Functions

Convenience wrappers (`store_comment_in_mongo`, `store_submission_in_mongo`, etc.) that lazily initialize the singleton and delegate to it.
