# llmapi.py

Google Gemini-based LLM moderation API for the Streamlit dashboard.

## Overview

Uses the `google.generativeai` SDK to evaluate whether a Reddit comment violates subreddit Rule 2 (no verbal abuse/personal attacks). Returns a JSON object with a probability score (0–92) and a reason.

## Configuration

- Model: `llm-pro` (Gemini)
- Temperature: 0.9
- Safety thresholds: `BLOCK_ONLY_HIGH` for all categories
- API key loaded from `llm` environment variable

## Functions

### `PrintException()`

Prints detailed exception info (file, line, expression) for debugging.

### `convert_quotes(obj)`

Replaces double quotes with single quotes in strings (for JSON safety).

### `llm_detection(input_string, parent_comment, link_title) -> dict`

Sends a prompt to Gemini asking it to rate the comment's rule violation probability.

**Returns:**
```json
{"answer": "0-92", "reason": "explanation"}
```

**Logic:**
- If the response is blocked by safety filters → returns `answer: 100` (extremely toxic).
- If safety ratings contain `HIGH` → returns `answer: 100`.
- Otherwise, parses the JSON response from the model output.
- Returns `{"answer": "0", "reason": "API ERROR"}` on parse failures.
- Retries indefinitely on API exceptions with 2s delay.
