from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from datetime import datetime, UTC
import traceback
import logging

logger = logging.getLogger(__name__)

# Global client and db
client: AsyncIOMotorClient | None = None
db = None


async def get_client():
    """Get or initialize the MongoDB client."""
    global client
    if client is None:
        try:
            client = AsyncIOMotorClient(
                settings.MONGO_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                maxPoolSize=50,
                retryWrites=True,
            )
            await client.admin.command("ping")
            logger.info("MongoDB client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB: {str(e)}")
            client = None
            raise
    return client


async def get_db():
    """Get the database instance."""
    global db
    if db is None:
        mongo_client = await get_client()
        db = mongo_client[settings.MONGO_DB_NAME]
        logger.info(f"Connected to database: {settings.MONGO_DB_NAME}")
    return db


async def close_client():
    """Close the MongoDB client connection."""
    global client, db
    if client is not None:
        client.close()
        client = None
        db = None
        logger.info("MongoDB client closed")


async def log_error(error: Exception, location: str, additional_info: dict = None):
    """Log errors to MongoDB for debugging."""
    try:
        database = await get_db()
        error_collection = database["error_logs"]

        error_doc = {
            "timestamp": datetime.now(UTC),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "location": location,
            "traceback": traceback.format_exc(),
            "additional_info": additional_info or {},
        }

        await error_collection.insert_one(error_doc)
    except Exception as e:
        logger.error(f"Failed to log error to MongoDB: {str(e)}")
