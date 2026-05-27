import discord
from discord.ext import commands
from discord import app_commands, Interaction
from typing import Union
from services.ticket_service import TicketService
from services.guild_config_service import GuildConfigService
from utils.permissions import is_staff, is_ticket_channel, check_blacklist
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

    @app_commands.group(name="modmail", description="ModMail commands")
    async def modmail_group(self, interaction: Interaction):
        if interaction.invoked_subcommand is None:
            embed = discord.Embed(
                title="ModMail Commands",
                description="Use `/modmail new` to open a ticket.\nUse `/modmail adduser` or `/modmail removeuser` to manage users in a ticket channel.",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @modmail_group.command(name="new", description="Open a new ModMail ticket")
    async def modmail_new(self, interaction: Interaction, message: str = None):
        if not await check_blacklist(interaction):
            return
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
        
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
        
        channel = await self.ticket_service.create_ticket_channel(
            guild=interaction.guild,
            user=interaction.user,
            config=config
        )
        
        if not channel:
            await interaction.followup.send("❌ Failed to create ticket. Please check category configuration.", ephemeral=True)
            return
        
        ticket = await self.ticket_service.get_ticket_by_channel(channel.id)
        
        embed = create_ticket_embed(interaction.user, interaction.user.name)
        view = TicketControlView(self.ticket_service, interaction.user.id, interaction.guild.id)
        await channel.send(embed=embed, view=view)
        
        if message:
            await channel.send(f"**{interaction.user}:** {message}")
        
        await interaction.followup.send(f"✅ Ticket created: {channel.mention}", ephemeral=True)
        
        if ticket:
            await self.log_service.log_ticket_create(interaction.guild_id, interaction.user, ticket, channel)
        
        logger.info(f"New ticket created by {interaction.user} in guild {interaction.guild.id}")

    @modmail_group.command(name="adduser", description="Add a user to the current ticket")
    async def add_user(self, interaction: Interaction, user: discord.User):
        if not await self._check_staff_and_ticket(interaction):
            return
        try:
            await interaction.channel.set_permissions(user, read_messages=True, send_messages=True, attach_files=True, embed_links=True)
            await interaction.response.send_message(f"✅ Added {user.mention} to this ticket.", ephemeral=False)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to add user: {e}", ephemeral=True)

    @modmail_group.command(name="removeuser", description="Remove a user from the current ticket")
    async def remove_user(self, interaction: Interaction, user: discord.User):
        if not await self._check_staff_and_ticket(interaction):
            return
        ticket = await self.ticket_service.get_ticket_by_channel(interaction.channel_id)
        if ticket and user.id == ticket.user_id:
            await interaction.response.send_message("❌ Cannot remove the original ticket owner.", ephemeral=True)
            return
        try:
            await interaction.channel.set_permissions(user, read_messages=False, send_messages=False)
            await interaction.response.send_message(f"✅ Removed {user.mention} from this ticket.", ephemeral=False)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to remove user: {e}", ephemeral=True)

    @modmail_group.command(name="close", description="Close the current ticket")
    async def close_ticket(self, interaction: Interaction):
        if not await self._check_staff_and_ticket(interaction):
            return
        await interaction.response.defer()
        ticket = await self.ticket_service.get_ticket_by_channel(interaction.channel_id)
        if not ticket:
            await interaction.followup.send("❌ This is not a valid ticket channel.", ephemeral=True)
            return
        
        user = self.bot.get_user(ticket.user_id)
        if not user:
            try:
                user = await self.bot.fetch_user(ticket.user_id)
            except:
                user = None
        
        await interaction.followup.send("🔒 Closing ticket in 5 seconds...")
        await self.ticket_service.close_ticket(ticket, interaction.user.id)
        await self.log_service.log_ticket_close(interaction.guild_id, user, ticket, interaction.user, transcript_url=None)
        
        await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.timedelta(seconds=5))
        await interaction.channel.delete()
        logger.info(f"Ticket {ticket.ticket_id} closed by {interaction.user}")

    @modmail_group.command(name="claim", description="Claim the current ticket")
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
        embed = discord.Embed(title="Ticket Claimed", description=f"Claimed by {interaction.user.mention}", color=discord.Color.green())
        await interaction.channel.send(embed=embed)
        await self.log_service.log_ticket_claim(interaction.guild_id, ticket, interaction.user)
        logger.info(f"Ticket {ticket.ticket_id} claimed by {interaction.user}")

    @modmail_group.command(name="rename", description="Rename the current ticket channel")
    async def rename_ticket(self, interaction: Interaction, new_name: str):
        if not await self._check_staff_and_ticket(interaction):
            return
        ticket = await self.ticket_service.get_ticket_by_channel(interaction.channel_id)
        if not ticket:
            await interaction.response.send_message("❌ This is not a valid ticket channel.", ephemeral=True)
            return
        old_name = interaction.channel.name
        clean_name = new_name.lower().replace(" ", "-")[:100]
        try:
            await interaction.channel.edit(name=f"ticket-{clean_name}")
            await interaction.response.send_message(f"✅ Channel renamed to `{clean_name}`", ephemeral=False)
            await self.log_service.log_ticket_rename(interaction.guild_id, ticket, old_name, clean_name, interaction.user)
            logger.info(f"Ticket channel renamed from {old_name} to {clean_name} by {interaction.user}")
        except Exception as e:
            logger.error(f"Failed to rename channel: {e}")
            await interaction.response.send_message("❌ Failed to rename channel.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if isinstance(message.channel, discord.DMChannel):
            await self.handle_user_dm(message)
            return
        if message.guild and isinstance(message.channel, discord.TextChannel):
            await self.handle_staff_reply(message)

    async def handle_user_dm(self, message: discord.Message):
        user = message.author
        if await self.bot.blacklist.is_blacklisted(user.id, "user"):
            await user.send("❌ You are blacklisted from using this bot.")
            return
        
        ticket = await self.ticket_service.get_open_ticket(user.id)
        if not ticket:
            embed = discord.Embed(
                title="ModMail",
                description="You don't have an open ticket. Use `/modmail new` or the ticket panel button to create one.",
                color=discord.Color.blue()
            )
            await user.send(embed=embed)
            return
        
        guild = self.bot.get_guild(ticket.guild_id)
        if not guild:
            logger.error(f"Guild {ticket.guild_id} not found")
            return
        
        channel = guild.get_channel(ticket.channel_id)
        if not channel:
            await user.send("❌ Your ticket channel no longer exists. Please create a new ticket.")
            await self.ticket_service.close_ticket(ticket, None)
            return
        
        embed = create_reply_embed(user, message.content, is_staff=False)
        await channel.send(embed=embed)
        await self.ticket_service.update_activity(ticket.ticket_id)
        await self.log_service.log_user_reply(ticket.guild_id, ticket, user, message.content)
        logger.info(f"User reply from {user} in ticket {ticket.ticket_id}")

    async def handle_staff_reply(self, message: discord.Message):
        ticket = await self.ticket_service.get_ticket_by_channel(message.channel.id)
        if not ticket:
            return
        
        config_service = GuildConfigService(self.bot.db)
        config = await config_service.get_config(message.guild.id)
        member = message.guild.get_member(message.author.id)
        if not member:
            return
        if not await is_staff(member, config):
            await message.delete()
            await message.author.send("You cannot reply in this ticket channel. Staff only.")
            return
        
        user = self.bot.get_user(ticket.user_id)
        if not user:
            try:
                user = await self.bot.fetch_user(ticket.user_id)
            except:
                await message.channel.send("❌ Could not find the user to relay the message.")
                return
        
        embed = create_reply_embed(message.author, message.content, is_staff=True)
        try:
            await user.send(embed=embed)
        except discord.Forbidden:
            await message.channel.send("⚠️ Could not DM the user. They may have DMs disabled or blocked the bot.")
        
        await self.ticket_service.update_activity(ticket.ticket_id)
        await self.log_service.log_staff_reply(ticket.guild_id, ticket, message.author, message.content)
        logger.info(f"Staff reply from {message.author} in ticket {ticket.ticket_id}")

    async def _check_staff_and_ticket(self, interaction: Interaction) -> bool:
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
