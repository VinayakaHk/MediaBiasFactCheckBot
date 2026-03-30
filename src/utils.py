import re
import json
import random
import time
from functools import lru_cache
from src.exceptions import logger
from src.config import MBFC_JSON_PATH

MAX_BACKOFF = 300  # 5 minute cap


def exponential_backoff(attempt, max_wait=MAX_BACKOFF):
    """Sleep with exponential backoff + jitter. Returns the wait time used."""
    wait = min(2 ** attempt, max_wait) + random.uniform(0, 1)
    logger.info(f"Backing off for {wait:.1f}s (attempt {attempt + 1})")
    time.sleep(wait)
    return wait


def add_prefix_to_paragraphs(input_string):
    try:
        formatted_string = re.sub(r'\n+', '\n>\n>', input_string)
        formatted_string = re.sub(r'(?<=\n\n)(?=[^\n])', "> ", formatted_string)
        return formatted_string
    except Exception:
        logger.exception("Failed to format paragraphs")
        return input_string


def print_mbfc_text(domain, obj):
    text = f"""\n\n**📰 Media Bias fact Check Rating :**  {obj['name']} \n\n\n\n
|Metric|Rating|
|:-|:-|
|Bias Rating|{obj['bias']}|
|Factual Rating| {obj['factual']}|
"""
    credibility = obj.get("credibility", "no credibility rating available")
    if credibility != "no credibility rating available":
        text += f"|Credibility Rating|{obj['credibility']}|\n"

    text += f"""\nThis rating was provided by Media Bias Fact Check. For more information, see {obj['name']}'s review 
[here]({obj['profile']}).
***"""
    return text


@lru_cache(maxsize=1)
def _load_mbfc_data():
    with open(MBFC_JSON_PATH, 'r') as f:
        data = json.load(f)
    return {entry["url"]: entry for entry in data}


def is_valid_submission_statement(body: str) -> bool:
    """Single source of truth for SS validation."""
    from src.config import MIN_SUBMISSION_STATEMENT_LENGTH
    lower = body.lower()
    return (lower.startswith("submission statement") or lower.startswith("ss")) \
        and len(body) > MIN_SUBMISSION_STATEMENT_LENGTH


def mbfc_political_bias(domain_url):
    try:
        index = _load_mbfc_data()
        entry = index.get(domain_url)
        if entry:
            return print_mbfc_text(entry['url'], entry)
        logger.info(f"URL not found in MBFC index: {domain_url}")
        return None
    except Exception:
        logger.exception("Failed to look up MBFC data")
        return None
