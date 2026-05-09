# utils.py

Shared utility functions.

## Functions

### `exponential_backoff(attempt, max_wait=300)`

Sleeps with exponential backoff plus jitter, capped at `max_wait` seconds. Returns the wait time used.

### `add_prefix_to_paragraphs(input_string)`

Formats a string with Reddit blockquote prefixes (`>`) for embedding in bot replies.

### `print_mbfc_text(domain, obj)`

Generates a Markdown table with Media Bias Fact Check ratings (bias, factual, credibility) for a given source.

### `is_valid_submission_statement(body) -> bool`

Single source of truth for SS validation. Returns `True` if the comment body starts with "SS" or "Submission Statement" (case-insensitive) and exceeds `MIN_SUBMISSION_STATEMENT_LENGTH`.

### `mbfc_political_bias(domain_url)`

Looks up a domain in the MBFC JSON index (LRU-cached) and returns formatted rating text, or `None` if not found.
