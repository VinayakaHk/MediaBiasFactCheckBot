from pymongo.errors import ConnectionFailure, PyMongoError
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

import os
import sys
import linecache
import time
import praw
import certifi
import ssl
load_dotenv()


MAX_RETRIES = 10
RETRY_DELAY = 10

print(certifi.where())


def store_submission_in_mongo(mongo_db, submission):
    if submission.removed or submission.author is None:
        # Skip 'removed' submissions or submissions without an author
        return

    submissions_collection = mongo_db['submissions']
    submissions_collection.insert_one({
        'approved': submission.approved,
        'approved_at_utc': submission.approved_at_utc,
        'approved_by': submission.approved_by,
        'archived': submission.archived,
        '_author': submission.author,
        'created': submission.created,
        'distinguished': submission.distinguished,
        'downs': submission.downs,
        'domain': submission.domain,
        'id': submission.id,
        'is_reddit_media_domain': submission.is_reddit_media_domain,
        'is_self': submission.is_self,
        'is_video': submission.is_video,
        'locked': submission.locked,
        'mod_note': submission.mod_note,
        'mod_reason_by': submission.mod_reason_by,
        'mod_reason_title': submission.mod_reason_title,
        'mod_reports': submission.mod_reports,
        'name': submission.name,
        'num_comments': submission.num_comments,
        'num_reports': submission.num_reports,
        'over_18': submission.over_18,
        'permalink': submission.permalink,
        'pinned': submission.pinned,
        'post_hint': submission.post_hint,
        'removal_reason': submission.removal_reason,
        'removed': submission.removed,
        'removed_by': submission.removed_by,
        'removed_by_category': submission.removed_by_category,
        'report_reasons': submission.report_reasons,
        'selftext': submission.selftext,
        'send_replies': submission.send_replies,
        'spam': submission.spam,
        'spoiler': submission.spoiler,
        'stickied': submission.stickied,
        'subreddit': submission.subreddit,
        'subreddit_id': submission.subreddit_id,
        'subreddit_name_prefixed': submission.subreddit_name_prefixed,
        'subreddit_subscribers': submission.subreddit_subscribers,
        'title': submission.title,
        'upvote_ratio': submission.upvote_ratio,
        'ups': submission.ups,
        'url': submission.url,
        'url_overridden_by_dest': submission.url_overridden_by_dest,
        'user_reports': submission.user_reports,
        'author': submission.author.name,
    })


def store_comment_in_mongo(mongo_db, comment):
    if comment.removed or comment.author is None:
        # Skip 'removed' comments or comments without an author
        return

    comments_collection = mongo_db['comments']
    comments_collection.insert_one({
        'comment_id': comment.id,
        'body': comment.body,
        'author': comment.author.name,
        'score': comment.score,
        'created_utc': comment.created_utc,
        'permalink': comment.permalink,
        'link_id': comment.link_id,
        'parent_id': comment.parent_id,
        'is_submitter': comment.is_submitter,
    })


def connect_to_mongo():
    retries = 0
    while retries < MAX_RETRIES:
        try:
            # Create a new client and connect to the server
            client = MongoClient(os.environ.get("MONGODB"))
            # Send a ping to confirm a successful connection
            try:
                client.admin.command('ping')
                print("Pinged your deployment. You successfully connected to MongoDB!")
            except Exception as e:
                print(e)

            return client
        except Exception as e:
            print(e)
            print(
                f"Failed to connect to MongoDB, attempt {retries + 1}/{MAX_RETRIES}. Retrying in {RETRY_DELAY} seconds...")
            retries += 1
            time.sleep(RETRY_DELAY)
    print("Failed to connect to MongoDB after multiple attempts.")
    exit()


client = connect_to_mongo()
