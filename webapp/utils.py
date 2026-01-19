import pycountry


def extract_diet_category(text):
    """
    Extracts a main diet category from a text description.
    Returns: 'Carnivore', 'Herbivore', 'Omnivore', 'Insectivore', or 'Unknown'
    """
    if not text or not isinstance(text, str):
        return 'Unknown'

    text_lower = text.lower()

    if 'herbivore' in text_lower or 'plant' in text_lower or 'grass' in text_lower or 'leaves' in text_lower:
        if 'carnivore' not in text_lower and 'omnivore' not in text_lower:
            return 'Herbivore'

    if 'carnivore' in text_lower or 'meat' in text_lower or 'prey' in text_lower:
        if 'herbivore' not in text_lower and 'omnivore' not in text_lower:
            return 'Carnivore'

    if 'omnivore' in text_lower:
        return 'Omnivore'

    if 'insect' in text_lower or 'bug' in text_lower:
        return 'Insectivore'

    # Default fallback based on keywords if explicit terms are missing
    if any(x in text_lower for x in ['hunt', 'fish', 'mammal']):
        return 'Carnivore'

    return 'Unknown'


def extract_habitat_category(text):
    """
    Extracts a main habitat category from a text description.
    """
    if not text or not isinstance(text, str):
        return 'Unknown'

    text_lower = text.lower()

    categories = {
        'Marine/Coastal': [
            'ocean', 'sea', 'marine', 'coral', 'reef', 'coast', 'coastal', 'shore', 'beach', 'island', 'gulf', 'bay',
        ],
        'Freshwater': [
            'river', 'lake', 'pond', 'stream', 'creek', 'freshwater', 'lagoon', 'delta', 'canal', 'estuary',
        ],
        'Forest/Jungle': ['forest', 'jungle', 'woodland', 'rainforest', 'canopy', 'amazon', 'taiga'],
        'Desert/Arid': ['desert', 'arid', 'sand', 'dune', 'sahara', 'semi-arid'],
        'Savanna/Grassland': ['savanna', 'grassland', 'plain', 'prairie', 'meadow', 'steppe'],
        'Wetlands/Swamp': ['wetland', 'swamp', 'marsh', 'bog', 'mangrove'],
        'Mountain/Highland': ['mountain', 'alpine', 'himalaya', 'rocky', 'plateau', 'highland'],
        'Polar/Tundra': ['polar', 'arctic', 'antarctic', 'tundra', 'ice', 'snow'],
        'Urban/Domestic': ['urban', 'city', 'town', 'village', 'farm', 'ranch', 'domestic', 'pet', 'zoo']
    }

    for category, keywords in categories.items():
        if any(keyword in text_lower for keyword in keywords):
            return category

    return 'Terrestrial (General)'


def extract_countries(locations):
    """
    Extracts ISO Alpha-3 country codes from a list of location strings.
    """
    if not locations or not isinstance(locations, list):
        return []

    found_countries = set()

    # Pre-calculate common overrides for speed
    overrides = {
        'USA': 'USA', 'United States': 'USA', 'America': 'USA',
        'UK': 'GBR', 'United Kingdom': 'GBR', 'Great Britain': 'GBR',
        'Russia': 'RUS',
        'China': 'CHN',
        'Tanzania': 'TZA'
    }

    for loc in locations:
        if not isinstance(loc, str):
            continue

        loc_clean = loc.strip()

        # Check overrides first
        if loc_clean in overrides:
            found_countries.add(overrides[loc_clean])
            continue

        # Check pycountry
        # Try exact match first
        try:
            country = pycountry.countries.get(name=loc_clean)
            if country:
                found_countries.add(country.alpha_3)
                continue
        except BaseException:
            pass

        # Fuzzy match / validation
        for country in pycountry.countries:
            if country.name in loc_clean or loc_clean in country.name:
                found_countries.add(country.alpha_3)
                break

    return list(found_countries)


def extract_countries_from_text(text):
    """
    Scans a text block for country names and returns a list of ISO Alpha-3 codes.
    """
    import re
    if not text or not isinstance(text, str):
        return []

    found_countries = set()
    
    # Common overrides dictionary (Name -> Alpha_3)
    overrides = {
        'USA': 'USA', 'United States': 'USA', 'America': 'USA',
        'UK': 'GBR', 'United Kingdom': 'GBR', 'Great Britain': 'GBR',
        'Russia': 'RUS',
        'China': 'CHN',
        'South Korea': 'KOR',
        'North Korea': 'PRK',
        'Vietnam': 'VNM',
        'Laos': 'LAO',
        'Tanzania': 'TZA',
        'Madagascar': 'MDG'
    }

    # 1. Check overrides
    for country_name, code in overrides.items():
        if country_name in text:
             found_countries.add(code)

    # 2. Check pycountry names with Regex boundaries to avoid partial matches
    # (e.g. avoiding 'India' matching inside 'Indian Ocean' if possible, though 'Indian' isn't 'India')
    # But 'Guinea' in 'Guinea Pig' is a problem. 
    # exclusion list for common false positives
    exclusions = ['Guinea', 'Turkey', 'Jordan', 'Jersey', 'Georgia'] 
    
    for country in pycountry.countries:
        try:
            name = country.name
            if name in exclusions: 
                continue
                
            # Regex for whole word match
            if re.search(r'\b' + re.escape(name) + r'\b', text, re.IGNORECASE):
                found_countries.add(country.alpha_3)
        except:
            continue

    return list(found_countries)
