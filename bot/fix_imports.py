#!/usr/bin/env python3
"""
Fix import paths in the bot directory to use relative imports.
"""
import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix imports in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace "from bot." with relative imports
        # Pattern: from module import something
        pattern = r'from bot\.([^\s]+) import'
        replacement = r'from \1 import'
        
        new_content = re.sub(pattern, replacement, content)
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Fixed imports in: {file_path}")
            return True
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    
    return False

def fix_all_imports():
    """Fix imports in all Python files in the bot directory."""
    bot_dir = Path('.')
    fixed_count = 0
    
    for py_file in bot_dir.rglob('*.py'):
        if fix_imports_in_file(py_file):
            fixed_count += 1
    
    print(f"Fixed imports in {fixed_count} files")

if __name__ == "__main__":
    fix_all_imports()
