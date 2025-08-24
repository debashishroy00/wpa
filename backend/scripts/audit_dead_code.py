#!/usr/bin/env python
"""Audit and mark dead code for deletion"""

import os
import re
from pathlib import Path

# Patterns that indicate dead code
DEAD_CODE_PATTERNS = [
    # ML-related imports and code
    r'import torch',
    r'import tensorflow',
    r'import numpy',
    r'import pandas',
    r'from sentence_transformers',
    r'from transformers',
    r'import chromadb',
    r'from chromadb',
    r'import faiss',
    r'import hnswlib',
    r'from sklearn',
    r'import tiktoken',
    
    # Old vector DB methods
    r'ChromaDB',
    r'chromadb_client',
    r'collection\.add',
    r'collection\.query',
    r'collection\.delete',
    
    # Embedding-related that use ML
    r'SentenceTransformer',
    r'local_model',
    r'hybrid_embedding',
    r'local_provider',
    r'LocalEmbedding',
]

# Files/folders that are completely dead
DEAD_FILES = [
    'app/services/embeddings/local_provider.py.disabled',
    'app/services/embeddings/hybrid_service.py.disabled',
    'app/services/embeddings/sentence_transformer_provider.py',
    'app/services/embeddings/chromadb_provider.py',
    'app/services/chromadb_service.py',
    'app/ml/',
    'app/services/vector_db_old.py',
    'comprehensive_recovery.py',
    'diagnose_vector_db.py',
    'test_shadow_mode.py',
    'start_shadow_mode.sh',
]

def scan_file(filepath):
    """Scan a file for dead code patterns"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Skip binary files
        return []
    
    dead_code_found = []
    for pattern in DEAD_CODE_PATTERNS:
        if re.search(pattern, content):
            dead_code_found.append(pattern)
    
    return dead_code_found

def audit_project(root_dir='app'):
    """Audit entire project for dead code"""
    print("🔍 Starting Dead Code Audit...")
    print("=" * 50)
    
    files_to_delete = []
    files_to_review = []
    
    # Check for completely dead files
    for dead_file in DEAD_FILES:
        if os.path.exists(dead_file):
            files_to_delete.append(dead_file)
            print(f"❌ DELETE: {dead_file}")
    
    # Scan all Python files
    for root, dirs, files in os.walk(root_dir):
        # Skip __pycache__
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                dead_patterns = scan_file(filepath)
                
                if dead_patterns:
                    files_to_review.append((filepath, dead_patterns))
                    print(f"⚠️  REVIEW: {filepath}")
                    for pattern in dead_patterns[:3]:  # Show first 3 patterns
                        print(f"    - Contains: {pattern}")
    
    print("\n" + "=" * 50)
    print(f"Files to DELETE: {len(files_to_delete)}")
    print(f"Files to REVIEW: {len(files_to_review)}")
    
    return files_to_delete, files_to_review

if __name__ == "__main__":
    files_to_delete, files_to_review = audit_project()
    
    print("\n📋 Action Plan:")
    print("1. Rename files to delete with _delete suffix")
    print("2. Review and clean files with dead code")
    print("3. Run tests to ensure nothing breaks")
    print("4. Then permanently delete _delete files")