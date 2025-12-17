"""
Unit tests for the Scrapy spider.
Step 1b of the roadmap - JSON format validation.
"""
import pytest
from scrapy.http import HtmlResponse, Request


class TestAnimalsSpider:
    """Tests for AnimalsSpider."""

    def test_parse_animal_detail_extracts_name(self):
        """Verify that the animal name is extracted correctly."""
        # TODO: Implement with mocked HTML response
        pass

    def test_parse_animal_detail_extracts_scientific_name(self):
        """Verify scientific name extraction."""
        # TODO: Implement
        pass

    def test_parse_animal_detail_returns_required_fields(self):
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
        # TODO: Implement field validation
        pass

    def test_animals_per_letter_limit(self):
        """Verify that ANIMALS_PER_LETTER limit is respected."""
        # TODO: Implement
        pass


class TestJsonValidation:
    """Tests for exported JSON format validation."""

    def test_json_schema_is_valid(self):
        """Verify that exported JSON matches expected schema."""
        # TODO: Implement with jsonschema
        pass

    def test_no_null_animal_names(self):
        """Verify that no animal has a null name."""
        # TODO: Implement
        pass
