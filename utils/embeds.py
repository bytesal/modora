import discord
from datetime import datetime
from typing import Union

def create_ticket_embed(user: discord.User, username: str) -> discord.Embed:
    """Embed sent in new ticket channel."""
    embed = discord.Embed(
        title="📬 ModMail Ticket",
        description=f"**User:** {user.mention} ({user.id})\n**Username:** {username}\n\nUse the buttons below to manage this ticket.",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="Ticket created")
    return embed

def create_reply_embed(author: Union[discord.User, discord.Member], content: str, is_staff: bool) -> discord.Embed:
    """Embed for relaying messages between user and staff."""
    if is_staff:
        title = "📨 Staff Reply"
        color = discord.Color.green()
    else:
        title = "💬 User Reply"
        color = discord.Color.orange()
    
    embed = discord.Embed(
        title=title,
        description=content,
        color=color,
        timestamp=datetime.utcnow()
    )
    embed.set_author(name=str(author), icon_url=author.display_avatar.url)
    return embed
