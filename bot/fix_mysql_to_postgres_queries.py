#!/usr/bin/env python3
"""
Script to convert MySQL-style %s placeholders to PostgreSQL-style $1, $2, $3 placeholders
This fixes the "syntax error at or near '%'" PostgreSQL errors
"""
import os
import re
import sys
import shutil
from pathlib import Path

def convert_mysql_to_postgres_placeholders(content):
    """Convert MySQL %s placeholders to PostgreSQL $1, $2, $3 format"""
    lines = content.split('\n')
    converted_lines = []
    
    for line in lines:
        # Skip lines that are comments or don't contain SQL
        if line.strip().startswith('#') or line.strip().startswith('//'):
            converted_lines.append(line)
            continue
            
        # Skip strftime and other legitimate %s uses
        if 'strftime(' in line or 'format(' in line or '.format(' in line or '"%s"' in line:
            converted_lines.append(line)
            continue
            
        # Check if line contains SQL-like content with %s
        if '%s' in line and any(keyword in line.upper() for keyword in [
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WHERE', 'VALUES', 'SET', 'FROM'
        ]):
            # Count %s occurrences in this line
            placeholder_count = line.count('%s')
            if placeholder_count > 0:
                # Replace %s with $1, $2, $3, etc.
                new_line = line
                for i in range(placeholder_count):
                    new_line = new_line.replace('%s', f'${i+1}', 1)
                converted_lines.append(new_line)
                print(f"Converted: {line.strip()}")
                print(f"      To: {new_line.strip()}")
            else:
                converted_lines.append(line)
        else:
            converted_lines.append(line)
    
    return '\n'.join(converted_lines)

def fix_mysql_functions_to_postgres(content):
    """Fix MySQL-specific functions to PostgreSQL equivalents"""
    # UTC_TIMESTAMP() -> NOW()
    content = re.sub(r'UTC_TIMESTAMP\(\)', 'NOW()', content)
    
    # UPPER() is same in both, but just in case
    # Add more MySQL->PostgreSQL conversions as needed
    
    return content

def process_file(file_path):
    """Process a single Python file"""
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Convert MySQL placeholders to PostgreSQL
        converted_content = convert_mysql_to_postgres_placeholders(original_content)
        
        # Fix MySQL functions
        converted_content = fix_mysql_functions_to_postgres(converted_content)
        
        # Only write if content changed
        if converted_content != original_content:
            # Create backup
            backup_path = str(file_path) + '.backup'
            shutil.copy2(file_path, backup_path)
            
            # Write converted content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(converted_content)
            
            print(f"✅ Fixed: {file_path}")
            return True
        else:
            print(f"⏭️  No changes needed: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to process all Python files"""
    base_dir = Path(__file__).parent
    
    # Directories to process
    directories_to_process = [
        base_dir / "services",
        base_dir / "data", 
        base_dir / "commands",
        base_dir / "cogs",
        base_dir / "scripts",
        base_dir.parent / "scripts",  # Top-level scripts
        base_dir.parent / "api_endpoints.py",  # Specific files
    ]
    
    files_processed = 0
    files_fixed = 0
    
    print("🔄 Starting MySQL to PostgreSQL query conversion...")
    print("=" * 60)
    
    for directory in directories_to_process:
        if directory.is_file():
            # Process single file
            if directory.suffix == '.py':
                files_processed += 1
                if process_file(directory):
                    files_fixed += 1
        elif directory.exists():
            # Process all Python files in directory
            for py_file in directory.rglob('*.py'):
                files_processed += 1
                if process_file(py_file):
                    files_fixed += 1
        else:
            print(f"⚠️  Directory not found: {directory}")
    
    print("=" * 60)
    print(f"📊 Conversion complete!")
    print(f"   Files processed: {files_processed}")
    print(f"   Files modified: {files_fixed}")
    print(f"   Files unchanged: {files_processed - files_fixed}")
    
    if files_fixed > 0:
        print("\n🔄 Restart the Discord bot to apply the changes:")
        print("   The service manager will automatically restart it")
        print("\n📂 Backup files created with .backup extension")

if __name__ == "__main__":
    main()
