import discord
from discord.ext import commands
from discord import app_commands
from utils import get_logger

logger = get_logger(__name__)

class InfoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check bot latency and database connection")
    async def ping(self, interaction: discord.Interaction):
        """Simple ping command to test bot responsiveness."""
        # Check MongoDB connection
        db_status = "Connected" if self.bot.db and self.bot.db.client else "Disconnected"
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="Pong!",
            description=f"**Latency:** {latency}ms\n**Database:** {db_status}",
            color=discord.Color.green() if db_status == "Connected" else discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info(f"Ping command used by {interaction.user} in guild {interaction.guild_id}")

async def setup(bot: commands.Bot):
    await bot.add_cog(InfoCog(bot))
