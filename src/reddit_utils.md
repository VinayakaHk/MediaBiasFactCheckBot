# reddit_utils.py

Reddit API interaction utilities using PRAW.

## Functions

### `initialize_reddit() -> praw.Reddit`

Creates and returns an authenticated Reddit instance using credentials from `config.py`.

### `fetchDomainsandUrls(submission, is_self)`

Extracts all unique URLs and their domains from a submission's selftext (or URL for link posts). Returns `(urls, domains)`.

### `send_to_modqueue(submission, is_self)`

Removes a submission and sends a removal message instructing the author to add a Submission Statement. Includes archive.is bypass links for any URLs found.

### `get_reply_text(domains, urls, comment=None)`

Builds the bot's sticky reply containing:
- Archive/paywall bypass links
- Quoted Submission Statement (if provided)
- MBFC ratings for each domain
- Community reminder and mod contact link

### `create_sticky_reply(submission, reply_text)`

Posts a distinguished, stickied, locked reply on the submission.

### `approve_submission(submission, comment=None, is_self=True)`

Approves the submission, deletes previous bot comments, extracts domains, and posts the final sticky reply with MBFC ratings and the SS quote.
