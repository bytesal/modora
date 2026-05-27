import asyncio
import json
from aiohttp import web
from config.config import config
import logging

logger = logging.getLogger(__name__)

class HealthCheckServer:
    """Simple HTTP server for Railway health checks."""
    
    def __init__(self, bot):
        self.bot = bot
        self.app = web.Application()
        self.app.router.add_get('/health', self.health_handler)
        self.runner = None
        self.site = None
    
    async def health_handler(self, request):
        """Return bot status."""
        status = {
            "status": "ok" if not self.bot.is_closed() else "unhealthy",
            "guilds": len(self.bot.guilds),
            "latency": round(self.bot.latency * 1000),
            "database": "connected" if self.bot.db and self.bot.db.client else "disconnected"
        }
        return web.Response(text=json.dumps(status), content_type="application/json")
    
    async def start(self):
        """Start the health check server."""
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            self.site = web.TCPSite(self.runner, '0.0.0.0', config.HEALTH_CHECK_PORT)
            await self.site.start()
            logger.info(f"Health check server started on port {config.HEALTH_CHECK_PORT}")
        except Exception as e:
            logger.error(f"Failed to start health check server: {e}")
    
    async def stop(self):
        """Stop the health check server."""
        if self.runner:
            await self.runner.cleanup()
            logger.info("Health check server stopped")
