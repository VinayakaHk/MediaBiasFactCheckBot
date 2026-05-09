# get_latest_news.py

Fetches the latest geopolitical news summary using Selenium and Perplexity AI.

## Overview

Automates a browser to query Perplexity AI for region-wise geopolitical news, extracts the HTML response, converts it to Markdown, and formats citations for Reddit.

## Constants

| Name | Value | Description |
|------|-------|-------------|
| `MAX_RETRIES` | 10 | Browser launch retry attempts |
| `RETRY_DELAY` | 10 | Seconds between retries |

## Functions

### `element_strip(elem)`

Returns stripped text from a Selenium WebElement.

### `format_for_reddit(answer)`

Converts citation links from `[number](url)` format to `[[domain]](url)` for cleaner Reddit display.

### `get_latest_news() -> str`

1. Launches Firefox (macOS) or undetected Chrome (Linux).
2. Navigates to Perplexity AI with a geopolitical news query.
3. Waits for the "Related" section to confirm page load.
4. Extracts `.prose` elements and converts innerHTML to Markdown via `markdownify`.
5. Formats citations for Reddit.
6. Returns the formatted news string, or empty string on failure.

## Platform Handling

- **macOS**: Uses Firefox via geckodriver at `/opt/homebrew/bin/geckodriver`.
- **Linux (aarch64)**: Uses undetected-chromedriver with Xvfb virtual display.
