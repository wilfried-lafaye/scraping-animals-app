"""Script pour mettre à jour le conservation status depuis le site web"""
import json
import requests
from lxml import html
import time
from pymongo import MongoClient
import os

# MongoDB connection
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://scraper:scraper_password@localhost:27017/animals_db?authSource=admin')
client = MongoClient(MONGODB_URI)
db = client['animals_db']
collection = db['animals']

def extract_conservation_status(url):
    """Extract conservation status from an animal page"""
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, timeout=10)
        if response.status_code != 200:
            return None
            
        tree = html.fromstring(response.content)
        
        # Extract conservation status using XPath
        status_list = tree.xpath('//h2[contains(text(), "Conservation Status")]/following-sibling::ul//a/text()')
        
        if status_list:
            return ', '.join(status_list)
        return None
        
    except Exception as e:
        print(f"Error extracting from {url}: {e}")
        return None

def main():
    # Get all animals from database
    animals = list(collection.find({}, {'_id': 1, 'animal_name': 1, 'url': 1, 'conservation_status': 1}))
    total = len(animals)
    
    print(f"Found {total} animals in database")
    print("Starting conservation status update...")
    
    updated_count = 0
    already_has = 0
    not_found = 0
    
    for i, animal in enumerate(animals, 1):
        animal_name = animal.get('animal_name', 'Unknown')
        url = animal.get('url')
        current_status = animal.get('conservation_status')
        
        # Skip if already has conservation status
        if current_status:
            already_has += 1
            if i % 100 == 0:
                print(f"Progress: {i}/{total} ({updated_count} updated, {already_has} already had, {not_found} not found)")
            continue
        
        if not url:
            not_found += 1
            continue
        
        # Extract conservation status
        status = extract_conservation_status(url)
        
        if status:
            # Update in database
            collection.update_one(
                {'_id': animal['_id']},
                {'$set': {'conservation_status': status}}
            )
            updated_count += 1
            print(f"[{i}/{total}] ✅ {animal_name}: {status}")
        else:
            not_found += 1
            if i % 50 == 0:
                print(f"[{i}/{total}] ❌ {animal_name}: No conservation status found")
        
        # Be respectful: rate limit
        time.sleep(0.5)
        
        # Progress update every 100 animals
        if i % 100 == 0:
            print(f"Progress: {i}/{total} ({updated_count} updated, {already_has} already had, {not_found} not found)")
    
    print(f"\n{'='*60}")
    print(f"Update completed!")
    print(f"Total animals: {total}")
    print(f"Already had status: {already_has}")
    print(f"Newly updated: {updated_count}")
    print(f"Not found: {not_found}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
