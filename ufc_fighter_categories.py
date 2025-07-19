#!/usr/bin/env python3
"""
UFC Fighter Categories Database
Organizes UFC fighters by weight categories for dropdown selection.
"""

import json
import os
from typing import Dict, List

# UFC Weight Categories
UFC_CATEGORIES = {
    "Men": {
        "Flyweight": "Flyweight",
        "Bantamweight": "Bantamweight", 
        "Featherweight": "Featherweight",
        "Lightweight": "Lightweight",
        "Welterweight": "Welterweight",
        "Middleweight": "Middleweight",
        "Light Heavyweight": "Light Heavyweight",
        "Heavyweight": "Heavyweight",
        "Catch Weight": "Catch Weight",
        "Open Weight": "Open Weight"
    },
    "Women": {
        "Strawweight": "Women's Strawweight",
        "Flyweight": "Women's Flyweight",
        "Bantamweight": "Women's Bantamweight",
        "Featherweight": "Women's Featherweight",
        "Lightweight": "Women's Lightweight",
        "Catch Weight": "Women's Catch Weight"
    }
}

def load_fighter_data():
    """Load fighter data from JSON file."""
    try:
        with open("ufc_fighters_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ ufc_fighters_data.json not found!")
        print("Please run fetch_ufc_fighters.py first to get fighter data.")
        return {}

def organize_fighters_by_category(fighters_data: Dict) -> Dict:
    """Organize fighters by category for dropdown selection."""
    organized = {
        "categories": UFC_CATEGORIES,
        "fighters_by_category": {},
        "fighter_lookup": {}
    }
    
    # Initialize empty lists for each category
    for gender, categories in UFC_CATEGORIES.items():
        for category_key, category_name in categories.items():
            organized["fighters_by_category"][category_name] = []
    
    # Organize fighters into their categories
    for fighter_id, fighter_data in fighters_data.items():
        category = fighter_data.get("category", "")
        name = fighter_data.get("name", "")
        
        if category in organized["fighters_by_category"]:
            organized["fighters_by_category"][category].append({
                "id": fighter_id,
                "name": name,
                "nationality": fighter_data.get("nationality", ""),
                "record": f"{fighter_data.get('wins', 0)}-{fighter_data.get('losses', 0)}-{fighter_data.get('draws', 0)}",
                "logo_path": f"bot/static/logos/teams/FIGHTING/UFC/{name.replace(' ', '_').lower()}.png"
            })
            
            # Add to lookup for quick access
            organized["fighter_lookup"][fighter_id] = {
                "name": name,
                "category": category,
                "nationality": fighter_data.get("nationality", ""),
                "record": f"{fighter_data.get('wins', 0)}-{fighter_data.get('losses', 0)}-{fighter_data.get('draws', 0)}",
                "logo_path": f"bot/static/logos/teams/FIGHTING/UFC/{name.replace(' ', '_').lower()}.png"
            }
    
    # Sort fighters alphabetically within each category
    for category in organized["fighters_by_category"]:
        organized["fighters_by_category"][category].sort(key=lambda x: x["name"])
    
    return organized

def create_dropdown_data(organized_data: Dict) -> Dict:
    """Create dropdown-friendly data structure."""
    dropdown_data = {
        "gender_options": list(UFC_CATEGORIES.keys()),
        "category_options": {},
        "fighter_options": {}
    }
    
    # Create category options for each gender
    for gender, categories in UFC_CATEGORIES.items():
        dropdown_data["category_options"][gender] = list(categories.keys())
    
    # Create fighter options for each category
    for category_name, fighters in organized_data["fighters_by_category"].items():
        dropdown_data["fighter_options"][category_name] = [
            {
                "value": fighter["id"],
                "label": f"{fighter['name']} ({fighter['record']})",
                "nationality": fighter["nationality"],
                "logo_path": fighter["logo_path"]
            }
            for fighter in fighters
        ]
    
    return dropdown_data

def main():
    """Main function to organize fighter data."""
    print("🥊 Organizing UFC fighters by category...")
    
    # Load fighter data
    fighters_data = load_fighter_data()
    if not fighters_data:
        return
    
    # Organize fighters by category
    organized_data = organize_fighters_by_category(fighters_data)
    
    # Create dropdown data
    dropdown_data = create_dropdown_data(organized_data)
    
    # Save organized data
    with open("ufc_fighters_organized.json", "w") as f:
        json.dump(organized_data, f, indent=2)
    
    # Save dropdown data
    with open("ufc_fighters_dropdown.json", "w") as f:
        json.dump(dropdown_data, f, indent=2)
    
    # Print summary
    print(f"✅ Organized {len(fighters_data)} fighters into categories")
    print("📁 Saved to: ufc_fighters_organized.json")
    print("📁 Saved to: ufc_fighters_dropdown.json")
    
    # Print category summary
    print("\n📊 Category Summary:")
    for category, fighters in organized_data["fighters_by_category"].items():
        print(f"  {category}: {len(fighters)} fighters")

if __name__ == "__main__":
    main() 