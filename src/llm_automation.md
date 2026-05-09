# llm_automation.py

Selenium-based LLM abuse detection for comments.

## Overview

Uses a headless Chrome browser to query Perplexity AI, asking whether a comment violates Rule 2 (no verbal abuse/personal attacks). Based on the response, it may auto-remove the comment.

## Constants

| Name | Value | Description |
|------|-------|-------------|
| `MAX_RETRIES` | 3 | Browser launch retry attempts |
| `RETRY_DELAY` | 2 | Seconds between retries |

## Functions

### `element_strip(elem)`

Returns the stripped text content of a Selenium WebElement.

### `llm_detection(comment, mod_mail, parent_comment)`

1. Launches Chrome (with Xvfb on Linux/aarch64).
2. Navigates to Perplexity AI with a prompt asking if the comment violates Rule 2.
3. Waits for the `.prose` elements to load.
4. Parses the response:
   - If starts with `"True."` → removes the comment, sends a removal message, and saves.
   - If starts with `"False"` → saves the comment (no action).
5. Stores the LLM result in MongoDB via `store_llm_in_comments()`.

## Notes

- Only removes top-level comments automatically; nested rule-breaking comments are flagged but not removed.
- The function is designed to run in a background thread (spawned by `comment_handler.llm_comment()`).
