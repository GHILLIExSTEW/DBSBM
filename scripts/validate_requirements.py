#!/usr/bin/env python3
"""
Script to validate requirements.txt against actual imports in the codebase.
"""

import os
import re
import ast
from pathlib import Path
from typing import Set, Dict, List


def extract_imports_from_file(file_path: str) -> Set[str]:
    """Extract all import statements from a Python file."""
    imports = set()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse the AST to find imports
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)

    except Exception as e:
        print(f"Error parsing {file_path}: {e}")

    return imports


def get_all_imports() -> Set[str]:
    """Get all imports from Python files in the project."""
    all_imports = set()

    # Walk through all Python files
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip in root for skip in ['.git', '__pycache__', '.venv', 'node_modules']):
            continue

        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                imports = extract_imports_from_file(file_path)
                all_imports.update(imports)

    return all_imports


def parse_requirements() -> Dict[str, str]:
    """Parse requirements.txt and return package names."""
    requirements = {}

    try:
        with open('requirements.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '>=' in line:
                    # Extract package name from "package>=version"
                    package = line.split('>=')[0].strip()
                    version = line.split('>=')[1].strip()
                    requirements[package] = version
    except FileNotFoundError:
        print("requirements.txt not found")
        return {}

    return requirements


def is_external_dependency(import_name: str) -> bool:
    """Check if an import is an external dependency that should be in requirements.txt."""
    # Standard library modules to exclude
    stdlib_modules = {
        'os', 'sys', 'time', 'datetime', 'json', 'logging', 'asyncio', 'typing',
        'unittest', 'pathlib', 're', 'ast', 'io', 'traceback', 'uuid', 'secrets',
        'hashlib', 'hmac', 'base64', 'gc', 'csv', 'pickle', 'tempfile', 'random',
        'math', 'functools', 'collections', 'contextlib', 'subprocess', 'signal',
        'weakref', 'enum', 'dataclasses', 'argparse', 'difflib', 'string',
        'importlib', 'threading', 'tracemalloc', 'zoneinfo', 'ipaddress',
        'urllib.parse', 'unittest.mock', 'logging.handlers'  # These are stdlib submodules
    }

    # Internal project modules to exclude
    internal_prefixes = {
        'bot.', 'config.', 'scripts.', 'tests.', 'utils.', 'services.',
        'commands.', 'data.', 'api.', 'views.', 'constants.', 'webapp',
        'modals', 'parlay_betting', 'commands', 'utils', 'services', 'data',
        'api', 'views', 'constants', 'workflow', 'leagues', 'team_mappings',
        'basketball_teams', 'baseball_teams', 'football_teams', 'hockey_teams',
        'soccer_teams', 'ncaa_teams', 'other_sports_teams', 'thesportsdb',
        'ui_components', 'exceptions', 'graphql', 'graphene', 'graphene_sqlalchemy'
    }

    # Check if it's a standard library module
    if import_name in stdlib_modules:
        return False

    # Check if it's an internal project module
    for prefix in internal_prefixes:
        if import_name.startswith(prefix):
            return False

    # Check for common internal patterns
    if any(pattern in import_name for pattern in ['bot.', 'config.', 'scripts.', 'tests.']):
        return False

    return True


def get_package_name_from_import(import_name: str) -> str:
    """Convert import name to package name for requirements.txt."""
    # Common mapping of import names to package names
    import_to_package = {
        'discord': 'discord.py',
        'dotenv': 'python-dotenv',
        'PIL': 'Pillow',
        'sklearn': 'scikit-learn',
        'yaml': 'pyyaml',
        'pydantic_settings': 'pydantic-settings',
        'pytest_asyncio': 'pytest-asyncio',
        'opentelemetry': 'opentelemetry-api',  # This is a simplification
        'redis': 'redis',
        'aiohttp': 'aiohttp',
        'aiomysql': 'aiomysql',
        'numpy': 'numpy',
        'pandas': 'pandas',
        'requests': 'requests',
        'flask': 'flask',
        'pytest': 'pytest',
        'psutil': 'psutil',
        'matplotlib': 'matplotlib',
        'seaborn': 'seaborn',
        'scipy': 'scipy',
        'rapidfuzz': 'rapidfuzz',
        'pydantic': 'pydantic',
        'aiofiles': 'aiofiles',
        'werkzeug': 'werkzeug',
        'apscheduler': 'apscheduler',
        'prometheus_client': 'prometheus-client',
        'python_json_logger': 'python-json-logger',
        'python_dateutil': 'python-dateutil',
        'pytz': 'pytz',
        'click': 'click',
        'tqdm': 'tqdm',
        'python_multipart': 'python-multipart',
        'marshmallow': 'marshmallow',
        'msgpack': 'msgpack',
        'orjson': 'orjson',
        'jinja2': 'jinja2',
        'markupsafe': 'markupsafe',
        'websockets': 'websockets',
        'cryptography': 'cryptography',
        'bcrypt': 'bcrypt',
        'lz4': 'lz4',
        'joblib': 'joblib',
        'plotly': 'plotly',
        'statsmodels': 'statsmodels',
        'eli5': 'eli5',
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'healthcheck': 'healthcheck',
        'setuptools': 'setuptools',
        'pyotp': 'pyotp',
        'urllib': 'urllib3',  # urllib.parse is part of urllib3
        'unittest': 'unittest2',  # unittest.mock is part of unittest2
        'logging': 'logging',  # This is actually stdlib, should be filtered out
    }

    # Get the base package name (first part before any dots)
    base_name = import_name.split('.')[0]

    # Check if we have a specific mapping
    if base_name in import_to_package:
        return import_to_package[base_name]

    # Return the base name as the package name
    return base_name


def main():
    """Main validation function."""
    print("Validating requirements.txt against actual imports...")

    # Get all imports from the codebase
    all_imports = get_all_imports()
    print(f"Found {len(all_imports)} unique imports in the codebase")

    # Filter to only external dependencies
    external_imports = {
        imp for imp in all_imports if is_external_dependency(imp)}
    print(f"Found {len(external_imports)} external dependencies")

    # Parse requirements.txt
    requirements = parse_requirements()
    print(f"Found {len(requirements)} packages in requirements.txt")

    # Check for unused requirements
    unused_requirements = []
    for package in requirements:
        if package not in external_imports:
            # Check for common variations
            variations = [
                package,
                package.replace('-', '_'),
                package.replace('_', '-'),
                package.split('-')[0],  # For packages like "pydantic-settings"
            ]

            if not any(var in external_imports for var in variations):
                unused_requirements.append(package)

    # Check for missing requirements
    missing_requirements = []
    for import_name in external_imports:
        package_name = get_package_name_from_import(import_name)
        if package_name not in requirements:
            missing_requirements.append((import_name, package_name))

    print("\n=== VALIDATION RESULTS ===")

    if unused_requirements:
        print(f"\n❌ UNUSED REQUIREMENTS ({len(unused_requirements)}):")
        for package in unused_requirements:
            print(f"  - {package}")
    else:
        print("\n✅ No unused requirements found")

    if missing_requirements:
        print(f"\n❌ MISSING REQUIREMENTS ({len(missing_requirements)}):")
        for import_name, package_name in missing_requirements:
            print(f"  - {import_name} -> {package_name}")
    else:
        print("\n✅ No missing requirements found")

    print(f"\n📊 SUMMARY:")
    print(f"  - Total imports found: {len(all_imports)}")
    print(f"  - External dependencies: {len(external_imports)}")
    print(f"  - Total requirements: {len(requirements)}")
    print(f"  - Unused requirements: {len(unused_requirements)}")
    print(f"  - Missing requirements: {len(missing_requirements)}")


if __name__ == "__main__":
    main()
