from discord import Interaction, Member
from models.guild_config import GuildConfig
from config.config import config

async def is_staff(member: Member, guild_config: GuildConfig) -> bool:
    """Check if a member has any staff role."""
    if not guild_config.staff_role_ids:
        return False
    member_role_ids = [role.id for role in member.roles]
    return any(role_id in member_role_ids for role_id in guild_config.staff_role_ids)

async def is_admin(interaction: Interaction) -> bool:
    """Check if the user has administrator permission in the guild."""
    if not interaction.guild:
        return False
    return interaction.user.guild_permissions.administrator

def has_permission(interaction: Interaction, permission: str = "administrator"):
    """Check if user has a specific guild permission."""
    return getattr(interaction.user.guild_permissions, permission, False)

def is_ticket_channel(channel) -> bool:
    """Simple heuristic: channel name starts with 'ticket-'"""
    return hasattr(channel, "name") and channel.name.startswith("ticket-")

async def check_staff(interaction: Interaction) -> bool:
    """Decorator-like check for staff status in a command."""
    if not interaction.guild:
        return False
    from services.guild_config_service import GuildConfigService
    config_service = GuildConfigService(interaction.client.db)
    config = await config_service.get_config(interaction.guild.id)
    return await is_staff(interaction.user, config)

async def is_owner(interaction: Interaction) -> bool:
    """Check if the user is the bot owner (from application info)."""
    if not interaction.client.application:
        app = await interaction.client.application_info()
        return interaction.user.id == app.owner.id
    return interaction.user.id == interaction.client.application.owner.id

async def check_blacklist(interaction: Interaction) -> bool:
    """Check if user or guild is blacklisted (to be used as a command check)."""
    from utils.blacklist import BlacklistManager
    blacklist = BlacklistManager(interaction.client.db)
    if await blacklist.is_blacklisted(interaction.user.id, "user"):
        await interaction.response.send_message("❌ You are blacklisted from using this bot.", ephemeral=True)
        return False
    if interaction.guild and await blacklist.is_blacklisted(interaction.guild.id, "guild"):
        await interaction.response.send_message("❌ This server is blacklisted from using this bot.", ephemeral=True)
        return False
    return True
