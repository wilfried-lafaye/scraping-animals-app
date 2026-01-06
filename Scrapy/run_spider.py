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
    process = CrawlerProcess(settings)
    process.crawl(AnimalsSpider)
    process.start()


if __name__ == '__main__':
    main()
