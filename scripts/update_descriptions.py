#!/usr/bin/env python3
"""
Script to update descriptions for animals in MongoDB
by scraping them from their URLs.
"""

import sys
import time
import requests
from lxml import html
from pymongo import MongoClient

# MongoDB connection
MONGODB_URI = "mongodb://scraper:scraper_password@mongodb:27017/"
DATABASE_NAME = "animals_db"
COLLECTION_NAME = "animals"

def extract_description(url):
    """Extract description from animal page."""
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if response.status_code != 200:
            return None
        
        tree = html.fromstring(response.content)
        
        # Extract paragraphs from main content
        paragraphs = tree.xpath('//div[@id="single-animal-text"]//p//text()')
        
        if paragraphs:
            # Join and clean text
            text = ' '.join([p.strip() for p in paragraphs if p.strip() and len(p.strip()) > 20])
            
            # Limit to reasonable length
            if text and len(text) > 500:
                text = text[:500] + "..."
            
            return text if text else None
        
        return None
        
    except Exception as e:
        print(f"Error extracting description from {url}: {e}")
        return None


def main():
    """Main function to update descriptions."""
    print("🔄 Connecting to MongoDB...")
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    # Find all animals without descriptions
    animals_without_desc = list(collection.find(
        {"description": None},
        {"_id": 1, "animal_name": 1, "url": 1}
    ))
    
    total = len(animals_without_desc)
    print(f"📊 Found {total} animals without descriptions")
    
    if total == 0:
        print("✅ All animals already have descriptions!")
        return
    
    updated = 0
    failed = 0
    
    print(f"\n🚀 Starting to update descriptions...")
    
    for i, animal in enumerate(animals_without_desc, 1):
        animal_id = animal['_id']
        animal_name = animal['animal_name']
        url = animal.get('url')
        
        print(f"[{i}/{total}] Processing: {animal_name}...", end=' ')
        
        if not url:
            print("❌ No URL")
            failed += 1
            continue
        
        # Extract description
        description = extract_description(url)
        
        if description:
            # Update in MongoDB
            collection.update_one(
                {"_id": animal_id},
                {"$set": {"description": description}}
            )
            print("✅")
            updated += 1
        else:
            print("❌ Failed")
            failed += 1
        
        # Be respectful to the server
        time.sleep(0.2)
    
    print(f"\n✅ Update complete!")
    print(f"   - Updated: {updated}")
    print(f"   - Failed: {failed}")
    print(f"   - Total: {total}")
    
    client.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
