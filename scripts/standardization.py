#!/usr/bin/env python3
"""
Shared standardization utilities for animal data.
Used by both the Scrapy pipeline and the enrichment script.
"""
import re


def parse_range(value_str: str) -> tuple:
    """
    Parse a string containing numbers and return (min_val, max_val).
    Handles patterns like: "10-20", "up to 50", "5"
    Returns (None, None) if no numbers found.
    """
    if not value_str or not isinstance(value_str, str):
        return None, None

    # Normalize: replace en-dash with hyphen, remove commas
    value_str = value_str.replace("–", "-").replace(",", "")
    
    # Extract all floating point numbers
    numbers = [float(x) for x in re.findall(r"(\d*\.?\d+)", value_str)]
    
    if not numbers:
        return None, None
    
    if len(numbers) == 1:
        return numbers[0], numbers[0]
    
    if len(numbers) >= 2:
        return min(numbers), max(numbers)
        
    return None, None


def convert_unit(value: float, unit: str, type_: str) -> float:
    """
    Convert value to standard unit based on type.
    Standard units: Speed -> km/h, Weight -> kg, Length -> cm
    """
    unit = unit.lower().strip()
    
    if type_ == 'speed':
        if 'mph' in unit or 'mile' in unit:
            return value * 1.60934
        if 'km/h' in unit or 'kph' in unit:
            return value
            
    elif type_ == 'weight':
        if 'lbs' in unit or 'pound' in unit:
            return value * 0.453592
        if 'oz' in unit or 'ounce' in unit:
            return value * 0.0283495
        if 'kg' in unit:
            return value
        if 'g' in unit and 'kg' not in unit:
            return value / 1000.0
        if 'ton' in unit:
            return value * 907.185
            
    elif type_ == 'length':
        if 'inch' in unit:
            return value * 2.54
        if 'ft' in unit or 'feet' in unit or 'foot' in unit:
            return value * 30.48
        if 'm' in unit and 'cm' not in unit and 'mm' not in unit and 'mile' not in unit:
            return value * 100.0
        if 'cm' in unit:
            return value
        if 'mm' in unit:
            return value / 10.0
    
    return value


def parse_with_unit(text: str, value_type: str) -> tuple:
    """
    Extract numbers and identify units to convert to standard.
    Returns (min_std, max_std).
    """
    if not text:
        return None, None
        
    min_v, max_v = parse_range(text)
    if min_v is None:
        return None, None

    text_lower = text.lower()
    unit = "unknown"
    
    if value_type == 'speed':
        if 'mph' in text_lower:
            unit = 'mph'
        elif 'km' in text_lower:
            unit = 'km/h'
    elif value_type == 'weight':
        if 'lbs' in text_lower or 'pound' in text_lower:
            unit = 'lbs'
        elif 'kg' in text_lower:
            unit = 'kg'
        elif 'oz' in text_lower:
            unit = 'oz'
        elif 'gram' in text_lower or text_lower.endswith('g') or ' g ' in text_lower:
            unit = 'g'
        elif 'ton' in text_lower:
            unit = 'tons'
    elif value_type == 'length':
        if 'inch' in text_lower or '"' in text_lower:
            unit = 'inch'
        elif 'centimeter' in text_lower or 'cm' in text_lower:
            unit = 'cm'
        elif 'meter' in text_lower:
            if 'cm' not in text_lower and 'mm' not in text_lower and 'km' not in text_lower:
                unit = 'm'
        elif 'feet' in text_lower or 'ft' in text_lower:
            unit = 'ft'
    
    min_std = convert_unit(min_v, unit, value_type)
    max_std = convert_unit(max_v, unit, value_type)
    
    return round(min_std, 2), round(max_std, 2)


def standardize_animal(animal: dict) -> dict:
    """
    Standardize an animal's data fields.
    Converts text-based facts to standardized numeric fields.
    """
    facts = animal.get('facts', {})
    
    # --- Top Speed ---
    speed_text = facts.get('Top Speed') if facts else None
    if speed_text:
        _, max_s = parse_with_unit(speed_text, 'speed')
        if max_s:
            animal['top_speed_kph'] = max_s

    # --- Weight ---
    if facts:
        weights = []
        for k, v in facts.items():
            if 'weight' in k.lower():
                min_w, max_w = parse_with_unit(v, 'weight')
                if min_w is not None:
                    weights.extend([min_w, max_w])
        if weights:
            animal['weight_min_kg'] = min(weights)
            animal['weight_max_kg'] = max(weights)

    # --- Length ---
    length_text = facts.get('Length') if facts else None
    if length_text:
        min_l, max_l = parse_with_unit(length_text, 'length')
        if min_l is not None:
            animal['length_min_cm'] = min_l
            animal['length_max_cm'] = max_l

    # --- Lifespan ---
    lifespan_text = facts.get('Lifespan') if facts else None
    if lifespan_text:
        min_l, max_l = parse_range(lifespan_text)
        if min_l:
            animal['lifespan_min_years'] = min_l
            animal['lifespan_max_years'] = max_l

    # --- Litter Size ---
    litter_text = (facts.get('Litter Size') or facts.get('Average Litter Size')) if facts else None
    if litter_text:
        min_l, max_l = parse_range(litter_text)
        if min_l:
            animal['litter_size_min'] = int(min_l)
            animal['litter_size_max'] = int(max_l)

    return animal
