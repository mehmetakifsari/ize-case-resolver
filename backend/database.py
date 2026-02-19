import os
from pymongo import MongoClient

MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongodb:27017")
DB_NAME = os.getenv("DB_NAME", "ize_database")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]
