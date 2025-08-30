# Docker BaseUrl Configuration Fix

## Problem
The frontend was experiencing `baseUrl` configuration errors when running in Docker because:

1. The frontend container couldn't reach the backend at `localhost:8000` (localhost inside container != host machine)
2. Docker containers need to communicate using the Docker network names
3. Browser requests from the host need different URLs than container-to-container communication

## Solution

### 1. Updated Docker Compose Configuration
```yaml
environment:
  - VITE_API_BASE_URL=http://backend:8000          # For container-to-container
  - VITE_API_BASE_URL_EXTERNAL=http://localhost:8000  # For browser requests
```

### 2. Enhanced API URL Detection
The `getApiBaseUrl()` function now:
- Checks for environment variables first
- Handles Docker internal vs external URLs
- Provides better error handling and fallbacks

### 3. Added Environment Files
- `.env.docker` - Docker-specific configuration
- Updated `.env.development` - Local development

## Testing

Run the debug script to check your Docker setup:
```bash
# PowerShell (Windows)
./scripts/debug-docker-network.ps1

# Bash (Linux/Mac)
./scripts/debug-docker-network.sh
```

## Common Issues

1. **Backend not accessible**: Check if backend container is running
2. **Network errors**: Verify Docker network configuration
3. **Environment variables**: Ensure VITE_ variables are properly set

## Quick Fixes

1. Restart containers: `docker-compose down && docker-compose up`
2. Rebuild frontend: `docker-compose build frontend`
3. Check logs: `docker-compose logs frontend backend`