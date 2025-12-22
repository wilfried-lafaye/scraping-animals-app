# Scrapy settings for crawler project
BOT_NAME = "crawler"

SPIDER_MODULES = ["crawler.spiders"]
NEWSPIDER_MODULE = "crawler.spiders"

# Respectful crawling
ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 2
CONCURRENT_REQUESTS = 1

# Headers
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

# Output
FEEDS = {
    'data/animals_scrapy.json': {
        'format': 'json',
        'encoding': 'utf8',
        'indent': 4,
    },
}
