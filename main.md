# main.py

Entry point for the MediaBiasFactCheckBot Reddit bot.

## Overview

Launches three daemon threads to monitor a subreddit in real-time:

1. **Submission monitor** — watches for new posts and enforces submission statement requirements.
2. **Comment monitor** — watches for new comments and approves posts when a valid SS is detected.
3. **Retry sweep** — periodically re-checks submissions stuck in `awaiting_ss` state for missed SS comments.

## Constants

| Name | Value | Description |
|------|-------|-------------|
| `SWEEP_INTERVAL` | 120s | Seconds between retry sweep iterations |
| `STALE_THRESHOLD` | 300s | Submissions in `awaiting_ss` longer than this are re-scanned |

## Functions

### `retry_sweep(reddit, stop_threads)`

Periodically queries MongoDB for submissions stuck in `awaiting_ss` beyond `STALE_THRESHOLD`. For each stale submission, it fetches comments and approves the post if a valid SS is found.

### `main()`

Initializes the Reddit instance, spawns the three monitoring threads as daemons, and blocks on `signal.pause()` until interrupted.

## Usage

```bash
python main.py
```

Requires `.env` file with Reddit API credentials and `SUBREDDIT` configured.
