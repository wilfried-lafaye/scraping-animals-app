#!/usr/bin/env python
"""
Run script for Animals Spider.
Ensures TWISTED_REACTOR is installed before Scrapy starts.
"""
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Install asyncio reactor BEFORE importing twisted.internet.reactor
from twisted.internet import asyncioreactor
asyncioreactor.install()

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from crawler.spiders.animals_spider import AnimalsSpider


def main():
    settings = get_project_settings()
    # Some installed versions of `scrapy_impersonate` provide a download
    # handler incompatible with the current Scrapy runtime. For local runs
    # we disable the custom DOWNLOAD_HANDLERS to avoid handler init errors.
    if settings.get('DOWNLOAD_HANDLERS'):
        settings['DOWNLOAD_HANDLERS'] = {}
    # Also avoid applying the spider's custom DOWNLOAD_HANDLERS at crawl time
    if hasattr(AnimalsSpider, 'custom_settings') and 'DOWNLOAD_HANDLERS' in AnimalsSpider.custom_settings:
        cs = dict(AnimalsSpider.custom_settings)
        cs.pop('DOWNLOAD_HANDLERS', None)
        AnimalsSpider.custom_settings = cs

    # Optionally skip MongoDB pipeline when environment variable SKIP_MONGO is set
    if os.environ.get('SKIP_MONGO'):
        settings['ITEM_PIPELINES'] = {}
    else:
        # Ensure MongoDB pipeline is active for direct insertion when running locally
        settings['ITEM_PIPELINES'] = settings.get('ITEM_PIPELINES', {})
        settings['ITEM_PIPELINES'].update({
            'crawler.pipelines.MongoDBPipeline': 300,
        })

    process = CrawlerProcess(settings)
    process.crawl(AnimalsSpider)
    process.start()


if __name__ == '__main__':
    main()
