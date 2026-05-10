"""Fetches the latest geopolitical news summary from Perplexity AI."""

from src.perplexity import query_perplexity


def get_latest_news():
    return query_perplexity(
        "What are the latest geopolitical news this week? Make it region wise. Do not ask any more follow up questions."
    )
