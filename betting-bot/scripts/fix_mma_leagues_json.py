import json
import re

# Read the malformed JSON file
with open("betting-bot/data/mma_leagues.json", "r", encoding="utf-8") as f:
    content = f.read()

# Fix the JSON structure
# Replace unquoted property names and add missing commas
fixed_content = re.sub(r"(\s+)(\w+):\s*", r'\1"\2": ', content)
fixed_content = re.sub(
    r'(\s+)"(\w+)":\s*([^,\n]+)\n\s*}\s*\n\s*{',
    r'\1"\2": \3,\n\1},\n\1{',
    fixed_content,
)

# Parse and re-serialize to ensure valid JSON
try:
    data = json.loads(fixed_content)
    with open("betting-bot/data/mma_leagues.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print("Fixed mma_leagues.json successfully!")
except json.JSONDecodeError as e:
    print(f"Error: {e}")
    print("Manual fix required")
