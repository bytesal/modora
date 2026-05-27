from discord import Interaction, Member, Role
from typing import Union
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
    """Decorator-style permission check (to be used in commands)."""
    return getattr(interaction.user.guild_permissions, permission, False)
