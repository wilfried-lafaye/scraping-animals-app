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
        'JOBDIR': 'jobstate/animals',
        'ROBOTSTXT_OBEY': False
    }

    def start_requests(self):
        """Start with impersonation enabled via meta."""
        yield scrapy.Request(
            url="https://a-z-animals.com/animals/",
            callback=self.parse,
            meta={"impersonate": "safari15_5"}
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
                meta={"impersonate": "safari15_5"}
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
                        "impersonate": "safari15_5",
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

        # Helper to extract key-value pairs from a specific DL
        def extract_dl(selector_xpath):
            data = {}
            dl_elements = response.xpath(selector_xpath)
            for dl in dl_elements:
                dt_elements = dl.xpath('.//dt')
                dd_elements = dl.xpath('.//dd')
                for dt, dd in zip(dt_elements, dd_elements):
                    label = dt.xpath('string(.)').get()
                    value = dd.xpath('string(.)').get()
                    if label and value:
                        # Clean label (remove colon) and value
                        clean_label = label.strip().rstrip(':')
                        clean_value = value.strip()
                        if clean_label and clean_value:
                            data[clean_label] = clean_value
            return data

        # 1. Classification (Taxonomy) - usually in .animal-facts or similar
        # Note: On a-z-animals, the taxonomy is often in a specific box. we use the existing specific class.
        classification = extract_dl('//dl[contains(@class, "animal-facts")]')

        # 2. Key Facts (The top box with "Fun Fact", "Prey", etc.)
        # Often has class "row" and might be inside a div with specific attributes
        # We look for the "Facts" section specifically to keep them separate from physical traits if possible.
        facts = extract_dl('//div[contains(@class, "row")]//dl[contains(@class, "row")]') 
        # Fallback or additional: sometimes they are just in .row class DLs.
        
        # 3. Physical Characteristics (The bottom box with "Color", "Skin Type", etc.)
        # These are often in a section with an H2 "Physical Characteristics".
        physical_characteristics = {}
        # Try to find the DL following the "Physical Characteristics" header
        phys_header = response.xpath('//h2[contains(text(), "Physical Characteristics")]')
        if phys_header:
            # The DL is usually inside the next div or directly following
            # We can try a broader approach: Look for any DL that hasn't been captured yet?
            # Or specifically look for the container.
            # Let's try to grab the container following the header.
            # Try to grab the container following the header.
            # Case 1: Wrapped in a div (common)
            phys_dl = phys_header.xpath('./following-sibling::div[1]//dl')
            # Case 2: Direct sibling (as seen in example.html)
            if not phys_dl:
                phys_dl = phys_header.xpath('./following-sibling::dl[1]')
            
            if phys_dl:
                 # Extract standard
                 for dl in phys_dl:
                     dt_elements = dl.xpath('.//dt')
                     dd_elements = dl.xpath('.//dd')
                     for dt, dd in zip(dt_elements, dd_elements):
                         label = dt.xpath('string(.)').get()
                         value = dd.xpath('string(.)').get()
                         if label and value:
                             physical_characteristics[label.strip().rstrip(':')] = value.strip()

        # If empty, try a more generic approach to capture ALL DLs and categorize them?
        # For this task, we want to be sure we get everything.
        # Let's aggregate ALL data into a "general_facts" if we aren't sure, 
        # but the user asked for "generic", implies getting everything available.
        
        # Let's use a robust strategy: Capture ALL dl items into a single 'details' dict for safety, 
        # then also allow specific buckets if we can identify them.
        all_specs = extract_dl('//dl')
        
        # Merge physical chars into all_specs to ensure we have them
        all_specs.update(physical_characteristics)
        all_specs.update(facts)
        all_specs.update(classification)

        # Legacy fields extraction (Habitat, Diet) using the new generic data if available
        habitat = all_specs.get('Habitat', all_specs.get('Most Distinctive Feature', None))
        diet = all_specs.get('Diet', all_specs.get('Favorite Food', None))
        
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
            # Try getting first 2 paragraphs from main content
            description_parts = response.xpath('//div[@id="single-animal-text"]//p[position() <= 2]//text()').getall()
            if description_parts:
                description = " ".join([p.strip() for p in description_parts if p.strip() and len(p.strip()) > 20])
                # Limit to reasonable length, cut at sentence boundary
                if description and len(description) > 800:
                    # Try to cut at last sentence before 800 chars
                    cut_pos = description[:800].rfind('. ')
                    if cut_pos > 400:  # Only if we find a sentence ending after 400 chars
                        description = description[:cut_pos + 1]
                    else:
                        description = description[:800] + "..."

        # Key facts (list items)
        key_facts = response.xpath('//div[contains(@class, "animal-facts")]//li/text()').getall()

        # Conservation status - extract from h2 section
        conservation_status_list = response.xpath(
            '//h2[contains(text(), "Conservation Status")]/following-sibling::ul//a/text()'
        ).getall()
        # Join multiple statuses (e.g., "Critically Endangered, Endangered")
        conservation_status = ', '.join(conservation_status_list) if conservation_status_list else None

        # Locations
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
            'classification': classification,
            'facts': facts,
            'physical_characteristics': physical_characteristics,
            # 'all_data': all_specs, # Optional: include everything flat if needed
            'locations': locations,
            'url': response.url,
            'source_page': source_page
        }

        self.logger.info(f"Scraped details for: {animal_name}")
