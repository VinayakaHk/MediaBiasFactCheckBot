import praw
import re
import time
import os
from src.config import CLIENT_ID, CLIENT_SECRET, USER_AGENT, REDDIT_USERNAME, PASSWORD
from src.exceptions import print_exception
from src.config import SUBREDDIT
from src.utils import add_prefix_to_paragraphs
from src.utils import mbfc_political_bias

def initialize_reddit() -> praw.Reddit:
    """
    Initialize and return a Reddit instance using environment variables.
    
    Returns:
        praw.Reddit: Initialized Reddit instance
    """
    return praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        user_agent=USER_AGENT,
        username=REDDIT_USERNAME,
        password=PASSWORD,
        check_for_async=False
    )


def fetchDomainsandUrls(submission: praw.models.Submission, is_self: bool, comment: praw.models.Comment = None):
    """
    Extract domains and URLs from a submission's content.

    Args:
        submission (praw.models.Submission): The submission to extract content from
        is_self (bool): Whether the submission is a self-post
        comment (praw.models.Comment): Optional comment to analyze

    Returns:
        tuple: A tuple containing a list of unique URLs and a list of corresponding domains
    """
    try:
        urls = []
        domains = []

        full_text = submission.selftext if is_self else str(submission.url)

        # Find all URLs
        url_pattern = re.compile(r'https?://[^\s"\'<>]+')
        url_matches = url_pattern.findall(full_text)

        # Deduplicate and clean URLs
        seen = set()
        for url in url_matches:
            if url not in seen:
                seen.add(url)
                urls.append(url)
                match = re.search(r'https?://([a-zA-Z0-9.-]+)', url)
                if match:
                    domains.append(match.group(1))

        return urls, domains

    except Exception as e:
        print_exception()
        time.sleep(60)
        return [], []

def send_to_modqueue(submission: praw.models.Submission, is_self: bool) -> praw.models.ModmailConversation:
    """
    Send a submission to the modqueue and return the modmail message.
    """
    try:
        submission.mod.remove()
        urls, domains = fetchDomainsandUrls(submission, is_self)
        removal_message = f"""Your submission has been filtered until you comment a Submission Statement. 
Please add "Submission Statement" or "SS" (without the " ") while writing a submission Statement to get your post approved. 
Make sure it's about 1-2 paragraphs long. \n\n
If you need assistance with writing a submission Statement, please refer to https://reddit.com/r/{SUBREDDIT}/wiki/submissionstatement/ ."""

        if urls:
            removal_message += f"""\n\n
If you dont have access to the complete article, you can try the below links:\n\n
"""
            for index, url in enumerate(urls):
                removal_message += f"""* [{domains[index]}](https://archive.is/submit/?submitid=&url={url})"""

        message = submission.mod.send_removal_message(message=removal_message)
        message.mod.lock()
        message.mod.distinguish(sticky=True)
        message.mod.approve()
        return message
    except Exception as e:
        print_exception()

def get_reply_text(domains, urls, comment=None):
    """
    Generate reply text with archive links and submission statement.
    """
    try:
        archive_links = f"""\n\n🔗 **Bypass paywalls**:\n\n"""
        for index, url in enumerate(urls):
            archive_links += f"""* [{domains[index]}](https://archive.is/submit/?submitid=&url={url})"""
        formatted_string = add_prefix_to_paragraphs(
            comment.body) if comment else ""

        submission_statement = f"""📣 **[Submission Statement by OP]({comment.permalink})**:\n> {formatted_string}""" if comment else ""

        base_text = f"""{archive_links}\n\n{submission_statement} \n\n**📜 Community Reminder**: Let’s keep our discussions civil, respectful, and on-topic. Abide by the subreddit rules. Rule-violating comments will be removed."""
        domains = list(set(domains))
        for domain in domains:
            if domain:
                additional_text = mbfc_political_bias(domain)
                if additional_text:
                    base_text += "\n\n" + additional_text

        footer = f"""\n\n❓ Questions or concerns? [Contact our moderators](https://www.reddit.com/message/compose/?to=/r/{os.environ.get('SUBREDDIT')})."""

        return base_text + footer
    except Exception as e:
        print('Exception occurred trying to create submission statement: ', e)

def create_sticky_reply(submission, reply_text):
    """
    Create and configure a sticky reply on the submission.
    """
    reply = submission.reply(body=reply_text)
    reply.mod.distinguish(sticky=True)
    reply.mod.lock()
    reply.mod.approve()
    return reply

def approve_submission(submission, comment=None, is_self=True):
    """
    Approve a submission and handle the reply creation.
    """
    try:
        submission.mod.approve()
        if comment:
            comment.mod.approve()

        # Remove existing bot comments
        submission.comments.replace_more(limit=None)
        for bot_comment in submission.comments:
            if str(bot_comment.author).lower() == REDDIT_USERNAME.lower():
                bot_comment.delete()

        # Get URLs and domains
        urls, domains = fetchDomainsandUrls(submission, is_self)
        
        # If no URLs found in self text, use submission URL
        if is_self and not domains:
            url = str(submission.url)
            domain = re.search('https?://([A-Za-z_0-9.-]+).*', url).group(1)
            urls = [url]
            domains = [domain]

        # Create and configure reply
        reply_text = get_reply_text(domains, urls, comment)
        create_sticky_reply(submission, reply_text)

    except Exception as e:
        print_exception()
        time.sleep(60)


