#!/usr/bin/env python
"""Index all documents in the docs folder to ChromaDB"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.chromadb_service import ChromaDBService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DOCS_DIR = "./storage/docs"
ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.docx', '.doc', '.md'}

def extract_text_from_file(file_path, filename):
    """Extract text from various file formats"""
    ext = os.path.splitext(filename)[1].lower()

    try:
        if ext == '.pdf':
            try:
                import pdfplumber
                content = ""
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            content += text + "\n"
                return content
            except ImportError:
                print(f"  [WARNING] pdfplumber not installed, skipping PDF: {filename}")
                return None
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    except Exception as e:
        print(f"  [ERROR] Error extracting text from {filename}: {e}")
        return None

def index_documents():
    """Index all documents from the docs folder"""

    if not os.path.exists(DOCS_DIR):
        print(f"[ERROR] Documents folder not found: {DOCS_DIR}")
        print(f"   Please create it and add documents there.")
        return False

    # Initialize ChromaDB
    try:
        chroma = ChromaDBService()
        print("[OK] ChromaDB initialized")
    except Exception as e:
        print(f"[ERROR] Failed to initialize ChromaDB: {e}")
        return False

    # Get all document files
    doc_files = []
    for file in os.listdir(DOCS_DIR):
        file_path = os.path.join(DOCS_DIR, file)
        if os.path.isfile(file_path):
            ext = os.path.splitext(file)[1].lower()
            if ext in ALLOWED_EXTENSIONS:
                doc_files.append((file_path, file))

    if not doc_files:
        print(f"[WARNING] No documents found in {DOCS_DIR}")
        return False

    print(f"\n Found {len(doc_files)} document(s) to index:\n")

    indexed_count = 0
    for file_path, filename in doc_files:
        try:
            print(f"  Indexing: {filename}...", end='')

            content = extract_text_from_file(file_path, filename)

            if content is None:
                continue

            if not content.strip():
                print(f"  [SKIP] {filename} - Empty file, skipped")
                continue

            # Index in ChromaDB
            chroma.add_document(
                doc_id=filename,
                text=content,
                metadata={"filename": filename, "source": filename}
            )

            print(f"  [OK] {filename} - Indexed ({len(content)} chars)")
            indexed_count += 1

        except Exception as e:
            print(f"  [FAIL] {filename} - Failed: {e}")

    print(f"\n{'='*50}")
    print(f"[SUCCESS] Indexed {indexed_count}/{len(doc_files)} documents")
    print(f"{'='*50}\n")

    if indexed_count > 0:
        print("[INFO] Documents are now ready! The chatbot will use them to answer questions.")
        return True
    else:
        print("[ERROR] No documents were indexed. Check file formats and try again.")
        return False

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  DOCUMENT INDEXING")
    print("="*50 + "\n")

    success = index_documents()

    sys.exit(0 if success else 1)
