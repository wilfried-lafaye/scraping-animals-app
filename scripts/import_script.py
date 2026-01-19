import json
import os
from pymongo import MongoClient

# Configuration
# Inside docker, hostname is 'mongodb', on host it's 'localhost' (but we run this inside docker)
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://scraper:scraper_password@mongodb:27017/animals_db?authSource=admin")
DB_NAME = "animals_db"
COLLECTION_NAME = "animals"
JSON_FILE = "animals.json" # Relative path, assuming we copy it to WORKDIR

def import_data():
    print(f"Connecting to MongoDB at {MONGO_URI}...")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    # Drop existing collection to avoid duplicates/stale data
    print("Dropping existing collection...")
    collection.drop()

    print(f"Reading data from {JSON_FILE}...")
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        # Attempt 1: Standard Load
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            print("Standard JSON load failed. Attempting repair...")
            
            # Repair logic for Scrapy feed export weirdness
            # defined as: [ ] {obj}, {obj}, ...
            # We will try to make it a valid list: [ {obj}, {obj} ]
            
            # Remove existing brackets to start fresh
            clean_content = content.replace('[', '').replace(']', '')
            
            # Remove trailing comma if present
            if clean_content.strip().endswith(','):
                clean_content = clean_content.strip()[:-1]
                
            # Re-wrap in brackets
            fixed_content = f"[{clean_content}]"
            
            try:
                data = json.loads(fixed_content)
                print("Repair successful!")
            except json.JSONDecodeError:
                print("Repair failed. Trying line-by-line...")
                # Fallback: Parse individual lines
                data = []
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    # Remove trailing comma
                    if line.endswith(','):
                        line = line[:-1]
                    try:
                        # Skip standalone brackets
                        if line == '[' or line == ']': continue
                        obj = json.loads(line)
                        data.append(obj)
                    except:
                        pass
                        
        if isinstance(data, list) and len(data) > 0:
            print(f"Found {len(data)} records. Inserting...")
            collection.insert_many(data)
            print("Import successful!")
        else:
            print("JSON is empty or valid records count is 0.")

    except Exception as e:
        print(f"Critical error: {e}")

if __name__ == "__main__":
    import_data()
