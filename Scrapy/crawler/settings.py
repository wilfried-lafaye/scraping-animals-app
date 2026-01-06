# Scrapy settings for crawler project

BOT_NAME = "crawler"

SPIDER_MODULES = ["crawler.spiders"]
NEWSPIDER_MODULE = "crawler.spiders"

# Respectful crawling
ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 0.5
CONCURRENT_REQUESTS = 1

# Headers
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Enable scrapy-impersonate handler
DOWNLOAD_HANDLERS = {
    "http": "scrapy_impersonate.ImpersonateDownloadHandler",
    "https": "scrapy_impersonate.ImpersonateDownloadHandler",
}
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Feed export settings
FEED_EXPORT_ENCODING = 'utf-8'
FEED_EXPORT_INDENT = 2

# MongoDB settings (can be overridden by environment variables)
MONGO_URI = 'mongodb://scraper:scraper_password@localhost:27017/animals_db?authSource=admin'
MONGO_DB = 'animals_db'
MONGO_COLLECTION = 'animals'

# Item pipelines
ITEM_PIPELINES = {
    'crawler.pipelines.MongoDBPipeline': 300,
}

# Logging
LOG_LEVEL = 'INFO'
