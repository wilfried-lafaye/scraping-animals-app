#!/usr/bin/env python3
"""Enrich animal data from 'facts' field to main fields"""
import json
from pymongo import MongoClient

MONGODB_URI = "mongodb://scraper:scraper_password@localhost:27017/animals_db?authSource=admin"
DATABASE_NAME = "animals_db"
COLLECTION_NAME = "animals"

def enrich_animals():
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    # Récupérer tous les animaux
    animals = list(collection.find({}))
    
    updated_count = 0
    
    for animal in animals:
        facts = animal.get('facts', {})
        update_data = {}
        
        # Extraire habitat
        if not animal.get('habitat') and facts.get('Habitat'):
            update_data['habitat'] = facts['Habitat']
        
        # Extraire diet
        if not animal.get('diet') and facts.get('Diet'):
            update_data['diet'] = facts['Diet']
        
        # Extraire conservation status
        if not animal.get('conservation_status') and facts.get('Biggest Threat'):
            update_data['conservation_status'] = facts['Biggest Threat']
        
        # Mettre à jour si des données ont été extraites
        if update_data:
            collection.update_one(
                {'_id': animal['_id']},
                {'$set': update_data}
            )
            updated_count += 1
    
    print(f"✅ {updated_count} animaux enrichis!")
    
    # Afficher quelques exemples
    example = collection.find_one({'habitat': {'$ne': None}})
    if example:
        print(f"\nExemple - {example.get('animal_name')}:")
        print(f"  Habitat: {example.get('habitat')}")
        print(f"  Diet: {example.get('diet')}")
        print(f"  Status: {example.get('conservation_status')}")

if __name__ == '__main__':
    enrich_animals()
