#!/usr/bin/env python3
"""Debug vector store contents and structure"""

import json
import os
import sys
sys.path.append('/app')

def check_vector_store():
    """Check vector store in different possible locations"""
    possible_paths = [
        "/tmp/vector_store.json",
        "C:/temp/vector_store.json", 
        "C:/projects/wpa/vector_store.json",
        "C:/projects/wpa/backend/vector_store.json",
        "./vector_store.json",
        "../vector_store.json"
    ]
    
    print("Checking vector store locations:")
    for path in possible_paths:
        if os.path.exists(path):
            print(f"FOUND: {path}")
            analyze_vector_store(path)
            return
        else:
            print(f"NOT FOUND: {path}")
    
    print("Vector store not found in any expected location")

def analyze_vector_store(path):
    """Analyze the vector store file"""
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        
        print(f"\nAnalyzing vector store at {path}")
        print("="*50)
        
        documents = data.get('documents', {})
        print(f"Total documents: {len(documents)}")
        
        if not documents:
            print("Vector store is empty")
            return
        
        # Analyze each document
        for i, (doc_id, doc_data) in enumerate(documents.items(), 1):
            print(f"\nDocument {i}: {doc_id}")
            print(f"  Content length: {len(doc_data.get('content', ''))}")
            print(f"  Metadata: {doc_data.get('metadata', {})}")
            print(f"  Has embedding: {len(doc_data.get('embedding', [])) > 0}")
            
            # Show content preview
            content = doc_data.get('content', '')
            if len(content) > 100:
                preview = content[:100] + "..."
            else:
                preview = content
            print(f"  Content preview: {repr(preview)}")
        
        # Test some sample searches
        print(f"\nTesting sample searches:")
        test_searches = ["net worth", "financial", "retirement", "income", "assets"]
        
        for search_term in test_searches:
            matches = []
            for doc_id, doc_data in documents.items():
                content = doc_data.get('content', '').lower()
                if search_term.lower() in content:
                    matches.append(doc_id)
            
            print(f"  '{search_term}': {len(matches)} matches")
            if matches:
                print(f"    Matching docs: {matches}")
        
    except Exception as e:
        print(f"Error analyzing vector store: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_vector_store()