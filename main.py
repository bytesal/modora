import asyncio
import discord
from discord.ext import commands
from config.config import config
from database.mongo import mongo
from utils.logger import setup_logger, get_logger
import os

# Initialise logger
setup_logger()
logger = get_logger()

class ModMailBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.dm_messages = True  # To receive user DMs for replies
        
        super().__init__(
            command_prefix=config.BOT_PREFIX,
            intents=intents,
            help_command=None  # We'll implement custom help later
        )
        self.db = None  # MongoDB instance will be attached here

    async def setup_hook(self):
        """Async setup before bot starts."""
        logger.info("Setting up bot...")
        
        # Connect to MongoDB
        await mongo.connect()
        self.db = mongo
        
        # Load all cogs from cogs/ directory
        await self.load_cogs()
        
        # Sync slash commands (globally or per guild? globally for now)
        await self.tree.sync()
        logger.info("Slash commands synced globally")
        
        # Set bot activity
        activity = discord.Activity(type=discord.ActivityType.watching, name=config.BOT_ACTIVITY)
        await self.change_presence(activity=activity)

    async def load_cogs(self):
        """Load all cog files from the cogs folder."""
        cogs_folder = "cogs"
        for filename in os.listdir(cogs_folder):
            if filename.endswith(".py") and not filename.startswith("__"):
                try:
                    await self.load_extension(f"{cogs_folder}.{filename[:-3]}")
                    logger.info(f"Loaded cog: {filename}")
                except Exception as e:
                    logger.error(f"Failed to load cog {filename}: {e}")

    async def on_ready(self):
        """Event triggered when bot is ready."""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")

    async def on_message(self, message: discord.Message):
        """Handle DMs for ModMail (to be expanded later)."""
        if message.author.bot:
            return
        
        # For now, just log DMs
        if isinstance(message.channel, discord.DMChannel):
            logger.info(f"DM from {message.author}: {message.content}")
        
        # Ensure commands still process
        await self.process_commands(message)

    async def close(self):
        """Clean up on shutdown."""
        logger.info("Shutting down...")
        await mongo.disconnect()
        await super().close()

def main():
    bot = ModMailBot()
    try:
        bot.run(config.BOT_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()
