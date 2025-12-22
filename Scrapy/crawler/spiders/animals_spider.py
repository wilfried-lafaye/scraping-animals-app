import scrapy
from urllib.parse import urljoin


class AnimalsSpider(scrapy.Spider):
    name = "animals"
    allowed_domains = ["a-z-animals.com"]

    # Configuration: number of animals to scrape per letter
    ANIMALS_PER_LETTER = 10

    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 0.5,  # Reduced from 2s
        'CONCURRENT_REQUESTS': 1,
        # Enable scrapy-impersonate handler
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_impersonate.ImpersonateDownloadHandler",
            "https": "scrapy_impersonate.ImpersonateDownloadHandler",
        },
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
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

        # Extract scientific name (usually in subtitle or specific element)
        scientific_name = response.xpath(
            '//p[contains(@class, "scientific-name")]/text() | '
            '//span[contains(@class, "scientific")]/text() | '
            '//em/text()'
        ).get()

        # Extract description (first paragraph in main content)
        description = response.xpath(
            '//div[@itemprop="description"]//p[1]/text() | '
            '//article//p[1]/text()'
        ).get()

        # Extract key facts from the facts box
        key_facts = response.xpath(
            '//div[contains(@class, "animal-facts")]//li/text() | '
            '//ul[contains(@class, "facts")]//li/text()'
        ).getall()

        # Extract conservation status
        conservation_status = response.xpath(
            '//*[contains(text(), "Conservation Status")]/following-sibling::*[1]/text() | '
            '//a[contains(@href, "conservation")]/text()'
        ).get()

        # Extract habitat
        habitat = response.xpath(
            '//*[contains(text(), "Habitat")]/following-sibling::*[1]/text()'
        ).get()

        # Extract diet
        diet = response.xpath(
            '//*[contains(text(), "Diet")]/following-sibling::*[1]/text() | '
            '//a[contains(@href, "/diet/")]/text()'
        ).get()

        yield {
            'animal_name': animal_name,
            'scientific_name': scientific_name.strip() if scientific_name else None,
            'description': description.strip() if description else None,
            'key_facts': [f.strip() for f in key_facts if f.strip()] if key_facts else [],
            'conservation_status': conservation_status.strip() if conservation_status else None,
            'habitat': habitat.strip() if habitat else None,
            'diet': diet.strip() if diet else None,

            'url': response.url,
            'source_page': source_page
        }

        self.logger.info(f"Scraped details for: {animal_name}")
