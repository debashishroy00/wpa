#!/usr/bin/env python3
"""
WealthPath AI - Direct Startup Script
Bypasses all migration issues by starting Gunicorn directly
"""
import os
import subprocess
import sys

def main():
    print("==> Starting WealthPath AI Backend...")
    print("==> Skipping migrations - tables already exist in Supabase")
    print("==> Starting Gunicorn server directly...")
    
    # Get the port from environment
    port = os.getenv('PORT', '8000')
    
    # Start Gunicorn directly
    cmd = [
        'gunicorn', 
        'app.main:app',
        '--workers', '1',
        '--worker-class', 'uvicorn.workers.UvicornWorker',
        '--bind', f'0.0.0.0:{port}'
    ]
    
    print(f"==> Executing: {' '.join(cmd)}")
    
    # Replace the current process with Gunicorn
    os.execvp('gunicorn', cmd)

if __name__ == '__main__':
    main()