import discord
from discord.ext import commands
from discord import app_commands, Interaction, Modal, TextInput, TextStyle
from typing import Optional
from services.guild_config_service import GuildConfigService
from utils.permissions import is_admin
from utils.logger import get_logger

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
            elif self.setting_name == "panel":
                await service.set_panel_channel(interaction.guild_id, channel_id)
                desc = f"Panel channel set to <#{channel_id}>"
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

class SetupCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.group(name="setup", description="Configure the ModMail bot for this server")
    @app_commands.default_permissions(administrator=True)
    async def setup_group(self, interaction: Interaction):
        """Group command for setup – use subcommands."""
        if interaction.invoked_subcommand is None:
            embed = discord.Embed(
                title="Setup Commands",
                description=(
                    "Use `/setup category` – set the ticket category\n"
                    "/setup staffrole – add or remove staff roles\n"
                    "/setup logs – set logs channel\n"
                    "/setup transcripts – set transcripts channel\n"
                    "/setup panel – set panel channel and deploy message\n"
                    "/setup show – show current configuration\n"
                    "/setup reset – reset all settings"
                ),
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @setup_group.command(name="category", description="Set the category where ticket channels will be created")
    async def setup_category(self, interaction: Interaction):
        if not await is_admin(interaction):
            await interaction.response.send_message("❌ You need administrator permissions.", ephemeral=True)
            return
        await interaction.response.send_modal(CategoryModal())

    @setup_group.command(name="staffrole", description="Add or remove staff roles")
    async def setup_staffrole(self, interaction: Interaction):
        if not await is_admin(interaction):
            await interaction.response.send_message("❌ You need administrator permissions.", ephemeral=True)
            return
        await interaction.response.send_modal(StaffRoleModal())

    @setup_group.command(name="logs", description="Set the logs channel for ticket activity")
    async def setup_logs(self, interaction: Interaction):
        if not await is_admin(interaction):
            await interaction.response.send_message("❌ You need administrator permissions.", ephemeral=True)
            return
        await interaction.response.send_modal(ChannelModal("Set Logs Channel", "logs"))

    @setup_group.command(name="transcripts", description="Set the transcripts channel")
    async def setup_transcripts(self, interaction: Interaction):
        if not await is_admin(interaction):
            await interaction.response.send_message("❌ You need administrator permissions.", ephemeral=True)
            return
        await interaction.response.send_modal(ChannelModal("Set Transcripts Channel", "transcripts"))

    @setup_group.command(name="panel", description="Set the panel channel and deploy the ticket opening message")
    async def setup_panel(self, interaction: Interaction):
        if not await is_admin(interaction):
            await interaction.response.send_message("❌ You need administrator permissions.", ephemeral=True)
            return
        await interaction.response.send_modal(ChannelModal("Set Panel Channel", "panel"))

    @setup_group.command(name="show", description="Show current configuration for this server")
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

    @setup_group.command(name="reset", description="Reset all configuration for this server")
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

async def setup(bot: commands.Bot):
    await bot.add_cog(SetupCog(bot))
