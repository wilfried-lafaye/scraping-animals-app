#!/usr/bin/env python3
"""
Script pour charger les données des animaux dans MongoDB au démarrage de la webapp
"""
import json
import time
import os
import sys
from pymongo import MongoClient

def load_animals_data():
    """Charge les données des animaux depuis animals.json dans MongoDB"""
    
    MONGODB_URI = os.getenv(
        "MONGODB_URI", 
        "mongodb://scraper:scraper_password@mongodb:27017/animals_db?authSource=admin"
    )
    # Essayer plusieurs chemins possibles
    possible_paths = [
        "/data/animals.json",
        "/app/../scrapy/data/animals.json",
        "./scrapy/data/animals.json",
        "/workspaces/scraping-animals-app/scrapy/data/animals.json"
    ]
    
    json_file = None
    for path in possible_paths:
        if os.path.exists(path):
            json_file = path
            print(f"✓ Found animals.json at: {path}")
            break
    
    if not json_file:
        print(f"✗ Could not find animals.json in any of these paths:")
        for path in possible_paths:
            print(f"  - {path}")
        return False
    
    # Attendre que MongoDB soit prêt
    max_retries = 30
    for attempt in range(max_retries):
        try:
            client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
            client.admin.command("ping")
            print("✓ MongoDB is ready")
            break
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"✗ MongoDB not available after {max_retries} attempts")
                return False
            time.sleep(1)
    
    try:
        db = client['animals_db']
        collection = db['animals']
        
        # Vérifier si les données sont déjà chargées
        count = collection.count_documents({})
        if count > 0:
            print(f"✓ {count} animal records already in database")
            return True
        
        print(f"Loading animals data from {json_file}...")
        
        # Lire et charger les données
        with open(json_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        print(f"File size: {len(content)} bytes")
        
        # Essayer le parse standard
        try:
            data = json.loads(content)
            print("✓ Standard JSON parse successful")
        except json.JSONDecodeError as e:
            print(f"Standard JSON parse failed at line {e.lineno}: {e.msg}")
            # Essayer de récupérer du JSON valide depuis la fin du fichier
            # Commencer à chercher un closing bracket [ ou ]
            if content.count('}') > content.count(']'):
                # C'est un array d'objects
                # Chercher le dernier ] valide
                last_bracket = content.rfind(']')
                if last_bracket > 0:
                    content_to_parse = content[:last_bracket + 1]
                    try:
                        data = json.loads(content_to_parse)
                        print(f"✓ Recovered {len(data)} records from truncated file")
                    except:
                        print("Failed to recover from truncated file, trying line-by-line...")
                        data = []
                else:
                    data = []
            else:
                data = []
            
            # Fallback: Parse line by line
            if not data:
                print("Trying line-by-line parsing...")
                data = []
                in_object = False
                current_object = ""
                
                for line in content.split('\n'):
                    line = line.rstrip()
                    if line == '[':
                        in_object = False
                        continue
                    elif line == ']':
                        if current_object:
                            current_object += '\n' + line
                            in_object = False
                    elif line.startswith('{'):
                        current_object = line
                        in_object = True
                    elif in_object:
                        current_object += '\n' + line
                    
                    # Check if object is complete
                    if current_object and current_object.rstrip().endswith('},'):
                        try:
                            obj = json.loads(current_object.rstrip()[:-1])  # Remove trailing comma
                            data.append(obj)
                            current_object = ""
                        except:
                            pass
                    elif current_object and current_object.rstrip().endswith('}'):
                        try:
                            obj = json.loads(current_object)
                            data.append(obj)
                            current_object = ""
                        except:
                            pass
                
                print(f"✓ Line-by-line parsing found {len(data)} objects")
        
        # Nettoyer les données
        if isinstance(data, list):
            data = [doc for doc in data if isinstance(doc, dict)]
        
        if isinstance(data, list) and len(data) > 0:
            collection.insert_many(data)
            print(f"✓ Successfully loaded {len(data)} animal records into MongoDB")
            return True
        else:
            print("✗ No valid data found in JSON file after parsing")
            return False
            
    except Exception as e:
        print(f"✗ Error loading data: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()

if __name__ == "__main__":
    success = load_animals_data()
    sys.exit(0 if success else 1)
