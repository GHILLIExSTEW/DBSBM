"""
UFC Fighter Service
Handles UFC fighter selection and category management for dropdowns.
"""

import json
import os
from typing import Dict, List, Optional
from pathlib import Path

class UFCFighterService:
    def __init__(self):
        self.organized_data = {}
        self.dropdown_data = {}
        self.load_fighter_data()
    
    def load_fighter_data(self):
        """Load organized fighter data."""
        try:
            # Try to load from the project root
            organized_path = Path("ufc_fighters_organized.json")
            dropdown_path = Path("ufc_fighters_dropdown.json")
            
            if organized_path.exists():
                with open(organized_path, "r") as f:
                    self.organized_data = json.load(f)
            
            if dropdown_path.exists():
                with open(dropdown_path, "r") as f:
                    self.dropdown_data = json.load(f)
                    
        except Exception as e:
            print(f"Warning: Could not load UFC fighter data: {e}")
    
    def get_gender_options(self) -> List[str]:
        """Get available gender options (Men/Women)."""
        return self.dropdown_data.get("gender_options", [])
    
    def get_category_options(self, gender: str) -> List[str]:
        """Get category options for a specific gender."""
        return self.dropdown_data.get("category_options", {}).get(gender, [])
    
    def get_fighter_options(self, category: str) -> List[Dict]:
        """Get fighter options for a specific category."""
        return self.dropdown_data.get("fighter_options", {}).get(category, [])
    
    def get_fighter_by_id(self, fighter_id: str) -> Optional[Dict]:
        """Get fighter data by ID."""
        return self.organized_data.get("fighter_lookup", {}).get(fighter_id)
    
    def get_fighters_by_category(self, category: str) -> List[Dict]:
        """Get all fighters in a specific category."""
        return self.organized_data.get("fighters_by_category", {}).get(category, [])
    
    def search_fighters(self, query: str, limit: int = 10) -> List[Dict]:
        """Search fighters by name."""
        results = []
        query_lower = query.lower()
        
        for fighter_id, fighter_data in self.organized_data.get("fighter_lookup", {}).items():
            if query_lower in fighter_data["name"].lower():
                results.append({
                    "id": fighter_id,
                    **fighter_data
                })
                if len(results) >= limit:
                    break
        
        return results
    
    def get_category_stats(self) -> Dict:
        """Get statistics for each category."""
        stats = {}
        for category, fighters in self.organized_data.get("fighters_by_category", {}).items():
            stats[category] = {
                "count": len(fighters),
                "fighters": [f["name"] for f in fighters[:5]]  # First 5 fighters
            }
        return stats
    
    def is_ufc_league(self, league_name: str) -> bool:
        """Check if a league is UFC."""
        return league_name.upper() in ["UFC", "MMA"]
    
    def get_dropdown_structure(self) -> Dict:
        """Get the complete dropdown structure for frontend."""
        return {
            "gender_options": self.get_gender_options(),
            "category_options": self.dropdown_data.get("category_options", {}),
            "fighter_options": self.dropdown_data.get("fighter_options", {}),
            "total_fighters": len(self.organized_data.get("fighter_lookup", {}))
        }

# Global instance
ufc_fighter_service = UFCFighterService() 