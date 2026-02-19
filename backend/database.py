from motor.motor_asyncio import AsyncIOMotorClient
import os

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
mongo_timeout_ms = int(os.environ.get('MONGO_TIMEOUT_MS', '5000'))

client = AsyncIOMotorClient(
    mongo_url,
    serverSelectionTimeoutMS=mongo_timeout_ms,
    connectTimeoutMS=mongo_timeout_ms,
    socketTimeoutMS=mongo_timeout_ms,
)
db = client[os.environ['DB_NAME']]
