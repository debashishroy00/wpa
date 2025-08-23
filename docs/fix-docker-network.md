# Fix Docker Network Conflict

## Quick Fix Commands

Run these commands in the project root (`C:\projects\wpa`):

```cmd
# 1. Stop and remove existing containers/networks
docker-compose down

# 2. Remove any conflicting networks (optional)
docker network prune -f

# 3. Start with the updated network configuration
docker-compose up -d

# 4. Check if services are running
docker-compose ps
```

## Alternative: Use Different Subnet

If the issue persists, you can try different subnet ranges in `docker-compose.yml`:

```yaml
networks:
  wpa-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.30.0.0/16  # Try this if 172.25 still conflicts
        # Or try: 192.168.100.0/24
```

## Check Network Conflicts

To see what networks are already in use:

```cmd
# List all Docker networks
docker network ls

# Inspect a specific network
docker network inspect bridge

# See network IP ranges
docker network ls -q | xargs docker network inspect | grep -E "Name|Subnet"
```

## Troubleshooting

If you continue having issues:

1. **Restart Docker Desktop** completely
2. **Use host networking** (add to services):
   ```yaml
   network_mode: "host"
   ```
3. **Remove custom network** entirely:
   ```yaml
   # Comment out the networks section and remove network references from services
   ```

The updated configuration should resolve the network conflict!