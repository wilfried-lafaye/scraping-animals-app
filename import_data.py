#!/usr/bin/env python3
"""Import animal data from JSON to MongoDB"""
import json
import os
from pymongo import MongoClient

# Configuration
MONGODB_URI = "mongodb://scraper:scraper_password@localhost:27017/animals_db?authSource=admin"
DATABASE_NAME = "animals_db"
COLLECTION_NAME = "animals"

def import_data():
    # Chemin absolu du fichier JSON
    json_path = os.path.join(os.path.dirname(__file__), 'data', 'animals.json')
    
    # Vérifier que le fichier existe
    if not os.path.exists(json_path):
        print(f"❌ Fichier non trouvé: {json_path}")
        return
    
    # Connexion MongoDB
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    # Charger les données JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        animals = json.load(f)
    
    # Supprimer les anciennes données
    collection.delete_many({})
    
    # Insérer les nouvelles données
    if animals:
        result = collection.insert_many(animals)
        print(f"✅ {len(result.inserted_ids)} animaux importés avec succès!")
        
        # Afficher un exemple
        example = collection.find_one({})
        print(f"Exemple: {example.get('animal_name', 'N/A')}")
    else:
        print("❌ Aucune donnée à importer")

if __name__ == '__main__':
    import_data()
