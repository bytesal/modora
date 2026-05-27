import discord
from discord.ui import View, Button, Modal, TextInput
from services.ticket_service import TicketService

class RenameModal(Modal, title="Rename Ticket Channel"):
    new_name = TextInput(label="New Channel Name", placeholder="Enter a short name", required=True, max_length=50)
    
    def __init__(self, ticket_service: TicketService, channel: discord.TextChannel):
        super().__init__()
        self.ticket_service = ticket_service
        self.channel = channel
    
    async def on_submit(self, interaction: discord.Interaction):
        clean = self.new_name.value.lower().replace(" ", "-")
        try:
            await self.channel.edit(name=f"ticket-{clean}")
            await interaction.response.send_message(f"✅ Channel renamed to `{clean}`", ephemeral=True)
        except Exception:
            await interaction.response.send_message("❌ Failed to rename channel.", ephemeral=True)

class TicketControlView(View):
    """View with buttons for staff to manage a ticket."""
    def __init__(self, ticket_service: TicketService, user_id: int, guild_id: int):
        super().__init__(timeout=None)  # Persistent
        self.ticket_service = ticket_service
        self.user_id = user_id
        self.guild_id = guild_id
    
    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket:close")
    async def close_button(self, interaction: discord.Interaction, button: Button):
        if not await self._is_staff(interaction):
            return
        await interaction.response.defer()
        ticket = await self.ticket_service.get_ticket_by_channel(interaction.channel_id)
        if not ticket:
            await interaction.followup.send("❌ Not a ticket channel.", ephemeral=True)
            return
        await interaction.followup.send("🔒 Closing ticket in 5 seconds...")
        await self.ticket_service.close_ticket(ticket, interaction.user.id)
        await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.timedelta(seconds=5))
        await interaction.channel.delete()
    
    @discord.ui.button(label="Claim", style=discord.ButtonStyle.success, emoji="✅", custom_id="ticket:claim")
    async def claim_button(self, interaction: discord.Interaction, button: Button):
        if not await self._is_staff(interaction):
            return
        ticket = await self.ticket_service.get_ticket_by_channel(interaction.channel_id)
        if not ticket:
            await interaction.response.send_message("❌ Not a ticket channel.", ephemeral=True)
            return
        if ticket.staff_id:
            await interaction.response.send_message(f"❌ Already claimed by <@{ticket.staff_id}>", ephemeral=True)
            return
        await self.ticket_service.claim_ticket(ticket.ticket_id, interaction.user.id)
        await interaction.response.send_message(f"✅ You claimed this ticket.", ephemeral=False)
    
    @discord.ui.button(label="Rename", style=discord.ButtonStyle.secondary, emoji="✏️", custom_id="ticket:rename")
    async def rename_button(self, interaction: discord.Interaction, button: Button):
        if not await self._is_staff(interaction):
            return
        modal = RenameModal(self.ticket_service, interaction.channel)
        await interaction.response.send_modal(modal)
    
    async def _is_staff(self, interaction: discord.Interaction) -> bool:
        from services.guild_config_service import GuildConfigService
        from utils.permissions import is_staff as check_staff
        
        if not interaction.guild:
            await interaction.response.send_message("Not in a guild.", ephemeral=True)
            return False
        config_service = GuildConfigService(interaction.client.db)
        config = await config_service.get_config(interaction.guild.id)
        if not await check_staff(interaction.user, config):
            await interaction.response.send_message("❌ You need staff permissions.", ephemeral=True)
            return False
        return True
