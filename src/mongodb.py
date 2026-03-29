import os
import time
import threading
import praw
from pymongo.mongo_client import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError, OperationFailure
from pymongo import IndexModel, DESCENDING
from dotenv import load_dotenv
from src.exceptions import logger

load_dotenv()

MAX_RETRIES = 10
RETRY_DELAY = 10

# Submission state machine states
STATE_PENDING = "pending_review"
STATE_AWAITING_SS = "awaiting_ss"
STATE_APPROVED = "approved"


class MongoDB:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.db = None
        self._connect()

    def _connect(self):
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                client = MongoClient(os.environ.get("MONGODB"))
                client.admin.command('ping')
                self.db = client.reddit
                logger.info("Successfully connected to MongoDB")
                self._create_indexes()
                return
            except (ConnectionFailure, PyMongoError):
                logger.exception(f"MongoDB connection attempt {attempt}/{MAX_RETRIES} failed")
                time.sleep(RETRY_DELAY)
        logger.critical("Failed to connect to MongoDB after all retries")
        raise ConnectionFailure("Could not connect to MongoDB")

    def _create_indexes(self):
        try:
            self.db['comments'].create_indexes([
                IndexModel([('comment_id', DESCENDING), ('parent_id', DESCENDING)], unique=True)
            ])
            self.db['submissions'].create_indexes([
                IndexModel([('submission_id', DESCENDING)], unique=True)
            ])
            self.db['submission_state'].create_indexes([
                IndexModel([('submission_id', DESCENDING)], unique=True),
                IndexModel([('state', DESCENDING), ('updated_at', DESCENDING)])
            ])
        except OperationFailure:
            logger.exception("Failed to create indexes")

    def store_comment(self, comment: praw.models.Comment):
        try:
            self.db['comments'].update_one(
                {'comment_id': str(comment.id)},
                {'$setOnInsert': {
                    'author': str(comment.author),
                    'author_is_blocked': comment.author_is_blocked,
                    'banned_at_utc': comment.banned_at_utc,
                    'banned_by': str(comment.banned_by) if comment.banned_by else None,
                    'body': comment.body,
                    'controversiality': comment.controversiality,
                    'created_utc': comment.created_utc,
                    'distinguished': comment.distinguished,
                    'comment_id': str(comment.id),
                    'is_submitter': comment.is_submitter,
                    'link_author': str(comment.link_author),
                    'link_id': comment.link_id,
                    'link_permalink': comment.link_permalink,
                    'link_title': comment.link_title,
                    'link_url': comment.link_url,
                    'name': comment.name,
                    'parent_id': comment.parent_id,
                    'permalink': comment.permalink,
                    'stickied': comment.stickied,
                    'subreddit': str(comment.subreddit),
                    'subreddit_id': comment.subreddit_id,
                    'subreddit_name_prefixed': comment.subreddit_name_prefixed,
                }},
                upsert=True
            )
        except PyMongoError:
            logger.exception("Failed to store comment")

    def store_submission(self, submission: praw.models.Submission):
        try:
            self.db['submissions'].update_one(
                {'submission_id': str(submission.id)},
                {'$setOnInsert': {
                    'author': str(submission.author),
                    'created': submission.created,
                    'distinguished': submission.distinguished,
                    'domain': submission.domain,
                    'submission_id': str(submission.id),
                    'is_reddit_media_domain': submission.is_reddit_media_domain,
                    'is_self': submission.is_self,
                    'is_video': submission.is_video,
                    'locked': submission.locked,
                    'permalink': submission.permalink,
                    'selftext': submission.selftext,
                    'spoiler': submission.spoiler,
                    'stickied': submission.stickied,
                    'subreddit': str(submission.subreddit),
                    'subreddit_id': submission.subreddit_id,
                    'subreddit_name_prefixed': submission.subreddit_name_prefixed,
                    'subreddit_subscribers': submission.subreddit_subscribers,
                    'title': submission.title,
                    'url': submission.url,
                }},
                upsert=True
            )
        except PyMongoError:
            logger.exception("Failed to store submission")

    def store_llm_in_comments(self, reason: str, comment_id: str):
        try:
            self.db['comments'].update_one(
                {"comment_id": comment_id},
                {"$set": {'ai_removal_reason': reason}}
            )
        except PyMongoError:
            logger.exception("Failed to store LLM result")

    def get_comment_body(self, comment_id: str):
        try:
            comment = self.db['comments'].find_one({'comment_id': comment_id})
            if comment is None or comment['link_id'] == comment['parent_id']:
                return None

            parts = comment['parent_id'].split('_')
            if len(parts) != 2:
                return None

            parent = self.db['comments'].find_one({'comment_id': parts[1]})
            return parent['body'] if parent else None
        except PyMongoError:
            logger.exception("Failed to get comment body")
            return None

    # --- Submission state machine ---

    def init_submission_state(self, submission_id):
        """Create initial pending_review state. Returns the current state doc."""
        try:
            self.db['submission_state'].update_one(
                {'submission_id': submission_id},
                {'$setOnInsert': {
                    'submission_id': submission_id,
                    'state': STATE_PENDING,
                    'created_at': time.time(),
                    'updated_at': time.time(),
                    'ss_comment_id': None,
                }},
                upsert=True
            )
            return self.db['submission_state'].find_one({'submission_id': submission_id})
        except PyMongoError:
            logger.exception("Failed to init submission state")
            return None

    def transition_to_awaiting_ss(self, submission_id):
        """Atomic: pending_review -> awaiting_ss. Returns True if transition succeeded."""
        try:
            result = self.db['submission_state'].update_one(
                {'submission_id': submission_id, 'state': STATE_PENDING},
                {'$set': {'state': STATE_AWAITING_SS, 'updated_at': time.time()}}
            )
            return result.modified_count == 1
        except PyMongoError:
            logger.exception("Failed to transition to awaiting_ss")
            return False

    def transition_to_approved(self, submission_id, ss_comment_id=None):
        """Atomic: pending_review|awaiting_ss -> approved. Returns True if transition succeeded."""
        try:
            update = {'$set': {'state': STATE_APPROVED, 'updated_at': time.time()}}
            if ss_comment_id:
                update['$set']['ss_comment_id'] = ss_comment_id

            result = self.db['submission_state'].update_one(
                {'submission_id': submission_id, 'state': {'$in': [STATE_PENDING, STATE_AWAITING_SS]}},
                update
            )
            return result.modified_count == 1
        except PyMongoError:
            logger.exception("Failed to transition to approved")
            return False

    def get_submission_state(self, submission_id):
        try:
            return self.db['submission_state'].find_one({'submission_id': submission_id})
        except PyMongoError:
            logger.exception("Failed to get submission state")
            return None

    def get_stale_awaiting_ss(self, max_age_seconds=300):
        """Find submissions stuck in awaiting_ss for longer than max_age_seconds (for retry sweep)."""
        try:
            cutoff = time.time() - max_age_seconds
            return list(self.db['submission_state'].find({
                'state': STATE_AWAITING_SS,
                'updated_at': {'$lt': cutoff}
            }))
        except PyMongoError:
            logger.exception("Failed to query stale submissions")
            return []


# Module-level convenience functions for backward compatibility
_db = None
_db_lock = threading.Lock()

def _get_db():
    global _db
    with _db_lock:
        if _db is None:
            _db = MongoDB()
        return _db

def store_comment_in_mongo(comment):
    _get_db().store_comment(comment)

def store_submission_in_mongo(submission):
    _get_db().store_submission(submission)

def store_llm_in_comments(reason, comment_id):
    _get_db().store_llm_in_comments(reason, comment_id)

def comment_body(comment_id):
    return _get_db().get_comment_body(comment_id)

def init_submission_state(submission_id):
    return _get_db().init_submission_state(submission_id)

def transition_to_awaiting_ss(submission_id):
    return _get_db().transition_to_awaiting_ss(submission_id)

def transition_to_approved(submission_id, ss_comment_id=None):
    return _get_db().transition_to_approved(submission_id, ss_comment_id)

def get_submission_state(submission_id):
    return _get_db().get_submission_state(submission_id)

def get_stale_awaiting_ss(max_age_seconds=300):
    return _get_db().get_stale_awaiting_ss(max_age_seconds)
