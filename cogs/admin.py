import discord
from discord.ext import commands
from discord import app_commands, Interaction
from utils.blacklist import BlacklistManager
from utils.permissions import is_owner
from utils.logger import get_logger
from services.guild_config_service import GuildConfigService
from services.ticket_service import TicketService

logger = get_logger(__name__)

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.blacklist = BlacklistManager(bot.db)
    
    # ========== OWNER-ONLY COMMANDS ==========
    @app_commands.command(name="blacklist", description="Manage global blacklist (owner only)")
    @app_commands.default_permissions(administrator=True)
    async def blacklist_group(self, interaction: Interaction, action: str, target_type: str, target_id: str, reason: str = None):
        """
        action: add, remove, list
        target_type: user, guild
        target_id: Discord ID
        """
        if not await is_owner(interaction):
            await interaction.response.send_message("❌ This command is only available to the bot owner.", ephemeral=True)
            return
        
        action = action.lower()
        target_type = target_type.lower()
        
        try:
            target_id_int = int(target_id)
        except ValueError:
            await interaction.response.send_message("❌ Invalid ID. Must be a number.", ephemeral=True)
            return
        
        if action == "add":
            if target_type not in ["user", "guild"]:
                await interaction.response.send_message("❌ target_type must be 'user' or 'guild'.", ephemeral=True)
                return
            await self.blacklist.add_blacklist(target_id_int, target_type, reason, interaction.user.id)
            embed = discord.Embed(
                title="✅ Blacklist Added",
                description=f"**Type:** {target_type}\n**ID:** {target_id}\n**Reason:** {reason or 'No reason provided'}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        elif action == "remove":
            success = await self.blacklist.remove_blacklist(target_id_int)
            if success:
                embed = discord.Embed(
                    title="✅ Blacklist Removed",
                    description=f"Removed {target_id_int} from blacklist.",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="❌ Not Found",
                    description=f"{target_id_int} was not blacklisted.",
                    color=discord.Color.orange()
                )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        elif action == "list":
            items = await self.blacklist.get_all_blacklisted()
            if not items:
                await interaction.response.send_message("No blacklisted items.", ephemeral=True)
                return
            description = "\n".join([f"**{item['type']}** {item['id']} - {item.get('reason', 'No reason')}" for item in items[:20]])
            embed = discord.Embed(
                title="Blacklisted Items",
                description=description or "Too many items to display.",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        else:
            await interaction.response.send_message("❌ Action must be add, remove, or list.", ephemeral=True)
    
    @app_commands.command(name="stats", description="Show bot statistics (owner only)")
    async def stats(self, interaction: Interaction):
        if not await is_owner(interaction):
            await interaction.response.send_message("❌ This command is only available to the bot owner.", ephemeral=True)
            return
        
        guild_count = len(self.bot.guilds)
        user_count = len(set(self.bot.users))
        
        # Get ticket stats from database
        ticket_service = TicketService(self.bot.db)
        collection = await ticket_service._get_collection()
        total_tickets = await collection.count_documents({})
        open_tickets = await collection.count_documents({"status": {"$in": ["open", "claimed", "reopened"]}})
        
        embed = discord.Embed(title="Bot Statistics", color=discord.Color.green())
        embed.add_field(name="Guilds", value=str(guild_count), inline=True)
        embed.add_field(name="Users", value=str(user_count), inline=True)
        embed.add_field(name="Total Tickets", value=str(total_tickets), inline=True)
        embed.add_field(name="Open Tickets", value=str(open_tickets), inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
