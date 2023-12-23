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
