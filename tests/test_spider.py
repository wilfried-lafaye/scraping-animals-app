"""
Unit tests for the Scrapy spider.
Step 1b of the roadmap - JSON format validation.
"""
import pytest
import json
import os
from scrapy.http import HtmlResponse, Request

# Add Scrapy path to import the spider
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Scrapy'))

from crawler.spiders.animals_spider import AnimalsSpider


def create_mock_response(url, body, meta=None):
    """Helper to create a mock Scrapy response."""
    request = Request(url=url, meta=meta or {})
    return HtmlResponse(url=url, request=request, body=body, encoding='utf-8')


# Sample HTML for testing parse_animal_detail
SAMPLE_ANIMAL_HTML = """
<!DOCTYPE html>
<html>
<head><title>Tiger</title></head>
<body>
    <h1>Tiger</h1>
    <em>Panthera tigris</em>
    <div itemprop="description">
        <p>The tiger is the largest living cat species and a member of the genus Panthera.</p>
    </div>
    <div class="animal-facts">
        <ul>
            <li>Largest living cat species</li>
            <li>Native to Asia</li>
        </ul>
    </div>
    <div>
        <span>Conservation Status</span>
        <span>Endangered</span>
    </div>
    <div>
        <span>Habitat</span>
        <span>Forests of Asia</span>
    </div>
    <div>
        <span>Diet</span>
        <span>Carnivore</span>
    </div>
</body>
</html>
"""


class TestAnimalsSpider:
    """Tests for AnimalsSpider."""

    @pytest.fixture
    def spider(self):
        """Create a spider instance for testing."""
        return AnimalsSpider()

    @pytest.fixture
    def mock_response(self):
        """Create a mock response with sample animal HTML."""
        return create_mock_response(
            url="https://a-z-animals.com/animals/tiger/",
            body=SAMPLE_ANIMAL_HTML,
            meta={
                "animal_name": "Tiger",
                "source_page": "https://a-z-animals.com/animals/animals-that-start-with-t/"
            }
        )

    def test_parse_animal_detail_extracts_name(self, spider, mock_response):
        """Verify that the animal name is extracted correctly."""
        results = list(spider.parse_animal_detail(mock_response))
        assert len(results) == 1
        assert results[0]['animal_name'] == 'Tiger'

    def test_parse_animal_detail_extracts_scientific_name(self, spider, mock_response):
        """Verify scientific name extraction."""
        results = list(spider.parse_animal_detail(mock_response))
        assert len(results) == 1
        # Scientific name comes from <em> tag in our mock HTML
        assert results[0]['scientific_name'] == 'Panthera tigris'

    def test_parse_animal_detail_returns_required_fields(self, spider, mock_response):
        """Verify that all required fields are present in the result."""
        required_fields = [
            'animal_name',
            'scientific_name',
            'description',
            'key_facts',
            'conservation_status',
            'habitat',
            'diet',
            'url',
            'source_page'
        ]
        results = list(spider.parse_animal_detail(mock_response))
        assert len(results) == 1
        for field in required_fields:
            assert field in results[0], f"Missing required field: {field}"

    def test_animals_per_letter_limit(self, spider):
        """Verify that ANIMALS_PER_LETTER limit is configured."""
        assert hasattr(spider, 'ANIMALS_PER_LETTER')
        assert spider.ANIMALS_PER_LETTER == 10
        assert isinstance(spider.ANIMALS_PER_LETTER, int)


class TestJsonValidation:
    """Tests for exported JSON format validation."""

    @pytest.fixture
    def sample_animal_data(self):
        """Sample valid animal data."""
        return {
            'animal_name': 'Tiger',
            'scientific_name': 'Panthera tigris',
            'description': 'The tiger is the largest living cat species.',
            'key_facts': ['Largest living cat species', 'Native to Asia'],
            'conservation_status': 'Endangered',
            'habitat': 'Forests of Asia',
            'diet': 'Carnivore',
            'url': 'https://a-z-animals.com/animals/tiger/',
            'source_page': 'https://a-z-animals.com/animals/animals-that-start-with-t/'
        }

    def test_json_schema_is_valid(self, sample_animal_data):
        """Verify that sample data matches expected schema."""
        # Verify types
        assert isinstance(sample_animal_data['animal_name'], str)
        assert isinstance(sample_animal_data['key_facts'], list)
        assert isinstance(sample_animal_data['url'], str)
        
        # Verify URL format
        assert sample_animal_data['url'].startswith('https://a-z-animals.com/')
        
        # Verify data can be serialized to JSON
        json_str = json.dumps(sample_animal_data)
        parsed = json.loads(json_str)
        assert parsed == sample_animal_data

    def test_no_null_animal_names(self, sample_animal_data):
        """Verify that animal name is not null."""
        assert sample_animal_data['animal_name'] is not None
        assert len(sample_animal_data['animal_name']) > 0


class TestSpiderConfiguration:
    """Tests for spider configuration."""

    @pytest.fixture
    def spider(self):
        return AnimalsSpider()

    def test_spider_name(self, spider):
        """Verify spider name is configured."""
        assert spider.name == "animals"

    def test_allowed_domains(self, spider):
        """Verify allowed domains are configured."""
        assert "a-z-animals.com" in spider.allowed_domains

    def test_custom_settings_exist(self, spider):
        """Verify custom settings are configured."""
        assert hasattr(spider, 'custom_settings')
        assert 'DOWNLOAD_DELAY' in spider.custom_settings
        assert 'DOWNLOAD_HANDLERS' in spider.custom_settings

