#!/usr/bin/env python3
"""
PDF Extractor Script

This script reads all PDF files in the bot/data/api_sports_docs directory
and extracts their text content into readable text files.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional

# Try to import PDF libraries
try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

# Add the bot directory to the path so we can import modules
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extracts text content from PDF files."""
    
    def __init__(self):
        self.pdf_dir = project_root / "bot" / "data" / "api_sports_docs"
        self.output_dir = current_dir / "extracted_pdfs"
        self.output_dir.mkdir(exist_ok=True)
        
    def get_pdf_files(self) -> List[Path]:
        """Get all PDF files in the api_sports_docs directory."""
        pdf_files = []
        if self.pdf_dir.exists():
            for file in self.pdf_dir.glob("*.pdf"):
                pdf_files.append(file)
        return sorted(pdf_files)
    
    def extract_text_from_pdf(self, pdf_path: Path) -> Optional[str]:
        """Extract text content from a PDF file."""
        try:
            # Try PyPDF2 first
            if HAS_PYPDF2:
                return self._extract_with_pypdf2(pdf_path)
            
            # Try pdfplumber as fallback
            if HAS_PDFPLUMBER:
                return self._extract_with_pdfplumber(pdf_path)
            
            logger.error("Neither PyPDF2 nor pdfplumber are available!")
            return None
                
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path.name}: {e}")
            return None
    
    def _extract_with_pypdf2(self, pdf_path: Path) -> str:
        """Extract text using PyPDF2."""
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Page {page_num + 1} ---\n"
                        text += page_text
                        text += "\n"
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num + 1}: {e}")
        return text
    
    def _extract_with_pdfplumber(self, pdf_path: Path) -> str:
        """Extract text using pdfplumber."""
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Page {page_num + 1} ---\n"
                        text += page_text
                        text += "\n"
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num + 1}: {e}")
        return text
    
    def save_extracted_text(self, pdf_path: Path, text: str) -> Path:
        """Save extracted text to a file."""
        # Create a clean filename
        filename = pdf_path.stem.replace(" ", "_").replace("-", "_")
        output_file = self.output_dir / f"{filename}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Extracted from: {pdf_path.name}\n")
            f.write(f"# Original file: {pdf_path}\n")
            f.write(f"# Extracted on: {Path(__file__).stat().st_mtime}\n")
            f.write("=" * 80 + "\n\n")
            f.write(text)
        
        return output_file
    
    def create_summary_file(self, extraction_results: Dict[Path, Dict]) -> Path:
        """Create a summary file with extraction results."""
        summary_file = self.output_dir / "extraction_summary.md"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("# PDF Extraction Summary\n\n")
            f.write(f"Extracted on: {Path(__file__).stat().st_mtime}\n\n")
            f.write("## Files Processed\n\n")
            
            for pdf_path, result in extraction_results.items():
                status = "✅ Success" if result['success'] else "❌ Failed"
                f.write(f"### {pdf_path.name}\n")
                f.write(f"- **Status**: {status}\n")
                f.write(f"- **Original Size**: {pdf_path.stat().st_size / 1024 / 1024:.1f} MB\n")
                
                if result['success']:
                    f.write(f"- **Output File**: {result['output_file'].name}\n")
                    f.write(f"- **Text Length**: {len(result['text'])} characters\n")
                    f.write(f"- **Lines**: {result['text'].count(chr(10)) + 1}\n")
                else:
                    f.write(f"- **Error**: {result['error']}\n")
                f.write("\n")
        
        return summary_file
    
    def process_all_pdfs(self) -> Dict[Path, Dict]:
        """Process all PDF files and extract their text."""
        pdf_files = self.get_pdf_files()
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        results = {}
        
        for pdf_path in pdf_files:
            logger.info(f"Processing: {pdf_path.name}")
            
            try:
                text = self.extract_text_from_pdf(pdf_path)
                
                if text and text.strip():
                    output_file = self.save_extracted_text(pdf_path, text)
                    results[pdf_path] = {
                        'success': True,
                        'text': text,
                        'output_file': output_file,
                        'error': None
                    }
                    logger.info(f"✅ Successfully extracted {len(text)} characters to {output_file.name}")
                else:
                    results[pdf_path] = {
                        'success': False,
                        'text': None,
                        'output_file': None,
                        'error': 'No text content extracted'
                    }
                    logger.warning(f"❌ No text content extracted from {pdf_path.name}")
                    
            except Exception as e:
                results[pdf_path] = {
                    'success': False,
                    'text': None,
                    'output_file': None,
                    'error': str(e)
                }
                logger.error(f"❌ Failed to process {pdf_path.name}: {e}")
        
        return results
    
    def run(self):
        """Run the PDF extraction process."""
        logger.info("Starting PDF extraction process...")
        logger.info(f"PDF directory: {self.pdf_dir}")
        logger.info(f"Output directory: {self.output_dir}")
        
        # Check if PDF directory exists
        if not self.pdf_dir.exists():
            logger.error(f"PDF directory does not exist: {self.pdf_dir}")
            return
        
        # Process all PDFs
        results = self.process_all_pdfs()
        
        # Create summary
        summary_file = self.create_summary_file(results)
        
        # Print summary
        successful = sum(1 for r in results.values() if r['success'])
        total = len(results)
        
        logger.info(f"\nExtraction completed!")
        logger.info(f"Successfully processed: {successful}/{total} files")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Summary file: {summary_file.name}")
        
        if successful < total:
            logger.warning(f"Failed to process {total - successful} files. Check the summary for details.")


def main():
    """Main function to run the PDF extraction."""
    extractor = PDFExtractor()
    extractor.run()


if __name__ == "__main__":
    main() 