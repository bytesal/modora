import asyncio
import discord
from discord.ext import commands
from config.config import config
from database.mongo import mongo
from utils.logger import setup_logger, get_logger
from utils.error_handler import ErrorHandler
from utils.blacklist import BlacklistManager
from utils.rate_limiter import RateLimiter
from utils.health_check import HealthCheckServer
import os
import signal

setup_logger()
logger = get_logger()

class ModMailBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.dm_messages = True

        if config.DISABLE_VOICE:
            discord.VoiceClient = None

        super().__init__(
            command_prefix=config.BOT_PREFIX,
            intents=intents,
            help_command=None,
            max_messages=config.MAX_MESSAGES_CACHE
        )
        self.db = None
        self.error_handler = None
        self.blacklist = None
        self.dm_rate_limiter = RateLimiter(max_messages=5, per_seconds=60)
        self.health_server = None

    async def setup_hook(self):
        logger.info("Setting up bot...")
        await mongo.connect()
        self.db = mongo
        self.blacklist = BlacklistManager(self.db)
        self.error_handler = ErrorHandler(self)
        self.health_server = HealthCheckServer(self)
        await self.health_server.start()
        await self.load_cogs()
        await self.tree.sync()
        logger.info("Slash commands synced globally")

    async def load_cogs(self):
        cogs_folder = "cogs"
        for filename in os.listdir(cogs_folder):
            if filename.endswith(".py") and not filename.startswith("__"):
                try:
                    await self.load_extension(f"{cogs_folder}.{filename[:-3]}")
                    logger.info(f"Loaded cog: {filename}")
                except Exception as e:
                    logger.error(f"Failed to load cog {filename}: {e}")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")
        logger.info(f"Memory usage: {self._get_memory_usage()}")
        # Set activity after websocket is ready
        activity = discord.Activity(type=discord.ActivityType.watching, name=config.BOT_ACTIVITY)
        await self.change_presence(activity=activity)

    def _get_memory_usage(self):
        try:
            import psutil
            process = psutil.Process()
            return f"{process.memory_info().rss / 1024 / 1024:.2f} MB"
        except ImportError:
            return "N/A (psutil not installed)"

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if isinstance(message.channel, discord.DMChannel):
            if await self.blacklist.is_blacklisted(message.author.id, "user"):
                await message.channel.send("❌ You are blacklisted from using this bot.")
                return
            limited, wait = self.dm_rate_limiter.check_and_update(message.author.id)
            if limited:
                await message.channel.send(f"⏳ You are sending messages too quickly. Please wait {wait} seconds.")
                return
        await self.process_commands(message)

    async def on_command_error(self, ctx, error):
        if self.error_handler:
            await self.error_handler.on_command_error(ctx, error)

    async def on_error(self, event_method, *args, **kwargs):
        logger.error(f"Unhandled error in {event_method}")
        import traceback
        traceback.print_exc()

    async def close(self):
        logger.info("Shutting down...")
        if self.health_server:
            await self.health_server.stop()
        await mongo.disconnect()
        await super().close()

def main():
    bot = ModMailBot()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(bot.close()))

    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        await bot.error_handler.on_app_command_error(interaction, error)

    try:
        bot.run(config.BOT_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()
