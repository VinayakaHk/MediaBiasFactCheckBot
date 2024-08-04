from pymongo.errors import ConnectionFailure, PyMongoError
from pymongo.mongo_client import MongoClient
from pymongo import IndexModel, DESCENDING
from pymongo.errors import OperationFailure

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
db = None


def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno,
                                                       line.strip(), exc_obj))


def store_llm_in_comments(reason , comment_id):
    """
    A function that stores a llm in the comments based on the given reason and comment_id.
    
    Parameters:
    - reason: The reason for storing the llm in the comments.
    - comment_id: The ID of the comment to store the llm in.
    
    Returns:
    None
    """
    print('reason',reason)
    print('comment_id',comment_id)
    try:
        global db
        comments_collection = db['comments']

        comment = comments_collection.update_one(
            {"comment_id": comment_id}, {"$set": {'ai_removal_reason' : reason} }
        )
    except Exception as e:
        PrintException()


def comment_body(comment_id):
    """
    Retrieves the parent comment body based on the given comment_id.

    Args:
        comment_id (int): The unique identifier for the comment.

    Returns:
        str: The body of the parent comment, or None if not found.
    """
    try:
        global db
        comments_collection = db['comments']
        comment = comments_collection.find_one({'comment_id': comment_id})
        if (comment == None or (comment['link_id'] == comment['parent_id'])):
            return None

        split_parts = comment['parent_id'].split('_')
        parent_id = None
        if len(split_parts) == 2:
            parent_id = split_parts[1]
        else:
            return None
        if parent_id == None:
            return None
        parent_comment = comments_collection.find_one(
            {'comment_id': parent_id})
        if (parent_comment == None):
            return None
        return parent_comment['body']
    except Exception as e:
        PrintException()


def store_submission_in_mongo(submission):
    """
    A function that stores a submission in a MongoDB collection.
    
    Parameters:
    submission: object - the submission object to be stored
    
    Returns:
    None
    """
    try:
        global db

        submissions_collection = db['submissions']
        if_submission = submissions_collection.find_one(
            {'submission_id': submission.id})
        if (if_submission == None):
            submissions_collection.insert_one({
                'author': str(submission.author),
                'created': str(submission.created),
                'distinguished': str(submission.distinguished),
                'domain': str(submission.domain),
                'submission_id': str(submission.id),
                'is_reddit_media_domain': str(submission.is_reddit_media_domain),
                'is_self': str(submission.is_self),
                'is_video': str(submission.is_video),
                'locked': str(submission.locked),
                'permalink': str(submission.permalink),
                'selftext': str(submission.selftext),
                'spoiler': str(submission.spoiler),
                'stickied': str(submission.stickied),
                'subreddit': str(submission.subreddit),
                'subreddit_id': str(submission.subreddit_id),
                'subreddit_name_prefixed': str(submission.subreddit_name_prefixed),
                'subreddit_subscribers': str(submission.subreddit_subscribers),
                'title': str(submission.title),
                'url': str(submission.url),
            })
        else:
            print('Submission Exists in mongodb')
    except Exception as e:
        PrintException()


def store_comment_in_mongo(comment):
    """
    A function to store a comment in a MongoDB collection.
    
    Parameters:
    comment (obj): The comment object to be stored in the collection.
    
    Returns:
    None
    """
    try:
        global db
        comments_collection = db['comments']
        if_comment = comments_collection.find_one({'comment_id': comment.id})
        if (if_comment == None):
            comments_collection.insert_one({
                'author': str(comment.author),
                'author_is_blocked': str(comment.author_is_blocked),
                'banned_at_utc': str(comment.banned_at_utc),
                'banned_by': str(comment.banned_by),
                'body': str(comment.body),
                'controversiality': str(comment.controversiality),
                'created_utc': str(comment.created_utc),
                'distinguished': str(comment.distinguished),
                'comment_id': str(comment.id),
                'is_submitter': str(comment.is_submitter),
                'link_author': str(comment.link_author),
                'link_id': str(comment.link_id),
                'link_permalink': str(comment.link_permalink),
                'link_title': str(comment.link_title),
                'link_url': str(comment.link_url),
                'name': str(comment.name),
                'parent_id': str(comment.parent_id),
                'permalink': str(comment.permalink),
                'stickied': str(comment.stickied),
                'subreddit': str(comment.subreddit),
                'subreddit_id': str(comment.subreddit_id),
                'subreddit_name_prefixed': str(comment.subreddit_name_prefixed),
            })
        else:
            print('Comment exists in mongodb', comment)
    except Exception as e:
        PrintException()


def create_indexes():
    """
    A function to create indexes for the 'comments' and 'submissions' collections in the database.
    """
    try:
        global db

        # Create compound index for 'comments' collection
        comment_index_model = IndexModel(
            [('comment_id', DESCENDING), ('parent_id', DESCENDING)], unique=True)
        db['comments'].create_indexes([comment_index_model])

        # Create index for 'submissions' collection
        submission_index_model = IndexModel(
            [('submission_id', DESCENDING)], unique=True)
        db['submissions'].create_indexes([submission_index_model])

    except OperationFailure as e:
        print('OperationFailure: ', e)
    except Exception as e:
        print('Exception occurred: ', e)


def connect_to_mongo():
    """
    A function to establish a connection to a MongoDB database with retries in case of failure.
    This function does the following:
    - Attempts to connect to the MongoDB server using the provided environment variable.
    - Sends a ping to confirm the connection's success.
    - If the connection is successful, it prints a success message, creates necessary indexes, and returns the database connection.
    - If the connection fails, it retries a specified number of times with a delay between each attempt.
    - If all attempts fail, it prints a failure message and exits the program.
    
    Returns:
    - db (pymongo.database.Database): The connected MongoDB database.
    """
    global db
    retries = 0
    while retries < MAX_RETRIES:
        try:
            # Create a new client and connect to the server
            client = MongoClient(os.environ.get("MONGODB"))
            db = client.reddit
            # Send a ping to confirm a successful connection
            try:
                client.admin.command('ping')
                print("Pinged your deployment. You successfully connected to MongoDB!")
                create_indexes()
                return db
            except Exception as e:
                PrintException()
        except Exception as e:
            PrintException()
            print(
                f"Failed to connect to MongoDB, attempt {retries + 1}/{MAX_RETRIES}. Retrying in {RETRY_DELAY} seconds...")
            retries += 1
            time.sleep(RETRY_DELAY)
    print("Failed to connect to MongoDB after multiple attempts.")
    exit()
