import scrapy
from urllib.parse import urljoin
import os


class AnimalsSpider(scrapy.Spider):
    name = "animals"
    allowed_domains = ["a-z-animals.com"]

    # Configuration: number of animals to scrape per letter
    ANIMALS_PER_LETTER = 10000

    # Spider-specific settings + JSON export
    custom_settings = {
        # Enable scrapy-impersonate to bypass 403
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_impersonate.ImpersonateDownloadHandler",
            "https": "scrapy_impersonate.ImpersonateDownloadHandler",
        },
        # Respectful crawling at spider level
        'DOWNLOAD_DELAY': 0.5,
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        # JSON export avec chemin absolu
        'FEEDS': {
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'animals.json'): {
                'format': 'json',
                'encoding': 'utf-8',
                'overwrite': True,
            },
        },
        # Allow resuming long crawls (persist scheduler state)
        'JOBDIR': 'jobstate/animals'
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
        # Explicit log for user tracking
        letter = response.url.split('start-with-')[-1].replace('/', '').upper()
        self.logger.info(f"✅ LETTER COMPLETED: Finished queuing animals for letter '{letter}'")

        # Try to follow pagination for this letter page (if any)
        next_selectors = [
            '//a[@rel="next"]/@href',
            '//link[@rel="next"]/@href',
            '//a[contains(@class, "next")]/@href',
            '//ul[contains(@class, "pagination")]//a[@rel="next" or contains(@class, "next") or contains(translate(normalize-space(.), "NEXT", "next"), "next")]/@href',
            # Generic fallback for common query params
            '//a[contains(@href, "?page=") or contains(@href, "?pg=") or contains(@href, "/page/")]/@href'
        ]

        next_urls = set()
        for xp in next_selectors:
            for href in response.xpath(xp).getall():
                if href:
                    next_urls.add(urljoin(response.url, href))

        for next_url in next_urls:
            # Rely on Scrapy dupefilter to avoid loops
            self.logger.info(f"Following pagination: {next_url}")
            yield scrapy.Request(
                next_url,
                callback=self.parse_letter_page,
                meta={"impersonate": "chrome120"}
            )

    def parse_animal_detail(self, response):
        """Parse individual animal page and extract detailed information."""
        animal_name = response.meta.get('animal_name')
        source_page = response.meta.get('source_page')

        # Extract image URL
        image_url = response.xpath('//img[contains(@class, "animal-image") or contains(@class, "main-image")]/@src').get()
        if not image_url:
            image_url = response.xpath('//img[@alt="' + animal_name + '"]/@src').get()
        if not image_url:
            image_url = response.xpath('//div[contains(@class, "animal-header")]//img/@src').get()
        if image_url:
            image_url = urljoin(response.url, image_url)

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

        # Extract fields expected by unit tests / JSON schema
        scientific_name = response.xpath('//em/text()').get()

        # Description - Try multiple selectors
        # First try: structured data JSON-LD
        description = None
        try:
            import json
            import re
            json_ld_match = re.search(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', response.text, re.DOTALL)
            if json_ld_match:
                json_data = json.loads(json_ld_match.group(1))
                if isinstance(json_data, dict) and '@graph' in json_data:
                    for item in json_data['@graph']:
                        if item.get('@type') == 'WebPage' and 'description' in item:
                            desc = item['description']
                            # Only use if it's not the generic description
                            if desc and 'high-quality pictures' not in desc.lower():
                                description = desc
                            break
        except Exception:
            pass
        
        # Second try: extract from paragraph tags
        if not description:
            # Try getting first few paragraphs from main content
            description_parts = response.xpath('//div[@id="single-animal-text"]//p[position() <= 3]//text()').getall()
            if description_parts:
                description = " ".join([p.strip() for p in description_parts if p.strip() and len(p.strip()) > 20])
                # Limit to reasonable length
                if description and len(description) > 500:
                    description = description[:500] + "..."

        # Key facts (list items)
        key_facts = response.xpath('//div[contains(@class, "animal-facts")]//li/text()').getall()

        # Conservation status - extract from h2 section
        conservation_status_list = response.xpath(
            '//h2[contains(text(), "Conservation Status")]/following-sibling::ul//a/text()'
        ).getall()
        # Join multiple statuses (e.g., "Critically Endangered, Endangered")
        conservation_status = ', '.join(conservation_status_list) if conservation_status_list else None
        
        # Habitat and diet — look for labelled spans
        def extract_label_value(label):
            val = response.xpath(f'//span[normalize-space(text())="{label}"]/following-sibling::span[1]/text()').get()
            return val.strip() if val else None

        habitat = extract_label_value('Habitat')
        diet = extract_label_value('Diet')

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
            'scientific_name': scientific_name,
            'description': description,
            'key_facts': key_facts if key_facts else None,
            'conservation_status': conservation_status,
            'habitat': habitat,
            'diet': diet,
            'image_url': image_url,
            'classification': classification if classification else None,
            'facts': facts if facts else None,
            'locations': locations if locations else [],
            'url': response.url,
            'source_page': source_page
        }

        self.logger.info(f"Scraped details for: {animal_name}")
