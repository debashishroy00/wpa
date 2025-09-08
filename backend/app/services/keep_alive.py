"""
Keep-alive service to prevent Render cold starts
"""
import asyncio
import httpx
import structlog
from datetime import datetime
from app.core.config import settings

logger = structlog.get_logger()

class KeepAliveService:
    """Service to keep Render deployment warm"""
    
    def __init__(self):
        self.is_running = False
        self.ping_interval = 600  # 10 minutes (will be set from config)
        self.health_url = None
        
    def set_health_url(self, url: str, interval_minutes: int = 10):
        """Set the health check URL and ping interval"""
        self.health_url = url
        self.ping_interval = interval_minutes * 60  # Convert to seconds
        
    async def start_keep_alive(self):
        """Start the keep-alive ping loop"""
        if self.is_running or not self.health_url:
            return
            
        self.is_running = True
        logger.info("Starting keep-alive service", url=self.health_url, interval=self.ping_interval)
        
        while self.is_running:
            try:
                await asyncio.sleep(self.ping_interval)
                await self._ping_health()
            except Exception as e:
                logger.error("Keep-alive ping failed", error=str(e))
                
    async def stop_keep_alive(self):
        """Stop the keep-alive service"""
        self.is_running = False
        logger.info("Stopping keep-alive service")
        
    async def _ping_health(self):
        """Ping the health endpoint"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.health_url)
                if response.status_code == 200:
                    logger.debug("Keep-alive ping successful", timestamp=datetime.now().isoformat())
                else:
                    logger.warning("Keep-alive ping returned non-200", status_code=response.status_code)
        except Exception as e:
            logger.error("Keep-alive ping exception", error=str(e))

# Global instance
keep_alive_service = KeepAliveService()