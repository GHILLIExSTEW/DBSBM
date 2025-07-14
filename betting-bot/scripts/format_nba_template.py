import json
import re

def format_nba_template():
    """Format the NBA teams template file into valid JSON"""
    
    # Read the malformed template file
    with open('betting-bot/data/basketball_nba_teams_template.json', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add quotes around all property names
    content = re.sub(r'(\s+)(\w+):', r'\1"\2":', content)
    
    # Add commas between objects in the response array
    content = re.sub(r'}\s*\n\s*{', '},\n    {', content)
    
    # Add commas between top-level properties
    content = re.sub(r'"\]\s*\n\s*"', '"],\n  "', content)
    
    # Remove trailing commas before closing brackets
    content = re.sub(r',\s*([}\]])', r'\1', content)
    
    # Fix the top-level structure
    content = re.sub(r'^\{\s*\n\s*\{', '{\n  {', content)
    
    # Parse and validate the JSON
    try:
        data = json.loads(content)
        
        # Write the properly formatted JSON to the main file
        with open('betting-bot/data/basketball_nba_teams.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully formatted NBA teams JSON with {len(data.get('response', []))} teams!")
        print("File saved as: betting-bot/data/basketball_nba_teams.json")
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print("Manual formatting required")

if __name__ == "__main__":
    format_nba_template() 