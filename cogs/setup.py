import discord
from discord.ext import commands
from discord import app_commands, Interaction, TextStyle
from discord.ui import Modal, TextInput
from typing import Optional
from services.guild_config_service import GuildConfigService
from utils.permissions import is_admin
from utils.logger import get_logger
from views.ticket_panel import TicketPanelView

logger = get_logger(__name__)

class CategoryModal(Modal, title="Set Ticket Category"):
    category_id = TextInput(
        label="Category ID",
        placeholder="Enter the category ID where ticket channels will be created",
        required=True,
        style=TextStyle.short
    )
    
    async def on_submit(self, interaction: Interaction):
        try:
            category_id = int(self.category_id.value)
            await interaction.response.defer(ephemeral=True)
            service = GuildConfigService(interaction.client.db)
            await service.set_category(interaction.guild_id, category_id)
            embed = discord.Embed(
                title="✅ Category Set",
                description=f"Ticket category has been set to <#{category_id}>",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(f"Guild {interaction.guild_id} set category to {category_id}")
        except ValueError:
            await interaction.response.send_message("❌ Invalid category ID. Please enter a numeric ID.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error setting category: {e}")
            await interaction.followup.send("❌ An error occurred while setting the category.", ephemeral=True)

class StaffRoleModal(Modal, title="Manage Staff Roles"):
    action = TextInput(
        label="Action",
        placeholder="add or remove",
        required=True,
        style=TextStyle.short
    )
    role_id = TextInput(
        label="Role ID",
        placeholder="Enter the role ID",
        required=True,
        style=TextStyle.short
    )
    
    async def on_submit(self, interaction: Interaction):
        action = self.action.value.lower()
        try:
            role_id = int(self.role_id.value)
            await interaction.response.defer(ephemeral=True)
            service = GuildConfigService(interaction.client.db)
            
            if action == "add":
                await service.add_staff_role(interaction.guild_id, role_id)
                embed = discord.Embed(
                    title="✅ Staff Role Added",
                    description=f"<@&{role_id}> has been added as a staff role.",
                    color=discord.Color.green()
                )
            elif action == "remove":
                await service.remove_staff_role(interaction.guild_id, role_id)
                embed = discord.Embed(
                    title="✅ Staff Role Removed",
                    description=f"<@&{role_id}> has been removed from staff roles.",
                    color=discord.Color.green()
                )
            else:
                await interaction.followup.send("❌ Action must be `add` or `remove`.", ephemeral=True)
                return
            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(f"Guild {interaction.guild_id} {action} staff role {role_id}")
        except ValueError:
            await interaction.response.send_message("❌ Invalid role ID. Please enter a numeric ID.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error managing staff role: {e}")
            await interaction.followup.send("❌ An error occurred.", ephemeral=True)

class ChannelModal(Modal):
    def __init__(self, title: str, setting_name: str):
        super().__init__(title=title)
        self.setting_name = setting_name
        self.channel_id_input = TextInput(
            label="Channel ID",
            placeholder="Enter the channel ID",
            required=True,
            style=TextStyle.short
        )
        self.add_item(self.channel_id_input)
    
    async def on_submit(self, interaction: Interaction):
        try:
            channel_id = int(self.channel_id_input.value)
            await interaction.response.defer(ephemeral=True)
            service = GuildConfigService(interaction.client.db)
            
            if self.setting_name == "logs":
                await service.set_logs_channel(interaction.guild_id, channel_id)
                desc = f"Logs channel set to <#{channel_id}>"
            elif self.setting_name == "transcripts":
                await service.set_transcripts_channel(interaction.guild_id, channel_id)
                desc = f"Transcripts channel set to <#{channel_id}>"
            else:
                await interaction.followup.send("❌ Unknown setting.", ephemeral=True)
                return
            
            embed = discord.Embed(title="✅ Channel Set", description=desc, color=discord.Color.green())
            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(f"Guild {interaction.guild_id} set {self.setting_name} to {channel_id}")
        except ValueError:
            await interaction.response.send_message("❌ Invalid channel ID. Please enter a numeric ID.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error setting {self.setting_name}: {e}")
            await interaction.followup.send("❌ An error occurred.", ephemeral=True)

class PanelChannelModal(Modal, title="Set Panel Channel"):
    channel_id = TextInput(
        label="Channel ID",
        placeholder="Enter the channel ID where the ticket panel should be placed",
        required=True,
        style=TextStyle.short
    )
    
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
    
    async def on_submit(self, interaction: Interaction):
        try:
            channel_id = int(self.channel_id.value)
            await interaction.response.defer(ephemeral=True)
            service = GuildConfigService(interaction.client.db)
            await service.set_panel_channel(interaction.guild_id, channel_id)
            
            cog = interaction.client.get_cog("SetupCog")
            success = await cog.deploy_panel(interaction, channel_id)
            if success:
                embed = discord.Embed(
                    title="✅ Panel Deployed",
                    description=f"Ticket panel has been created in <#{channel_id}>",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="⚠️ Partial Setup",
                    description=f"Panel channel set but failed to send message. Please check permissions (bot needs Send Messages and Embed Links).",
                    color=discord.Color.orange()
                )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Invalid channel ID.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in panel setup: {e}")
            await interaction.followup.send("❌ An error occurred.", ephemeral=True)

class SetupCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Create the group
    setup = app_commands.Group(name="setup", description="Configure the ModMail bot for this server", default_permissions=discord.Permissions(administrator=True))

    @setup.command(name="category", description="Set the category where ticket channels will be created")
    async def setup_category(self, interaction: Interaction):
        if not await is_admin(interaction):
            await interaction.response.send_message("❌ You need administrator permissions.", ephemeral=True)
            return
        await interaction.response.send_modal(CategoryModal())

    @setup.command(name="staffrole", description="Add or remove staff roles")
    async def setup_staffrole(self, interaction: Interaction):
        if not await is_admin(interaction):
            await interaction.response.send_message("❌ You need administrator permissions.", ephemeral=True)
            return
        await interaction.response.send_modal(StaffRoleModal())

    @setup.command(name="logs", description="Set the logs channel for ticket activity")
    async def setup_logs(self, interaction: Interaction):
        if not await is_admin(interaction):
            await interaction.response.send_message("❌ You need administrator permissions.", ephemeral=True)
            return
        await interaction.response.send_modal(ChannelModal("Set Logs Channel", "logs"))

    @setup.command(name="transcripts", description="Set the transcripts channel")
    async def setup_transcripts(self, interaction: Interaction):
        if not await is_admin(interaction):
            await interaction.response.send_message("❌ You need administrator permissions.", ephemeral=True)
            return
        await interaction.response.send_modal(ChannelModal("Set Transcripts Channel", "transcripts"))

    @setup.command(name="panel", description="Set the panel channel and deploy the ticket opening message")
    async def setup_panel(self, interaction: Interaction):
        if not await is_admin(interaction):
            await interaction.response.send_message("❌ You need administrator permissions.", ephemeral=True)
            return
        modal = PanelChannelModal(self.bot)
        await interaction.response.send_modal(modal)

    @setup.command(name="cooldown", description="Set cooldown seconds between ticket creation (0 to disable)")
    async def setup_cooldown(self, interaction: Interaction, seconds: int):
        if not await is_admin(interaction):
            await interaction.response.send_message("❌ You need administrator permissions.", ephemeral=True)
            return
        if seconds < 0:
            await interaction.response.send_message("❌ Cooldown cannot be negative.", ephemeral=True)
            return
        service = GuildConfigService(self.bot.db)
        await service.update_config(interaction.guild_id, {"cooldown_seconds": seconds})
        embed = discord.Embed(
            title="✅ Cooldown Set",
            description=f"Ticket creation cooldown is now {seconds} seconds.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @setup.command(name="autoclose", description="Set auto-close timeout in minutes (0 to disable)")
    async def setup_autoclose(self, interaction: Interaction, minutes: int):
        if not await is_admin(interaction):
            await interaction.response.send_message("❌ You need administrator permissions.", ephemeral=True)
            return
        if minutes < 0:
            await interaction.response.send_message("❌ Minutes cannot be negative.", ephemeral=True)
            return
        service = GuildConfigService(self.bot.db)
        await service.update_config(interaction.guild_id, {"auto_close_minutes": minutes})
        embed = discord.Embed(
            title="✅ Auto-Close Set",
            description=f"Tickets will be closed after {minutes} minutes of inactivity." if minutes > 0 else "Auto-close disabled.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @setup.command(name="show", description="Show current configuration for this server")
    async def setup_show(self, interaction: Interaction):
        if not await is_admin(interaction):
            await interaction.response.send_message("❌ You need administrator permissions.", ephemeral=True)
            return
        service = GuildConfigService(self.bot.db)
        config = await service.get_config(interaction.guild_id)
        
        embed = discord.Embed(title="ModMail Configuration", color=discord.Color.blue())
        embed.add_field(name="Category", value=f"<#{config.category_id}>" if config.category_id else "Not set", inline=False)
        staff_roles = ", ".join(f"<@&{rid}>" for rid in config.staff_role_ids) if config.staff_role_ids else "None"
        embed.add_field(name="Staff Roles", value=staff_roles, inline=False)
        embed.add_field(name="Logs Channel", value=f"<#{config.logs_channel_id}>" if config.logs_channel_id else "Not set", inline=False)
        embed.add_field(name="Transcripts Channel", value=f"<#{config.transcripts_channel_id}>" if config.transcripts_channel_id else "Not set", inline=False)
        embed.add_field(name="Panel Channel", value=f"<#{config.panel_channel_id}>" if config.panel_channel_id else "Not set", inline=False)
        embed.add_field(name="Auto-close (minutes)", value=str(config.auto_close_minutes), inline=True)
        embed.add_field(name="Cooldown (seconds)", value=str(config.cooldown_seconds), inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @setup.command(name="reset", description="Reset all configuration for this server")
    async def setup_reset(self, interaction: Interaction):
        if not await is_admin(interaction):
            await interaction.response.send_message("❌ You need administrator permissions.", ephemeral=True)
            return
        service = GuildConfigService(self.bot.db)
        await service.reset_config(interaction.guild_id)
        embed = discord.Embed(
            title="🔄 Configuration Reset",
            description="All settings have been reset. Use `/setup` again to reconfigure.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info(f"Guild {interaction.guild_id} reset configuration")

    async def deploy_panel(self, interaction: Interaction, channel_id: int) -> bool:
        channel = interaction.guild.get_channel(channel_id)
        if not channel:
            return False
        
        embed = discord.Embed(
            title="ModMail Support",
            description="Click the button below to open a ticket. A private channel will be created for you to communicate with staff.",
            color=discord.Color.blue()
        )
        view = TicketPanelView(self.bot)
        
        try:
            message = await channel.send(embed=embed, view=view)
            service = GuildConfigService(self.bot.db)
            await service.set_panel_message(interaction.guild_id, message.id)
            return True
        except Exception as e:
            logger.error(f"Failed to deploy panel: {e}")
            return False

async def setup(bot: commands.Bot):
    cog = SetupCog(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(cog.setup)
