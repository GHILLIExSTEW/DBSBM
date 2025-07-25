#!/usr/bin/env python3
"""
PDF Extraction Summary Script

This script provides a summary of the PDF extraction results.
"""

import os
from pathlib import Path


def main():
    """Show summary of PDF extraction results."""
    current_dir = Path(__file__).parent
    extracted_dir = current_dir / "extracted_pdfs"

    print("📄 PDF Extraction Results Summary")
    print("=" * 50)

    if not extracted_dir.exists():
        print("❌ No extracted PDFs directory found!")
        return

    # Count extracted files
    txt_files = list(extracted_dir.glob("*.txt"))
    summary_file = extracted_dir / "extraction_summary.md"

    print(f"📁 Output Directory: {extracted_dir}")
    print(f"📊 Total Extracted Files: {len(txt_files)}")
    print(f"📋 Summary File: {'✅ Found' if summary_file.exists() else '❌ Missing'}")
    print()

    print("📖 Extracted Files:")
    print("-" * 30)

    total_size = 0
    total_lines = 0

    for txt_file in sorted(txt_files):
        file_size = txt_file.stat().st_size
        total_size += file_size

        # Count lines
        try:
            with open(txt_file, "r", encoding="utf-8") as f:
                lines = len(f.readlines())
                total_lines += lines
        except:
            lines = "Unknown"

        print(f"✅ {txt_file.name}")
        print(f"   📏 Size: {file_size / 1024:.1f} KB")
        print(f"   📄 Lines: {lines}")
        print()

    print("📈 Summary Statistics:")
    print("-" * 30)
    print(f"📊 Total Files: {len(txt_files)}")
    print(f"📏 Total Size: {total_size / 1024 / 1024:.1f} MB")
    print(f"📄 Total Lines: {total_lines:,}")
    print(f"📊 Average Size: {total_size / len(txt_files) / 1024:.1f} KB per file")
    print()

    print("🎯 Next Steps:")
    print("-" * 30)
    print("1. 📖 Read the extracted .txt files to access API documentation")
    print("2. 🔍 Search for specific endpoints or parameters")
    print("3. 📝 Use the content for API integration in your bot")
    print("4. 🔄 Re-run the script if you add new PDFs to the directory")
    print()

    print("📁 File Locations:")
    print("-" * 30)
    print(f"📂 Extracted Files: {extracted_dir}")
    print(
        f"📂 Original PDFs: {current_dir.parent / 'bot' / 'data' / 'api_sports_docs'}"
    )
    print(f"📂 Script Location: {current_dir / 'pdf_extractor.py'}")


if __name__ == "__main__":
    main()
