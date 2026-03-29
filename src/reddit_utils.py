import praw
import re
import time
import os
from src.config import CLIENT_ID, CLIENT_SECRET, USER_AGENT, REDDIT_USERNAME, PASSWORD, SUBREDDIT
from src.exceptions import logger
from src.utils import add_prefix_to_paragraphs, mbfc_political_bias


def initialize_reddit() -> praw.Reddit:
    return praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        user_agent=USER_AGENT,
        username=REDDIT_USERNAME,
        password=PASSWORD,
        check_for_async=False
    )


def fetchDomainsandUrls(submission: praw.models.Submission, is_self: bool):
    try:
        urls = []
        domains = []
        full_text = submission.selftext if is_self else str(submission.url)

        url_pattern = re.compile(r'https?://[^\s"\'<>]+')
        seen = set()
        for url in url_pattern.findall(full_text):
            if url not in seen:
                seen.add(url)
                urls.append(url)
                match = re.search(r'https?://([a-zA-Z0-9.-]+)', url)
                if match:
                    domains.append(match.group(1))

        return urls, domains
    except Exception:
        logger.exception("Error extracting URLs from submission")
        return [], []


def send_to_modqueue(submission: praw.models.Submission, is_self: bool):
    try:
        submission.mod.remove()
        urls, domains = fetchDomainsandUrls(submission, is_self)
        removal_message = f"""Your submission has been filtered until you comment a Submission Statement. 
Please add "Submission Statement" or "SS" (without the " ") while writing a submission Statement to get your post approved. 
Make sure it's about 1-2 paragraphs long. \n\n
If you need assistance with writing a submission Statement, please refer to https://reddit.com/r/{SUBREDDIT}/wiki/submissionstatement/ ."""

        if urls:
            removal_message += "\n\nIf you dont have access to the complete article, you can try the below links:\n\n"
            for index, url in enumerate(urls):
                removal_message += f"* [{domains[index]}](https://unwall.app/{url})"

        message = submission.mod.send_removal_message(message=removal_message)
        message.mod.lock()
        message.mod.distinguish(sticky=True)
        message.mod.approve()
        return message
    except Exception:
        logger.exception("Error sending submission to modqueue")


def get_reply_text(domains, urls, comment=None):
    try:
        archive_links = "\n\n🔗 **Bypass paywalls**:\n\n"
        for index, url in enumerate(urls):
            archive_links += f"* [{domains[index]}](https://unwall.app/{url})"

        formatted_string = add_prefix_to_paragraphs(comment.body) if comment else ""
        submission_statement = f'📣 **[Submission Statement by OP]({comment.permalink})**:\n> {formatted_string}' if comment else ""

        base_text = f"""{archive_links}\n\n{submission_statement} \n\n**📜 Community Reminder**: Let's keep our discussions civil, respectful, and on-topic. Abide by the subreddit rules. Rule-violating comments will be removed."""

        for domain in set(domains):
            if domain:
                additional_text = mbfc_political_bias(domain)
                if additional_text:
                    base_text += "\n\n" + additional_text

        footer = f"\n\n❓ Questions or concerns? [Contact our moderators](https://www.reddit.com/message/compose/?to=/r/{SUBREDDIT})."
        return base_text + footer
    except Exception:
        logger.exception("Error creating reply text")
        return ""


def create_sticky_reply(submission, reply_text):
    reply = submission.reply(body=reply_text)
    reply.mod.distinguish(sticky=True)
    reply.mod.lock()
    reply.mod.approve()
    return reply


def approve_submission(submission, comment=None, is_self=True):
    try:
        submission.mod.approve()
        if comment:
            comment.mod.approve()

        submission.comments.replace_more(limit=None)
        for bot_comment in submission.comments:
            if str(bot_comment.author).lower() == REDDIT_USERNAME.lower():
                bot_comment.delete()

        urls, domains = fetchDomainsandUrls(submission, is_self)

        if is_self and not domains:
            url = str(submission.url)
            match = re.search(r'https?://([A-Za-z_0-9.-]+).*', url)
            if match:
                urls = [url]
                domains = [match.group(1)]

        reply_text = get_reply_text(domains, urls, comment)
        create_sticky_reply(submission, reply_text)
    except Exception:
        logger.exception("Error approving submission")
        time.sleep(60)
