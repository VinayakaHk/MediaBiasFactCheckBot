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

def send_to_modqueue(submission: praw.models.Submission) -> praw.models.ModmailConversation:
    """
    Send a submission to the modqueue and return the modmail message.
    
    Args:
        submission (praw.models.Submission): The submission to be sent to modqueue
    
    Returns:
        praw.models.ModmailConversation: The sent modmail message
    """
    try:
        submission.mod.remove()
        message = submission.mod.send_removal_message(
            message=f"""Your submission has been filtered until you comment a Submission Statement.
    Please add "Submission Statement" or "SS" (without the " ") while writing a submission Statement
    to get your post approved. Make sure it's about 1-2 paragraphs long.
    \n\nIf you need assistance with writing a submission Statement, please refer to https://reddit.com/r/{SUBREDDIT}/wiki/submissionstatement/ ."""
        )
        message.mod.lock()
        return message
    except Exception as e:
        print_exception()

# Add more Reddit-related utility functions here

def get_reply_text(domains, urls, comment=None):
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



def approve_submission(submission, comment=None, is_self=True):
    try:
        submission.mod.approve()
        submission.comments.replace_more(limit=None)
        for top_level_comment in submission.comments:
            if str(top_level_comment.author).lower() == REDDIT_USERNAME.lower():
                top_level_comment.delete()
        if not is_self:
            url = str(submission.url)
            domain = re.search('https?://([A-Za-z_0-9.-]+).*', url).group(1)
            domain = [domain]
            url = [url]
            reply_text = get_reply_text(domain, url, comment)
            reply = submission.reply(body=reply_text)
            reply.mod.distinguish(sticky=True)
            reply.mod.lock()
        else:
            urls = []
            domains = []
            full_text = submission.selftext
            url_pattern = re.compile(r'(https?://[^\]\s)]+)')
            domain_pattern = re.compile(r'https?://([a-zA-Z0-9.-]+)')

            url_matches = url_pattern.findall(full_text)
            domain_matches = domain_pattern.findall(full_text)
            if (domain_matches == []):
                url = str(submission.url)
                domain = re.search(
                    'https?://([A-Za-z_0-9.-]+).*', url).group(1)
                domain = [domain]
                url = [url]
                reply_text = get_reply_text(domain, url, comment)
                reply = submission.reply(body=reply_text)
                reply.mod.distinguish(sticky=True)
                reply.mod.lock()
            else:
                # Extract URLs and domains from the selftext
                for url, domain in zip(url_matches, domain_matches):
                    # Check if the URL is already in the list
                    if url not in urls:
                        urls.append(url)
                        domains.append(domain)
                # Generate reply text using the extracted domains and URLs
                reply_text = get_reply_text(domains, urls, comment)
                reply = submission.reply(body=reply_text)
                reply.mod.distinguish(sticky=True)
                reply.mod.lock()
    except Exception as e:
        print_exception()
        time.sleep(60)


