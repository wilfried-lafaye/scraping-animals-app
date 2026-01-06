import scrapy
from urllib.parse import urljoin


class AnimalsSpider(scrapy.Spider):
    name = "animals"
    allowed_domains = ["a-z-animals.com"]

    # Configuration: number of animals to scrape per letter
    ANIMALS_PER_LETTER = 10

    # Spider-specific settings + JSON export
    custom_settings = {
        # Enable scrapy-impersonate to bypass 403
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_impersonate.ImpersonateDownloadHandler",
            "https": "scrapy_impersonate.ImpersonateDownloadHandler",
        },
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        # JSON export
        'FEEDS': {
            'data/animals.json': {
                'format': 'json',
                'encoding': 'utf-8',
                'overwrite': True,
            },
        },
    }

    def start_requests(self):
        """Start with impersonation enabled via meta."""
        yield scrapy.Request(
            url="https://a-z-animals.com/animals/",
            callback=self.parse,
            meta={"impersonate": "chrome120"}
        )

    def parse(self, response):
        """Parse the main animals page and follow letter links."""
        letter_links = response.xpath(
            '//a[contains(@href, "/animals/animals-that-start-with-")]/@href'
        ).getall()

        self.logger.info(f"Found {len(letter_links)} letter pages.")

        for link in letter_links:
            full_url = urljoin(response.url, link)
            yield scrapy.Request(
                full_url,
                callback=self.parse_letter_page,
                meta={"impersonate": "chrome120"}
            )

    def parse_letter_page(self, response):
        """Parse a letter page and extract animal URLs, limited by ANIMALS_PER_LETTER."""
        animal_links = response.xpath(
            '//li/a[starts-with(@href, "https://a-z-animals.com/animals/") '
            'and not(contains(@href, "animals-that-start-with"))]'
        )

        count = 0
        for a_link in animal_links:
            # Limit to ANIMALS_PER_LETTER per letter page
            if count >= self.ANIMALS_PER_LETTER:
                break

            name = a_link.xpath('text()').get()
            url = a_link.xpath('@href').get()

            if name and url:
                # Skip category pages (Amphibians, Birds, Fish, Mammals, Reptiles, All Animals)
                skip_names = ['Amphibians', 'Birds', 'Fish', 'Mammals', 'Reptiles', 'All Animals']
                if name.strip() in skip_names:
                    continue

                count += 1
                # Follow the URL to get detailed info
                yield scrapy.Request(
                    url=urljoin(response.url, url),
                    callback=self.parse_animal_detail,
                    meta={
                        "impersonate": "chrome120",
                        "animal_name": name.strip(),
                        "source_page": response.url
                    }
                )

        self.logger.info(f"Queued {count} animals from {response.url}")

    def parse_animal_detail(self, response):
        """Parse individual animal page and extract detailed information."""
        animal_name = response.meta.get('animal_name')
        source_page = response.meta.get('source_page')

        # Extract Scientific Classification (taxonomy)
        classification = {}
        classification_dl = response.xpath('//dl[contains(@class, "animal-facts")]')
        if classification_dl:
            dt_elements = classification_dl.xpath('.//dt')
            dd_elements = classification_dl.xpath('.//dd')
            for dt, dd in zip(dt_elements, dd_elements):
                label = dt.xpath('string(.)').get()
                value = dd.xpath('string(.)').get()
                if label and value:
                    label = label.strip().rstrip(':')
                    value = value.strip()
                    classification[label] = value

        # Extract Animal Facts (Main Prey, Habitat, Predators, Diet, etc.)
        facts = {}
        facts_dl = response.xpath('//dl[@class="row" and contains(@title, "Facts")]')
        if facts_dl:
            dt_elements = facts_dl.xpath('.//dt')
            dd_elements = facts_dl.xpath('.//dd')
            for dt, dd in zip(dt_elements, dd_elements):
                label = dt.xpath('string(.)').get()
                value = dd.xpath('string(.)').get()
                if label and value:
                    label = label.strip().rstrip(':')
                    value = value.strip()
                    if label and value:
                        facts[label] = value

        # Extract Locations (continents/regions where the animal is found)
        locations = response.xpath(
            '//a[contains(@href, "/animals/location/")]/text()'
        ).getall()
        excluded = ['By Location', 'Location', 'By']
        locations = [
            loc.strip() for loc in locations
            if loc.strip() and loc.strip() not in excluded
        ]

        yield {
            'animal_name': animal_name,
            'classification': classification if classification else None,
            'facts': facts if facts else None,
            'locations': locations if locations else [],
            'url': response.url,
            'source_page': source_page
        }

        self.logger.info(f"Scraped details for: {animal_name}")
