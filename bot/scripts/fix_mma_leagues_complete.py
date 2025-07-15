import json
import re


def fix_mma_leagues_json():
    """Fix the malformed MMA leagues JSON file"""

    # Read the file
    with open("bot/data/mma_leagues.json", "r", encoding="utf-8") as f:
        content = f.read()

    # Fix the JSON structure
    # Replace unquoted property names with quoted ones
    content = re.sub(r"(\s+)(\w+):\s*", r'\1"\2": ', content)

    # Add missing commas between objects
    content = re.sub(r"(\s+)\}(\s*)\n(\s*)\{", r"\1},\n\3{", content)

    # Remove trailing comma before closing bracket
    content = re.sub(r",(\s*)\]", r"\1]", content)

    # Parse to validate JSON
    try:
        data = json.loads(content)
        print(f"Successfully parsed JSON with {len(data)} items")

        # Write back the fixed JSON
        with open("bot/data/mma_leagues.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print("Fixed mma_leagues.json successfully!")
        return True

    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print("Attempting manual fix...")

        # Manual fix approach
        lines = content.split("\n")
        fixed_lines = []

        for i, line in enumerate(lines):
            # Fix property names
            if re.match(r"\s+\w+:\s*", line):
                line = re.sub(r"(\s+)(\w+):\s*", r'\1"\2": ', line)

            # Add commas between objects
            if line.strip() == "}" and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line.startswith("{"):
                    line = line + ","

            fixed_lines.append(line)

        # Join and try to parse again
        fixed_content = "\n".join(fixed_lines)

        try:
            data = json.loads(fixed_content)
            with open("bot/data/mma_leagues.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print("Fixed mma_leagues.json with manual approach!")
            return True
        except json.JSONDecodeError as e2:
            print(f"Manual fix also failed: {e2}")
            return False


if __name__ == "__main__":
    fix_mma_leagues_json()
