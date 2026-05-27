from discord import Interaction, Member
from models.guild_config import GuildConfig

async def is_staff(member: Member, config: GuildConfig) -> bool:
    """Check if a member has any staff role."""
    if not config.staff_role_ids:
        return False
    member_role_ids = [role.id for role in member.roles]
    return any(role_id in member_role_ids for role_id in config.staff_role_ids)

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
