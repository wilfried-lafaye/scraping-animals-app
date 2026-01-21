import os
from elasticsearch import Elasticsearch


class SearchClient:
    def __init__(self):
        # Default to localhost if not set (for local dev), otherwise use env var (for docker)
        es_url = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")
        try:
            self.es = Elasticsearch(es_url)
            self.index_name = "animals"
        except Exception as e:
            print(f"Failed to connect to Elasticsearch: {e}")
            self.es = None

    def is_connected(self):
        if not self.es:
            return False
        try:
            return self.es.ping()
        except Exception:
            return False

    def search_animals(self, query_text):
        """
        Search for animals matching the query text.
        Returns a list of animal names.
        """
        if not self.is_connected() or not query_text:
            return []

        # Multi-match query searching across important fields
        body = {
            "query": {
                "multi_match": {
                    "query": query_text,
                    "fields": ["animal_name^3", "description", "key_facts", "scientific_name"],
                    "fuzziness": "AUTO"
                }
            },
            "_source": ["animal_name"],
            "size": 50  # Limit results
        }

        try:
            res = self.es.search(index=self.index_name, body=body)
            hits = res.get("hits", {}).get("hits", [])
            return [hit["_source"]["animal_name"] for hit in hits]
        except Exception as e:
            print(f"Search error: {e}")
            return []
