#!/usr/bin/env python3
"""Debug vector store contents and structure"""

import json
import os
import sys
sys.path.append('/app')  # Docker path

def main():
    """Debug vector store"""
    vector_path = "/tmp/vector_store.json"
    
    if not os.path.exists(vector_path):
        print(f"❌ Vector store not found at {vector_path}")
        return
    
    try:
        with open(vector_path, 'r') as f:
            data = json.load(f)
        
        documents = data.get('documents', {})
        print(f"📊 Found {len(documents)} documents in vector store")
        
        for doc_id, doc_data in documents.items():
            print(f"\n🔍 Document: {doc_id}")
            print(f"   Content length: {len(doc_data.get('content', ''))}")
            print(f"   Metadata: {doc_data.get('metadata', {})}")
            print(f"   Has embedding: {len(doc_data.get('embedding', [])) > 0}")
            
            # Show first 100 chars of content
            content = doc_data.get('content', '')[:100]
            print(f"   Content preview: {content}...")
            
    except Exception as e:
        print(f"❌ Error reading vector store: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()