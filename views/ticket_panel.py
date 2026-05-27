import discord
from discord.ui import View, Button
from services.ticket_service import TicketService
from services.guild_config_service import GuildConfigService

class TicketPanelView(View):
    """Persistent view with a button to open a ModMail ticket."""
    def __init__(self, bot):
        super().__init__(timeout=None)  # Persistent
        self.bot = bot

    @discord.ui.button(label="Open ModMail Ticket", style=discord.ButtonStyle.primary, emoji="✉️", custom_id="modmail:open_ticket")
    async def open_ticket_button(self, interaction: discord.Interaction, button: Button):
        """Button click handler – create a new ticket."""
        if not interaction.guild:
            await interaction.response.send_message("This button can only be used in a server.", ephemeral=True)
            return
        
        # Defer to avoid timeout
        await interaction.response.defer(ephemeral=True)
        
        ticket_service = TicketService(self.bot.db)
        config_service = GuildConfigService(self.bot.db)
        config = await config_service.get_config(interaction.guild_id)
        
        # Check if user already has open ticket
        existing = await ticket_service.get_open_ticket(interaction.user.id, interaction.guild_id)
        if existing:
            embed = discord.Embed(
                title="❌ Ticket Already Open",
                description=f"You already have an open ticket: <#{existing.channel_id}>\nPlease wait for it to be closed.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Create ticket channel
        channel = await ticket_service.create_ticket_channel(
            guild=interaction.guild,
            user=interaction.user,
            config=config
        )
        
        if not channel:
            await interaction.followup.send("❌ Failed to create ticket. Please contact server administrators.", ephemeral=True)
            return
        
        # Send initial embed with controls
        from utils.embeds import create_ticket_embed
        from views.ticket_controls import TicketControlView
        
        embed = create_ticket_embed(interaction.user, interaction.user.name)
        control_view = TicketControlView(ticket_service, interaction.user.id, interaction.guild.id)
        await channel.send(embed=embed, view=control_view)
        
        await interaction.followup.send(f"✅ Ticket created! Please go to {channel.mention}", ephemeral=True)
