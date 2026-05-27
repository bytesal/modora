import discord
from discord.ext import commands
from discord import app_commands, Interaction
from services.ticket_service import TicketService
from services.guild_config_service import GuildConfigService
from utils.permissions import is_staff, is_ticket_channel
from utils.logger import get_logger
from utils.embeds import create_ticket_embed, create_reply_embed
from utils.cooldown import CooldownManager
from services.log_service import LogService
from views.ticket_controls import TicketControlView

logger = get_logger(__name__)

class ModMailCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ticket_service = TicketService(bot.db)
        self.cooldown_manager = CooldownManager(bot.db)
        self.log_service = LogService(bot)

    # ========== SLASH COMMANDS ==========
    @app_commands.command(name="modmail", description="Open a new ModMail ticket")
    async def modmail_new(self, interaction: Interaction, message: str = None):
        """Open a new ticket. If message is provided, use as initial message."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
        
        # Check if user already has open ticket
        config_service = GuildConfigService(self.bot.db)
        config = await config_service.get_config(interaction.guild_id)
        
        existing = await self.ticket_service.get_open_ticket(interaction.user.id, interaction.guild_id)
        if existing:
            embed = discord.Embed(
                title="❌ Ticket Already Open",
                description=f"You already have an open ticket: <#{existing.channel_id}>\nPlease close it before opening a new one.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Cooldown check
        remaining = await self.cooldown_manager.get_remaining_cooldown(
            interaction.user.id, interaction.guild_id, config.cooldown_seconds
        )
        if remaining > 0:
            embed = discord.Embed(
                title="⏳ Cooldown",
                description=f"Please wait {remaining} seconds before opening another ticket.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        # Create ticket channel
        channel = await self.ticket_service.create_ticket_channel(
            guild=interaction.guild,
            user=interaction.user,
            config=config
        )
        
        if not channel:
            await interaction.followup.send("❌ Failed to create ticket. Please check category configuration.", ephemeral=True)
            return
        
        # Get the ticket document
        ticket = await self.ticket_service.get_ticket_by_channel(channel.id)
        
        # Send initial message in channel
        embed = create_ticket_embed(interaction.user, interaction.user.name)
        view = TicketControlView(self.ticket_service, interaction.user.id, interaction.guild.id)
        await channel.send(embed=embed, view=view)
        
        # Send initial user message if provided
        if message:
            await channel.send(f"**{interaction.user}:** {message}")
        
        await interaction.followup.send(f"✅ Ticket created: {channel.mention}", ephemeral=True)
        
        # Log ticket creation
        if ticket:
            await self.log_service.log_ticket_create(interaction.guild_id, interaction.user, ticket, channel)
        
        logger.info(f"New ticket created by {interaction.user} in guild {interaction.guild.id}")

    @app_commands.command(name="close", description="Close the current ticket")
    async def close_ticket(self, interaction: Interaction):
        """Close the ticket channel where command is used."""
        if not await self._check_staff_and_ticket(interaction):
            return
        
        await interaction.response.defer()
        ticket = await self.ticket_service.get_ticket_by_channel(interaction.channel_id)
        if not ticket:
            await interaction.followup.send("❌ This is not a valid ticket channel.", ephemeral=True)
            return
        
        # Get user for logging
        user = self.bot.get_user(ticket.user_id)
        if not user:
            try:
                user = await self.bot.fetch_user(ticket.user_id)
            except:
                user = None
        
        # Send closing message
        await interaction.followup.send("🔒 Closing ticket in 5 seconds...")
        await self.ticket_service.close_ticket(ticket, interaction.user.id)
        
        # Log ticket close
        await self.log_service.log_ticket_close(interaction.guild_id, user, ticket, interaction.user, transcript_url=None)
        
        # Delete channel after a short delay
        await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.timedelta(seconds=5))
        await interaction.channel.delete()
        logger.info(f"Ticket {ticket.ticket_id} closed by {interaction.user}")

    @app_commands.command(name="claim", description="Claim the current ticket")
    async def claim_ticket(self, interaction: Interaction):
        if not await self._check_staff_and_ticket(interaction):
            return
        
        ticket = await self.ticket_service.get_ticket_by_channel(interaction.channel_id)
        if not ticket:
            await interaction.response.send_message("❌ This is not a valid ticket channel.", ephemeral=True)
            return
        
        if ticket.staff_id:
            await interaction.response.send_message(f"❌ Ticket already claimed by <@{ticket.staff_id}>", ephemeral=True)
            return
        
        await self.ticket_service.claim_ticket(ticket.ticket_id, interaction.user.id)
        await interaction.response.send_message(f"✅ You have claimed this ticket.", ephemeral=False)
        
        # Update the embed in the channel
        embed = discord.Embed(title="Ticket Claimed", description=f"Claimed by {interaction.user.mention}", color=discord.Color.green())
        await interaction.channel.send(embed=embed)
        
        # Log claim
        await self.log_service.log_ticket_claim(interaction.guild_id, ticket, interaction.user)
        logger.info(f"Ticket {ticket.ticket_id} claimed by {interaction.user}")

    @app_commands.command(name="rename", description="Rename the current ticket channel")
    async def rename_ticket(self, interaction: Interaction, new_name: str):
        if not await self._check_staff_and_ticket(interaction):
            return
        
        ticket = await self.ticket_service.get_ticket_by_channel(interaction.channel_id)
        if not ticket:
            await interaction.response.send_message("❌ This is not a valid ticket channel.", ephemeral=True)
            return
        
        # Capture old name for logging
        old_name = interaction.channel.name
        
        # Sanitize name: lowercase, no spaces
        clean_name = new_name.lower().replace(" ", "-")[:100]
        try:
            await interaction.channel.edit(name=f"ticket-{clean_name}")
            await interaction.response.send_message(f"✅ Channel renamed to `{clean_name}`", ephemeral=False)
            
            # Log rename
            await self.log_service.log_ticket_rename(interaction.guild_id, ticket, old_name, clean_name, interaction.user)
            logger.info(f"Ticket channel renamed from {old_name} to {clean_name} by {interaction.user}")
        except Exception as e:
            logger.error(f"Failed to rename channel: {e}")
            await interaction.response.send_message("❌ Failed to rename channel.", ephemeral=True)

    # ========== EVENT HANDLERS ==========
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        
        # Handle DMs from users (user replying to ModMail)
        if isinstance(message.channel, discord.DMChannel):
            await self.handle_user_dm(message)
            return
        
        # Handle messages in ticket channels (staff replying)
        if message.guild and isinstance(message.channel, discord.TextChannel):
            await self.handle_staff_reply(message)

    async def handle_user_dm(self, message: discord.Message):
        """User sent a DM to the bot – relay to their open ticket channel."""
        user = message.author
        ticket = await self.ticket_service.get_open_ticket(user.id)
        if not ticket:
            # No open ticket, send info message
            embed = discord.Embed(
                title="ModMail",
                description="You don't have an open ticket. Use `/modmail new` or the ticket panel button to create one.",
                color=discord.Color.blue()
            )
            await user.send(embed=embed)
            return
        
        # Fetch guild and channel
        guild = self.bot.get_guild(ticket.guild_id)
        if not guild:
            logger.error(f"Guild {ticket.guild_id} not found")
            return
        
        channel = guild.get_channel(ticket.channel_id)
        if not channel:
            await user.send("❌ Your ticket channel no longer exists. Please create a new ticket.")
            await self.ticket_service.close_ticket(ticket, None)
            return
        
        # Relay message to staff channel
        embed = create_reply_embed(user, message.content, is_staff=False)
        await channel.send(embed=embed)
        
        # Update last activity
        await self.ticket_service.update_activity(ticket.ticket_id)
        
        # Log user reply
        await self.log_service.log_user_reply(ticket.guild_id, ticket, user, message.content)
        logger.info(f"User reply from {user} in ticket {ticket.ticket_id}")

    async def handle_staff_reply(self, message: discord.Message):
        """Staff message in a ticket channel – relay to user's DM."""
        # Check if channel is a ticket channel
        ticket = await self.ticket_service.get_ticket_by_channel(message.channel.id)
        if not ticket:
            return
        
        # Check if sender is staff
        config_service = GuildConfigService(self.bot.db)
        config = await config_service.get_config(message.guild.id)
        member = message.guild.get_member(message.author.id)
        if not member:
            return
        
        if not await is_staff(member, config):
            # Non-staff should not be able to send messages in ticket channels normally, but just in case
            await message.delete()
            await message.author.send("You cannot reply in this ticket channel. Staff only.")
            return
        
        # Get the user who opened the ticket
        user = self.bot.get_user(ticket.user_id)
        if not user:
            try:
                user = await self.bot.fetch_user(ticket.user_id)
            except:
                await message.channel.send("❌ Could not find the user to relay the message.")
                return
        
        # Relay to user's DM
        embed = create_reply_embed(message.author, message.content, is_staff=True)
        try:
            await user.send(embed=embed)
        except discord.Forbidden:
            await message.channel.send("⚠️ Could not DM the user. They may have DMs disabled or blocked the bot.")
        
        # Update activity
        await self.ticket_service.update_activity(ticket.ticket_id)
        
        # Log staff reply
        await self.log_service.log_staff_reply(ticket.guild_id, ticket, message.author, message.content)
        logger.info(f"Staff reply from {message.author} in ticket {ticket.ticket_id}")

    async def _check_staff_and_ticket(self, interaction: Interaction) -> bool:
        """Helper to verify staff permission and that command is used in a guild ticket channel."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return False
        
        config_service = GuildConfigService(self.bot.db)
        config = await config_service.get_config(interaction.guild_id)
        if not await is_staff(interaction.user, config):
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return False
        
        if not is_ticket_channel(interaction.channel):
            await interaction.response.send_message("❌ This command can only be used in a ticket channel.", ephemeral=True)
            return False
        
        return True

async def setup(bot: commands.Bot):
    await bot.add_cog(ModMailCog(bot))
