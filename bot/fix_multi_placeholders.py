#!/usr/bin/env python3
"""
Script to fix any remaining placeholder conversion issues and handle multi-placeholder lines correctly
"""
import os
import re
import sys
import shutil
from pathlib import Path

def fix_placeholders_on_line(line):
    """Fix multiple placeholders on a single line properly"""
    if '%s' not in line:
        return line
    
    # Skip non-SQL lines
    if not any(keyword in line.upper() for keyword in [
        'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WHERE', 'VALUES', 'SET', 'FROM'
    ]):
        return line
    
    # Skip legitimate %s uses 
    if 'strftime(' in line or 'format(' in line or '.format(' in line or '"%s"' in line:
        return line
    
    # Handle multi-placeholder lines correctly
    # Split by %s and rebuild with proper numbering
    parts = line.split('%s')
    if len(parts) <= 1:
        return line
    
    result = parts[0]
    for i in range(1, len(parts)):
        result += f'${i}' + parts[i]
    
    return result

def process_file(file_path):
    """Process a single Python file to fix any remaining issues"""
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        lines = original_content.split('\n')
        converted_lines = []
        changed = False
        
        for line in lines:
            new_line = fix_placeholders_on_line(line)
            if new_line != line:
                print(f"Fixed line in {file_path}:")
                print(f"  Before: {line.strip()}")
                print(f"  After:  {new_line.strip()}")
                changed = True
            converted_lines.append(new_line)
        
        if changed:
            # Write converted content
            converted_content = '\n'.join(converted_lines)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(converted_content)
            
            print(f"✅ Fixed multi-placeholder issues in: {file_path}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix remaining placeholder issues"""
    base_dir = Path(__file__).parent
    
    # Check all previously modified files
    files_processed = 0
    files_fixed = 0
    
    print("🔄 Fixing any remaining placeholder conversion issues...")
    print("=" * 60)
    
    # Process all Python files that might have issues
    for py_file in base_dir.rglob('*.py'):
        if py_file.name == 'fix_multi_placeholders.py':
            continue
            
        files_processed += 1
        if process_file(py_file):
            files_fixed += 1
    
    print("=" * 60)
    print(f"📊 Multi-placeholder fix complete!")
    print(f"   Files processed: {files_processed}")
    print(f"   Files modified: {files_fixed}")
    print(f"   Files unchanged: {files_processed - files_fixed}")

if __name__ == "__main__":
    main()
