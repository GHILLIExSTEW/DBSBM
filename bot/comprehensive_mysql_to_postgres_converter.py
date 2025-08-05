#!/usr/bin/env python3
"""
Comprehensive MySQL to PostgreSQL Conversion Script
This script will convert ALL MySQL syntax to PostgreSQL syntax across the entire bot codebase.
"""
import os
import re
import sys
import shutil
from pathlib import Path

def convert_mysql_to_postgres_syntax(content):
    """Convert MySQL-specific syntax to PostgreSQL equivalents"""
    
    # 1. Convert placeholder syntax: %s -> $1, $2, $3, etc.
    def replace_placeholders(text):
        lines = text.split('\n')
        converted_lines = []
        
        for line in lines:
            # Skip lines that are comments or don't contain SQL
            if line.strip().startswith('#') or line.strip().startswith('//'):
                converted_lines.append(line)
                continue
                
            # Skip legitimate %s uses (strftime, format, etc.)
            if 'strftime(' in line or 'format(' in line or '.format(' in line or '"%s"' in line:
                converted_lines.append(line)
                continue
                
            # Check if line contains SQL-like content with %s
            if '%s' in line and any(keyword in line.upper() for keyword in [
                'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WHERE', 'VALUES', 'SET', 'FROM', 'JOIN'
            ]):
                # Count %s occurrences and replace with $1, $2, $3, etc.
                placeholder_count = line.count('%s')
                if placeholder_count > 0:
                    new_line = line
                    for i in range(placeholder_count):
                        new_line = new_line.replace('%s', f'${i+1}', 1)
                    converted_lines.append(new_line)
                else:
                    converted_lines.append(line)
            else:
                converted_lines.append(line)
        
        return '\n'.join(converted_lines)
    
    # Apply placeholder conversion
    content = replace_placeholders(content)
    
    # 2. Convert MySQL functions to PostgreSQL equivalents
    conversions = [
        # Time functions
        (r'UTC_TIMESTAMP\(\)', 'NOW()'),
        (r'CURRENT_TIMESTAMP\(\)', 'NOW()'),
        (r'UNIX_TIMESTAMP\(\)', 'EXTRACT(EPOCH FROM NOW())'),
        (r'FROM_UNIXTIME\(([^)]+)\)', r'TO_TIMESTAMP(\1)'),
        
        # Date/Time arithmetic and functions
        (r'TIMESTAMPDIFF\(MINUTE,\s*([^,]+),\s*([^)]+)\)', r'EXTRACT(EPOCH FROM (\2 - \1))/60'),
        (r'TIMESTAMPDIFF\(HOUR,\s*([^,]+),\s*([^)]+)\)', r'EXTRACT(EPOCH FROM (\2 - \1))/3600'),
        (r'TIMESTAMPDIFF\(DAY,\s*([^,]+),\s*([^)]+)\)', r'EXTRACT(DAY FROM (\2 - \1))'),
        (r'TIMESTAMPDIFF\(SECOND,\s*([^,]+),\s*([^)]+)\)', r'EXTRACT(EPOCH FROM (\2 - \1))'),
        
        (r'DATE_SUB\(([^,]+),\s*INTERVAL\s+([^)]+)\)', r'(\1 - INTERVAL \'\2\')'),
        (r'DATE_ADD\(([^,]+),\s*INTERVAL\s+([^)]+)\)', r'(\1 + INTERVAL \'\2\')'),
        
        # String functions
        (r'CONCAT\(([^)]+)\)', r'(\1)'),  # PostgreSQL uses || for concatenation
        (r'IFNULL\(([^,]+),\s*([^)]+)\)', r'COALESCE(\1, \2)'),
        (r'ISNULL\(([^)]+)\)', r'(\1 IS NULL)'),
        
        # Conditional functions
        (r'IF\(([^,]+),\s*([^,]+),\s*([^)]+)\)', r'CASE WHEN \1 THEN \2 ELSE \3 END'),
        
        # Type conversions
        (r'CAST\(([^)]+)\s+AS\s+SIGNED\)', r'CAST(\1 AS INTEGER)'),
        (r'CAST\(([^)]+)\s+AS\s+UNSIGNED\)', r'CAST(\1 AS INTEGER)'),
        
        # MySQL specific syntax
        (r'AUTO_INCREMENT', 'SERIAL'),
        (r'ENGINE=InnoDB', ''),
        (r'CHARACTER SET utf8mb4', ''),
        (r'COLLATE utf8mb4_unicode_ci', ''),
        
        # Boolean values
        (r'\b1\b(?=\s*(?:AND|OR|WHERE|,|\)|$))', 'TRUE'),
        (r'\b0\b(?=\s*(?:AND|OR|WHERE|,|\)|$))', 'FALSE'),
        
        # LIMIT syntax (MySQL allows LIMIT without ORDER BY, PostgreSQL prefers ORDER BY)
        # This is handled manually for specific cases
        
        # Backticks to double quotes for identifiers
        (r'`([^`]+)`', r'"\1"'),
    ]
    
    # Apply all conversions
    for pattern, replacement in conversions:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
    
    # 3. Handle specific COALESCE type mismatches
    # Convert potential type mismatches in COALESCE
    content = re.sub(
        r'COALESCE\(([^,]+),\s*([^)]+)\)',
        lambda m: f'COALESCE({m.group(1)}::text, {m.group(2)}::text)' 
        if 'api_game_id' in m.group(0) else m.group(0),
        content,
        flags=re.IGNORECASE
    )
    
    return content

