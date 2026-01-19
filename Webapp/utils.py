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
        'Ocean/Marine': ['ocean', 'sea', 'marine', 'coral', 'reef', 'pacific', 'atlantic'],
        'Forest/Jungle': ['forest', 'jungle', 'woodland', 'rainforest', 'canopy', 'amazon'],
        'Desert': ['desert', 'arid', 'sand', 'dune', 'sahara'],
        'Savanna/Grassland': ['savanna', 'grassland', 'plain', 'prairie', 'meadow'],
        'Wetlands/Swamp': ['wetland', 'swamp', 'marsh', 'bog', 'mangrove', 'river', 'lake'],
        'Mountain': ['mountain', 'alpine', 'himalaya', 'rocky'],
        'Polar/Tundra': ['polar', 'arctic', 'antarctic', 'tundra', 'ice', 'snow'],
        'Urban/Domestic': ['urban', 'city', 'farm', 'house', 'pet']
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
