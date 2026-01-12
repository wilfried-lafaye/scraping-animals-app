#!/usr/bin/env python3
"""Extract keywords for diet and habitat from full text descriptions"""
import os
from pymongo import MongoClient

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://scraper:scraper_password@localhost:27017")
client = MongoClient(MONGODB_URI)
db = client["animals_db"]
collection = db["animals"]

# Keyword mappings - avec plus de variantes
DIET_KEYWORDS = {
    "carnivore": ["carnivorous", "carniv", "meat", "prey", "hunt", "fish", "bird"],
    "herbivore": ["herbivorous", "herb", "grass", "plant", "leaf", "leaves", "vegetable", "seed"],
    "omnivore": ["omnivorous", "omniv", "both plant and meat", "eats both"],
    "insectivore": ["insectivorous", "insect", "arthropod", "invertebrat"],
    "piscivore": ["piscivorous", "pisciv", "fish"],
}

HABITAT_KEYWORDS = {
    "forest": ["forest", "woodland", "jungle", "rainforest", "tree", "wood"],
    "grassland": ["grassland", "prairie", "savanna", "grass", "steppe", "plain"],
    "desert": ["desert", "arid", "sand", "dry"],
    "ocean": ["ocean", "sea", "marine", "aquatic", "water", "reef", "coral"],
    "mountain": ["mountain", "alpine", "highland", "peak"],
    "river": ["river", "freshwater", "stream", "creek", "pond"],
    "cave": ["cave", "underground", "burrow"],
}

def extract_keywords(text, keyword_dict):
    """Extract keywords from text"""
    if not text:
        return []
    
    text_lower = text.lower()
    found = []
    
    for keyword, patterns in keyword_dict.items():
        for pattern in patterns:
            if pattern in text_lower:
                found.append(keyword)
                break
    
    return list(set(found))  # Remove duplicates

# Update all animals
updated = 0
for animal in collection.find():
    updates = {}
    
    # Extract diet keywords
    if animal.get("diet"):
        diet_tags = extract_keywords(animal["diet"], DIET_KEYWORDS)
        if diet_tags:
            updates["diet_tags"] = diet_tags[:1]  # Keep only first tag
    
    # Extract habitat keywords
    if animal.get("habitat"):
        habitat_tags = extract_keywords(animal["habitat"], HABITAT_KEYWORDS)
        if habitat_tags:
            updates["habitat_tags"] = habitat_tags[:1]  # Keep only first tag
    
    # Update document
    if updates:
        collection.update_one({"_id": animal["_id"]}, {"$set": updates})
        updated += 1

print(f"✅ {updated} animaux enrichis avec des keywords!")

# Show example
example = collection.find_one({"animal_name": "Garden Eel"})
if example:
    print(f"\nExemple - {example.get('animal_name')}:")
    print(f"  Diet tags: {example.get('diet_tags', [])}")
    print(f"  Habitat tags: {example.get('habitat_tags', [])}")

