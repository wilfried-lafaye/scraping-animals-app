import json
import os
from elasticsearch import Elasticsearch, helpers

# Configuration
ES_HOST = "http://localhost:9200"
INDEX_NAME = "animals"
DATA_FILE = os.path.join(os.path.dirname(__file__), '../scrapy/data/animals.json')

def create_index(es):
    """Create the index with specific mappings."""
    if es.indices.exists(index=INDEX_NAME):
        print(f"Index '{INDEX_NAME}' already exists. Deleting it...")
        es.indices.delete(index=INDEX_NAME)

    mappings = {
        "properties": {
            "animal_name": {"type": "text", "analyzer": "standard"},
            "scientific_name": {"type": "text"},
            "description": {"type": "text", "analyzer": "english"},
            "key_facts": {"type": "text", "analyzer": "english"},
            "locations": {"type": "keyword"},
            "diet": {"type": "keyword"},
            "habitat": {"type": "keyword"},
            "conservation_status": {"type": "keyword"}
        }
    }

    es.indices.create(index=INDEX_NAME, mappings=mappings)
    print(f"Index '{INDEX_NAME}' created.")

def generate_actions(data):
    """Generator for bulk indexing."""
    for animal in data:
        yield {
            "_index": INDEX_NAME,
            "_source": {
                "animal_name": animal.get("animal_name"),
                "scientific_name": animal.get("scientific_name"),
                "description": animal.get("description"),
                "key_facts": animal.get("key_facts", []),
                "locations": animal.get("locations", []),
                "diet": animal.get("diet"),
                "habitat": animal.get("habitat"),
                "conservation_status": animal.get("conservation_status"),
                "image_url": animal.get("image_url"),
                "source_url": animal.get("url")
            }
        }

def main():
    # Connect to Elasticsearch
    try:
        es = Elasticsearch(ES_HOST)
        if not es.ping():
            raise ValueError("Connection failed")
        print(f"Connected to Elasticsearch at {ES_HOST}")
    except Exception as e:
        print(f"Error connecting to Elasticsearch: {e}")
        return

    # Load Data
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Loaded {len(data)} animals from {DATA_FILE}")
    except FileNotFoundError:
        print(f"File not found: {DATA_FILE}")
        return

    # Create Index
    create_index(es)

    # Bulk Index
    print("Indexing data...")
    success, failed = helpers.bulk(es, generate_actions(data), stats_only=True)
    print(f"Indexing complete: {success} successful, {failed} failed.")

if __name__ == "__main__":
    main()
