import discord
from discord.ext import commands
import traceback
import sys
from utils.logger import get_logger
from config.config import config
import aiohttp

logger = get_logger(__name__)

class ErrorHandler:
    """Global error handler for the bot."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    async def send_to_webhook(self, error: Exception, ctx=None, interaction=None):
        """Send error details to configured webhook URL."""
        if not config.ERROR_WEBHOOK_URL:
            return
        
        embed = discord.Embed(
            title="❌ Bot Error",
            description=f"```py\n{str(error)[:1900]}\n```",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        
        if ctx:
            embed.add_field(name="Command", value=f"`{ctx.command}`" if ctx.command else "Unknown", inline=False)
            embed.add_field(name="User", value=f"{ctx.author} ({ctx.author.id})", inline=True)
            embed.add_field(name="Guild", value=f"{ctx.guild.name} ({ctx.guild.id})" if ctx.guild else "DM", inline=True)
        elif interaction:
            embed.add_field(name="Command", value=f"`{interaction.command.name}`" if interaction.command else "Unknown", inline=False)
            embed.add_field(name="User", value=f"{interaction.user} ({interaction.user.id})", inline=True)
            embed.add_field(name="Guild", value=f"{interaction.guild.name} ({interaction.guild.id})" if interaction.guild else "DM", inline=True)
        
        try:
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(config.ERROR_WEBHOOK_URL, session=session)
                await webhook.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to send error to webhook: {e}")
    
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Handle command errors for prefix commands (if any)."""
        logger.error(f"Command error in {ctx.command}: {error}")
        await self.send_to_webhook(error, ctx=ctx)
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """Handle slash command errors."""
        # Extract original error
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            await interaction.response.send_message(f"⏳ Command on cooldown. Try again in {error.retry_after:.0f} seconds.", ephemeral=True)
            return
        
        if isinstance(error, discord.app_commands.MissingPermissions):
            await interaction.response.send_message(f"❌ You are missing permissions: {', '.join(error.missing_permissions)}", ephemeral=True)
            return
        
        if isinstance(error, discord.app_commands.BotMissingPermissions):
            await interaction.response.send_message(f"❌ Bot is missing permissions: {', '.join(error.missing_permissions)}", ephemeral=True)
            return
        
        if isinstance(error, discord.app_commands.CheckFailure):
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return
        
        # Log unexpected errors
        logger.error(f"Unhandled slash command error in {interaction.command}: {error}")
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        await self.send_to_webhook(error, interaction=interaction)
        
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An unexpected error occurred. The bot owner has been notified.", ephemeral=True)
            else:
                await interaction.followup.send("❌ An unexpected error occurred. The bot owner has been notified.", ephemeral=True)
        except:
            pass

from datetime import datetime