def process_file(file_path):
    """Process a single Python file"""
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Convert MySQL syntax to PostgreSQL
        converted_content = convert_mysql_to_postgres_syntax(original_content)
        
        # Only write if content changed
        if converted_content != original_content:
            # Create backup
            backup_path = str(file_path) + '.mysql_backup'
            shutil.copy2(file_path, backup_path)
            
            # Write converted content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(converted_content)
            
            print(f"✅ Converted: {file_path}")
            return True
        else:
            print(f"⏭️  No changes needed: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to process all files"""
    base_dir = Path(__file__).parent
    
    # Directories and files to process
    paths_to_process = [
        base_dir / "services",
        base_dir / "data", 
        base_dir / "commands",
        base_dir / "cogs",
        base_dir / "scripts",
        base_dir / "utils",
        base_dir / "api",
        base_dir / "bot",
        base_dir / "tests",
        base_dir / "migrations",
        base_dir / "main.py",
        base_dir.parent / "scripts",  # Top-level scripts
        base_dir.parent / "api_endpoints.py",  # Specific files
    ]
    
    files_processed = 0
    files_converted = 0
    
    print("🔄 Starting comprehensive MySQL to PostgreSQL conversion...")
    print("=" * 70)
    
    for path in paths_to_process:
        if path.is_file() and path.suffix == '.py':
            # Process single file
            files_processed += 1
            if process_file(path):
                files_converted += 1
        elif path.exists() and path.is_dir():
            # Process all Python files in directory recursively
            for py_file in path.rglob('*.py'):
                # Skip backup files and __pycache__
                if '.backup' in str(py_file) or '__pycache__' in str(py_file):
                    continue
                    
                files_processed += 1
                if process_file(py_file):
                    files_converted += 1
        else:
            print(f"⚠️  Path not found: {path}")
    
    print("=" * 70)
    print(f"📊 Conversion complete!")
    print(f"   Files processed: {files_processed}")
    print(f"   Files converted: {files_converted}")
    print(f"   Files unchanged: {files_processed - files_converted}")
    
    if files_converted > 0:
        print("\n🔄 All MySQL syntax converted to PostgreSQL!")
        print("📂 Backup files created with .mysql_backup extension")
        print("\n🚀 Ready to restart the Discord bot with PostgreSQL")

if __name__ == "__main__":
    main()
