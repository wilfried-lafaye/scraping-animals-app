#!/usr/bin/env python3
"""
Enrich animals.json with missing data from Wikipedia and Wikidata APIs.
- FETCHES IN ONE CALL: Description, Image, Wikidata ID
- Weight, length, lifespan from Wikidata
- Standardizes all data inline
"""
import json
import requests
import time
import re
from pathlib import Path
from standardization import standardize_animal


def get_wikipedia_data(animal_name: str, scientific_name: str = None) -> dict:
    """
    Fetch all available data from Wikipedia API in one go:
    - Description (extract)
    - Image (originalimage)
    - Wikidata ID (wikibase_item)
    """
    base_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
    
    for name in [scientific_name, animal_name]:
        if not name:
            continue
        
        wiki_name = name.strip().replace(" ", "_")
        
        try:
            response = requests.get(
                f"{base_url}{wiki_name}",
                headers={"User-Agent": "AnimalEnricher/1.0"},
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                
                # We need at least SOMETHING useful
                result = {}
                
                # Cipher description
                extract = data.get('extract')
                if extract and len(extract) > 50:
                    result['description'] = extract
                
                # Cipher image
                if 'originalimage' in data:
                    result['image_url'] = data['originalimage'].get('source')
                elif 'thumbnail' in data:
                    result['image_url'] = data['thumbnail'].get('source')
                    
                # Cipher Wikidata ID
                result['wikidata_id'] = data.get('wikibase_item')
                
                if result:
                    return result
                    
        except Exception as e:
            print(f"  Wikipedia error for {name}: {e}")
            continue
    
    return {}


def get_wikidata_properties(entity_id: str) -> dict:
    """Fetch structured data from Wikidata."""
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json"
    
    try:
        response = requests.get(url, headers={"User-Agent": "AnimalEnricher/1.0"}, timeout=15)
        if not response.ok:
            return {}
        
        data = response.json()
        entity = data.get('entities', {}).get(entity_id, {})
        claims = entity.get('claims', {})
        
        result = {}
        
        # P2067 = mass (weight)
        if 'P2067' in claims:
            try:
                mass_claim = claims['P2067'][0]['mainsnak']['datavalue']['value']
                amount = float(mass_claim.get('amount', 0))
                unit = mass_claim.get('unit', '')
                
                # Check for kg (Q11570) or gram (Q41803)
                if 'Q11570' in unit or 'kilogram' in unit:
                    result['weight_kg'] = amount
                elif 'Q41803' in unit or 'gram' in unit:
                    result['weight_kg'] = amount / 1000
                else:
                    # Generic fallback passed to standardizer if needed, but here we try to be precise
                     pass
            except Exception: pass
        
        # P2043 = length
        if 'P2043' in claims:
            try:
                length_claim = claims['P2043'][0]['mainsnak']['datavalue']['value']
                amount = float(length_claim.get('amount', 0))
                unit = length_claim.get('unit', '')
                
                # Check for meter (Q11573) or cm (Q174728)
                if 'Q11573' in unit or 'metre' in unit or 'meter' in unit:
                    result['length_cm'] = amount * 100
                elif 'Q174728' in unit or 'centimetre' in unit or 'centimeter' in unit:
                    result['length_cm'] = amount
            except Exception: pass
        
        # P2250 = lifespan
        if 'P2250' in claims:
            try:
                lifespan_claim = claims['P2250'][0]['mainsnak']['datavalue']['value']
                amount = float(lifespan_claim.get('amount', 0))
                unit = lifespan_claim.get('unit', '')
                
                # Check for year (Q577)
                if 'Q577' in unit or 'year' in unit or 'annum' in unit:
                    result['lifespan_years'] = amount
            except Exception: pass
        
        # P141 = conservation status
        if 'P141' in claims:
            try:
                status_id = claims['P141'][0]['mainsnak']['datavalue']['value']['id']
                status_map = {
                    'Q211005': 'Least Concern',
                    'Q719675': 'Near Threatened',
                    'Q278113': 'Vulnerable',
                    'Q11394': 'Endangered',
                    'Q219127': 'Critically Endangered',
                    'Q239509': 'Extinct in the Wild',
                    'Q237350': 'Extinct',
                }
                if status_id in status_map:
                    result['conservation_status'] = status_map[status_id]
            except Exception: pass
        
        return result
        
    except Exception as e:
        print(f"  Wikidata error: {e}")
        return {}


def enrich_animals(json_path: str, output_path: str = None):
    """Enrich animals.json with Wikipedia/Wikidata data."""
    if output_path is None:
        output_path = json_path
    
    print(f"Loading animals from {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        animals = json.load(f)
    
    print(f"Found {len(animals)} animals\n")
    
    stats = {
        'description_added': 0,
        'image_added': 0,
        'weight_added': 0,
        'length_added': 0,
        'lifespan_added': 0,
        'status_added': 0,
        'skipped': 0
    }
    
    for i, animal in enumerate(animals):
        animal_name = animal.get('animal_name', 'Unknown')
        scientific_name = animal.get('scientific_name')
        
        # Determine if we need to fetch anything
        missing_desc = not animal.get('description') or len(str(animal.get('description', ''))) < 50
        missing_image = not animal.get('image_url') or not animal.get('image_url', '').startswith('http')
        missing_stats = (
            (not animal.get('weight_min_kg')) or 
            (not animal.get('lifespan_min_years'))
        )
        
        if not (missing_desc or missing_image or missing_stats):
            stats['skipped'] += 1
            continue
        
        print(f"[{i+1}/{len(animals)}] Enriching: {animal_name}...")
        
        # 1. Fetch from Wikipedia (One call for Desc + Image + ID)
        wiki_data = get_wikipedia_data(animal_name, scientific_name)
        
        # Update Description
        if missing_desc and wiki_data.get('description'):
            animal['description'] = wiki_data['description']
            animal['description_source'] = 'wikipedia'
            stats['description_added'] += 1
            print(f"  ✓ Added description")
            
        # Update Image
        if missing_image and wiki_data.get('image_url'):
            animal['image_url'] = wiki_data['image_url']
            animal['image_source'] = 'wikipedia'
            stats['image_added'] += 1
            print(f"  ✓ Added image")
            
        # 2. Fetch from Wikidata (if ID found and stats missing)
        wikidata_id = wiki_data.get('wikidata_id')
        if wikidata_id and missing_stats:
            props = get_wikidata_properties(wikidata_id)
            
            if props.get('weight_kg') and not animal.get('weight_min_kg'):
                animal['weight_min_kg'] = props['weight_kg']
                animal['weight_max_kg'] = props['weight_kg']
                animal['weight_source'] = 'wikidata'
                stats['weight_added'] += 1
                print(f"  ✓ Added weight: {props['weight_kg']} kg")
            
            if props.get('length_cm') and not animal.get('length_cm'):
                animal['length_cm'] = props['length_cm']
                animal['length_source'] = 'wikidata'
                stats['length_added'] += 1
                print(f"  ✓ Added length: {props['length_cm']} cm")
            
            if props.get('lifespan_years') and not animal.get('lifespan_min_years'):
                animal['lifespan_min_years'] = props['lifespan_years']
                animal['lifespan_max_years'] = props['lifespan_years']
                animal['lifespan_source'] = 'wikidata'
                stats['lifespan_added'] += 1
                print(f"  ✓ Added lifespan: {props['lifespan_years']} years")
            
            if props.get('conservation_status') and not animal.get('conservation_status'):
                animal['conservation_status'] = props['conservation_status']
                stats['status_added'] += 1
                print(f"  ✓ Added status: {props['conservation_status']}")
            
            # Tag stats source
            if stats['weight_added'] or stats['length_added'] or stats['lifespan_added']:
                animal['stats_source'] = 'wikidata'
        
        # Standardize data after enrichment
        animal = standardize_animal(animal)
        animals[i] = animal
        
        # Rate limiting
        time.sleep(0.3)
    
    print(f"\n{'='*50}")
    print(f"Enrichment Summary:")
    print(f"  Descriptions added: {stats['description_added']}")
    print(f"  Images added:       {stats['image_added']}")
    print(f"  Weights added:      {stats['weight_added']}")
    print(f"  Lengths added:      {stats['length_added']}")
    print(f"  Lifespans added:    {stats['lifespan_added']}")
    print(f"  Conservation added: {stats['status_added']}")
    print(f"  Skipped (complete): {stats['skipped']}")
    print(f"{'='*50}")
    
    # Save
    print(f"\nSaving to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(animals, f, indent=2, ensure_ascii=False)
    
    print("Done!")


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    default_json = script_dir.parent / "scrapy" / "data" / "animals.json"
    
    if default_json.exists():
        enrich_animals(str(default_json))
    else:
        print(f"Error: {default_json} not found")
