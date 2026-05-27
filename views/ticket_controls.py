import discord
from discord.ui import View, Button, Modal, TextInput
from services.ticket_service import TicketService
from services.transcript_service import TranscriptService

class ConfirmCloseModal(Modal, title="Confirm Close Ticket"):
    reason = TextInput(
        label="Reason (optional)",
        placeholder="Why is this ticket being closed?",
        required=False,
        style=discord.TextStyle.paragraph,
        max_length=500
    )
    
    def __init__(self, ticket_service: TicketService, transcript_service: TranscriptService, channel: discord.TextChannel, user_id: int, guild_id: int):
        super().__init__()
        self.ticket_service = ticket_service
        self.transcript_service = transcript_service
        self.channel = channel
        self.user_id = user_id
        self.guild_id = guild_id
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        ticket = await self.ticket_service.get_ticket_by_channel(self.channel.id)
        if not ticket:
            await interaction.followup.send("❌ Ticket not found.", ephemeral=True)
            return
        
        # Generate transcript before closing
        transcript_path = await self.transcript_service.generate_transcript(self.channel, ticket)
        transcript_url = await self.transcript_service.send_transcript(self.guild_id, ticket, self.channel, transcript_path)
        
        # Close ticket
        await self.ticket_service.close_ticket(ticket, interaction.user.id)
        
        # Send log (optional: include reason)
        reason_text = f"\n**Reason:** {self.reason.value}" if self.reason.value else ""
        await interaction.followup.send(f"🔒 Ticket closed.{reason_text}", ephemeral=False)
        
        # Delete channel after delay
        await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.timedelta(seconds=5))
        await self.channel.delete()

class AddUserModal(Modal, title="Add User to Ticket"):
    user_id = TextInput(
        label="User ID",
        placeholder="Enter the Discord user ID to add",
        required=True,
        style=discord.TextStyle.short
    )
    
    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        self.channel = channel
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.user_id.value)
            user = await interaction.client.fetch_user(user_id)
            await self.channel.set_permissions(user, read_messages=True, send_messages=True, attach_files=True, embed_links=True)
            await interaction.response.send_message(f"✅ Added {user.mention} to this ticket.", ephemeral=False)
        except ValueError:
            await interaction.response.send_message("❌ Invalid user ID.", ephemeral=True)
        except discord.NotFound:
            await interaction.response.send_message("❌ User not found.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to add user: {e}", ephemeral=True)

class RemoveUserModal(Modal, title="Remove User from Ticket"):
    user_id = TextInput(
        label="User ID",
        placeholder="Enter the Discord user ID to remove",
        required=True,
        style=discord.TextStyle.short
    )
    
    def __init__(self, channel: discord.TextChannel, original_user_id: int):
        super().__init__()
        self.channel = channel
        self.original_user_id = original_user_id
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.user_id.value)
            if user_id == self.original_user_id:
                await interaction.response.send_message("❌ Cannot remove the original ticket owner.", ephemeral=True)
                return
            user = await interaction.client.fetch_user(user_id)
            await self.channel.set_permissions(user, read_messages=False, send_messages=False)
            await interaction.response.send_message(f"✅ Removed {user.mention} from this ticket.", ephemeral=False)
        except ValueError:
            await interaction.response.send_message("❌ Invalid user ID.", ephemeral=True)
        except discord.NotFound:
            await interaction.response.send_message("❌ User not found.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to remove user: {e}", ephemeral=True)

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
        # Show confirmation modal
        transcript_service = TranscriptService(interaction.client)
        modal = ConfirmCloseModal(self.ticket_service, transcript_service, interaction.channel, self.user_id, self.guild_id)
        await interaction.response.send_modal(modal)
    
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
        # Show modal for rename (simple text input)
        modal = discord.ui.Modal(title="Rename Ticket Channel")
        name_input = discord.ui.TextInput(label="New Channel Name", placeholder="Enter a short name", required=True, max_length=50)
        modal.add_item(name_input)
        
        async def on_submit(modal_interaction):
            new_name = name_input.value.lower().replace(" ", "-")[:100]
            try:
                await interaction.channel.edit(name=f"ticket-{new_name}")
                await modal_interaction.response.send_message(f"✅ Renamed to `{new_name}`", ephemeral=False)
            except:
                await modal_interaction.response.send_message("❌ Failed to rename.", ephemeral=True)
        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Transcript", style=discord.ButtonStyle.primary, emoji="📄", custom_id="ticket:transcript")
    async def transcript_button(self, interaction: discord.Interaction, button: Button):
        if not await self._is_staff(interaction):
            return
        await interaction.response.defer(ephemeral=True)
        ticket = await self.ticket_service.get_ticket_by_channel(interaction.channel_id)
        if not ticket:
            await interaction.followup.send("❌ Ticket not found.", ephemeral=True)
            return
        
        transcript_service = TranscriptService(interaction.client)
        filepath = await transcript_service.generate_transcript(interaction.channel, ticket)
        url = await transcript_service.send_transcript(self.guild_id, ticket, interaction.channel, filepath)
        if url:
            await interaction.followup.send(f"✅ Transcript generated: {url}", ephemeral=True)
        else:
            await interaction.followup.send("❌ Failed to send transcript. Check transcripts channel configuration.", ephemeral=True)
    
    @discord.ui.button(label="Add User", style=discord.ButtonStyle.secondary, emoji="➕", custom_id="ticket:adduser")
    async def adduser_button(self, interaction: discord.Interaction, button: Button):
        if not await self._is_staff(interaction):
            return
        modal = AddUserModal(interaction.channel)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Remove User", style=discord.ButtonStyle.secondary, emoji="➖", custom_id="ticket:removeuser")
    async def removeuser_button(self, interaction: discord.Interaction, button: Button):
        if not await self._is_staff(interaction):
            return
        modal = RemoveUserModal(interaction.channel, self.user_id)
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
