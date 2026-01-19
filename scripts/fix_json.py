#!/usr/bin/env python3
"""Fix corrupted JSON file"""
import json
import re

# Lire le fichier
with open('data/animals.json', 'r', encoding='utf-8') as f:
    content = f.read()

# Supprimer les caractères de contrôle invalides (sauf newline, tab, carriage return)
content = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F]', '', content)

# Corriger les doubles guillemets à la fin des valeurs ("",)
content = re.sub(r'"",\s*\n', '",\n', content)

# Essayer de parser
try:
    data = json.loads(content)
    print(f"✅ JSON corrigé ! {len(data)} animaux")
    
    # Réécrire
    with open('data/animals.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print("✅ Fichier sauvegardé !")
except json.JSONDecodeError as e:
    print(f"❌ Erreur : {e}")
