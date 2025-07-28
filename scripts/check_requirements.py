#!/usr/bin/env python3
"""
Simple script to check if requirements.txt is up to date.
"""

import os
import re

def check_imports_in_file(file_path, imports_found):
    """Check for imports in a specific file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for common imports
        import_patterns = [
            (r'import discord', 'discord.py'),
            (r'from discord', 'discord.py'),
            (r'import aiohttp', 'aiohttp'),
            (r'from aiohttp', 'aiohttp'),
            (r'import aiomysql', 'aiomysql'),
            (r'from aiomysql', 'aiomysql'),
            (r'import redis', 'redis'),
            (r'from redis', 'redis'),
            (r'import numpy', 'numpy'),
            (r'from numpy', 'numpy'),
            (r'import pandas', 'pandas'),
            (r'from pandas', 'pandas'),
            (r'import matplotlib', 'matplotlib'),
            (r'from matplotlib', 'matplotlib'),
            (r'import psutil', 'psutil'),
            (r'from psutil', 'psutil'),
            (r'import pydantic', 'pydantic'),
            (r'from pydantic', 'pydantic'),
            (r'import pydantic_settings', 'pydantic-settings'),
            (r'from pydantic_settings', 'pydantic-settings'),
            (r'import sklearn', 'scikit-learn'),
            (r'from sklearn', 'scikit-learn'),
            (r'import joblib', 'joblib'),
            (r'from joblib', 'joblib'),
            (r'import flask', 'flask'),
            (r'from flask', 'flask'),
            (r'import werkzeug', 'werkzeug'),
            (r'from werkzeug', 'werkzeug'),
            (r'import pytest', 'pytest'),
            (r'from pytest', 'pytest'),
            (r'import pytest_asyncio', 'pytest-asyncio'),
            (r'from pytest_asyncio', 'pytest-asyncio'),
            (r'import opentelemetry', 'opentelemetry-api'),
            (r'from opentelemetry', 'opentelemetry-api'),
            (r'import yaml', 'pyyaml'),
            (r'from yaml', 'pyyaml'),
            (r'import dotenv', 'python-dotenv'),
            (r'from dotenv', 'python-dotenv'),
            (r'import PIL', 'Pillow'),
            (r'from PIL', 'Pillow'),
            (r'import rapidfuzz', 'rapidfuzz'),
            (r'from rapidfuzz', 'rapidfuzz'),
            (r'import aiofiles', 'aiofiles'),
            (r'from aiofiles', 'aiofiles'),
            (r'import requests', 'requests'),
            (r'from requests', 'requests'),
            (r'import beautifulsoup4', 'beautifulsoup4'),
            (r'from beautifulsoup4', 'beautifulsoup4'),
            (r'import lxml', 'lxml'),
            (r'from lxml', 'lxml'),
            (r'import openpyxl', 'openpyxl'),
            (r'from openpyxl', 'openpyxl'),
            (r'import xlsxwriter', 'xlsxwriter'),
            (r'from xlsxwriter', 'xlsxwriter'),
            (r'import seaborn', 'seaborn'),
            (r'from seaborn', 'seaborn'),
            (r'import scipy', 'scipy'),
            (r'from scipy', 'scipy'),
            (r'import aioredis', 'aioredis'),
            (r'from aioredis', 'aioredis'),
            (r'import sqlalchemy', 'sqlalchemy'),
            (r'from sqlalchemy', 'sqlalchemy'),
            (r'import click', 'click'),
            (r'from click', 'click'),
            (r'import tqdm', 'tqdm'),
            (r'from tqdm', 'tqdm'),
            (r'import marshmallow', 'marshmallow'),
            (r'from marshmallow', 'marshmallow'),
            (r'import msgpack', 'msgpack'),
            (r'from msgpack', 'msgpack'),
            (r'import orjson', 'orjson'),
            (r'from orjson', 'orjson'),
            (r'import jinja2', 'jinja2'),
            (r'from jinja2', 'jinja2'),
            (r'import markupsafe', 'markupsafe'),
            (r'from markupsafe', 'markupsafe'),
            (r'import websockets', 'websockets'),
            (r'from websockets', 'websockets'),
            (r'import cryptography', 'cryptography'),
            (r'from cryptography', 'cryptography'),
            (r'import bcrypt', 'bcrypt'),
            (r'from bcrypt', 'bcrypt'),
            (r'import lz4', 'lz4'),
            (r'from lz4', 'lz4'),
            (r'import plotly', 'plotly'),
            (r'from plotly', 'plotly'),
            (r'import statsmodels', 'statsmodels'),
            (r'from statsmodels', 'statsmodels'),
            (r'import eli5', 'eli5'),
            (r'from eli5', 'eli5'),
            (r'import fastapi', 'fastapi'),
            (r'from fastapi', 'fastapi'),
            (r'import uvicorn', 'uvicorn'),
            (r'from uvicorn', 'uvicorn'),
            (r'import healthcheck', 'healthcheck'),
            (r'from healthcheck', 'healthcheck'),
            (r'import setuptools', 'setuptools'),
            (r'from setuptools', 'setuptools'),
            (r'import pyotp', 'pyotp'),
            (r'from pyotp', 'pyotp'),
        ]

        for pattern, package in import_patterns:
            if re.search(pattern, content):
                imports_found.add(package)

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

def main():
    """Check if requirements.txt is up to date."""
    print("Checking requirements.txt against actual imports...")

    # Get all Python files
    python_files = []
    for root, dirs, files in os.walk('.'):
        if any(skip in root for skip in ['.git', '__pycache__', '.venv', 'node_modules']):
            continue
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    # Check imports in all files
    imports_found = set()
    for file_path in python_files:
        check_imports_in_file(file_path, imports_found)

    print(f"Found {len(imports_found)} external dependencies being used:")
    for imp in sorted(imports_found):
        print(f"  - {imp}")

    # Read requirements.txt
    requirements = set()
    try:
        with open('requirements.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '>=' in line:
                    package = line.split('>=')[0].strip()
                    requirements.add(package)
    except FileNotFoundError:
        print("requirements.txt not found")
        return

    print(f"\nRequirements.txt contains {len(requirements)} packages:")
    for req in sorted(requirements):
        print(f"  - {req}")

    # Compare
    missing = imports_found - requirements
    unused = requirements - imports_found

    print(f"\n=== ANALYSIS ===")
    if missing:
        print(f"\n❌ MISSING FROM REQUIREMENTS.TXT ({len(missing)}):")
        for pkg in sorted(missing):
            print(f"  - {pkg}")
    else:
        print("\n✅ All used dependencies are in requirements.txt")

    if unused:
        print(f"\n⚠️  UNUSED IN REQUIREMENTS.TXT ({len(unused)}):")
        for pkg in sorted(unused):
            print(f"  - {pkg}")
    else:
        print("\n✅ No unused dependencies in requirements.txt")

    print(f"\n📊 SUMMARY:")
    print(f"  - Dependencies being used: {len(imports_found)}")
    print(f"  - Dependencies in requirements.txt: {len(requirements)}")
    print(f"  - Missing: {len(missing)}")
    print(f"  - Unused: {len(unused)}")

if __name__ == "__main__":
    main()
