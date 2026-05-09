# config.py

Centralized configuration loaded from environment variables.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CLIENT_ID` | Reddit app client ID |
| `CLIENT_SECRET` | Reddit app client secret |
| `REDDIT_USERNAME` | Bot's Reddit username |
| `PASSWORD` | Bot's Reddit password |
| `SUBREDDIT` | Target subreddit name |
| `WHITELIST_LLM` | Space-separated list of authors exempt from LLM moderation |

## Constants

| Name | Value | Description |
|------|-------|-------------|
| `MIN_SUBMISSION_STATEMENT_LENGTH` | 150 | Minimum character count for a valid SS |
| `SUBMISSION_STATEMENT_TOO_SHORT` | — | Reply text when SS is too short |
| `SUBMISSION_STATEMENT_FORMAT_INCORRECT` | — | Reply text when SS doesn't start with "SS" |
| `MBFC_JSON_PATH` | `./docs/MBFC_modified.json` | Path to the MBFC ratings data |
