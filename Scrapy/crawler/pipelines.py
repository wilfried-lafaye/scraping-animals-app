"""
MongoDB Pipeline for Scrapy.
Inserts scraped animal data into MongoDB.
"""
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


class MongoDBPipeline:
    """Pipeline to store scraped items in MongoDB."""

    def __init__(self, mongo_uri, mongo_db, mongo_collection):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.mongo_collection = mongo_collection
        self.client = None
        self.db = None

    @classmethod
    def from_crawler(cls, crawler):
        """Create pipeline instance from Scrapy settings."""
        return cls(
            mongo_uri=crawler.settings.get(
                'MONGO_URI',
                os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
            ),
            mongo_db=crawler.settings.get(
                'MONGO_DB',
                os.environ.get('MONGO_DB', 'animals_db')
            ),
            mongo_collection=crawler.settings.get(
                'MONGO_COLLECTION',
                os.environ.get('MONGO_COLLECTION', 'animals')
            )
        )

    def open_spider(self, spider):
        """Connect to MongoDB when spider opens."""
        try:
            self.client = MongoClient(self.mongo_uri)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.mongo_db]
            spider.logger.info(f"Connected to MongoDB: {self.mongo_db}")
        except ConnectionFailure as e:
            spider.logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def close_spider(self, spider):
        """Close MongoDB connection when spider closes."""
        if self.client:
            self.client.close()
            spider.logger.info("MongoDB connection closed")

    def process_item(self, item, spider):
        """Insert item into MongoDB collection."""
        collection = self.db[self.mongo_collection]

        # Use animal_name + url as unique identifier to avoid duplicates
        filter_query = {
            'animal_name': item.get('animal_name'),
            'url': item.get('url')
        }

        # Upsert: update if exists, insert if not
        collection.update_one(
            filter_query,
            {'$set': dict(item)},
            upsert=True
        )

        spider.logger.debug(f"Saved to MongoDB: {item.get('animal_name')}")
        return item
