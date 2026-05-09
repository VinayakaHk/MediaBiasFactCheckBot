# modmail_handler.py

Extracts URLs from modmail conversations.

## Functions

### `extract_moderator_links(reddit, conversation_id, subreddit) -> str | list`

Fetches a modmail conversation and extracts URLs from the last message.

- Ignores messages from the bot account (`GeoIndModBot`).
- Returns the first URL found, or an empty list if none.

## Parameters

| Param | Type | Description |
|-------|------|-------------|
| `reddit` | `praw.Reddit` | Authenticated Reddit instance |
| `conversation_id` | `str` | Modmail conversation ID |
| `subreddit` | `str` | Subreddit name |
