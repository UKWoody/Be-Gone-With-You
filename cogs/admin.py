import discord
from discord.ext import commands
from config import GUILD_ID, BOT_VERSION
from utils.helpers import get_progress_bar, format_eta
import time
from discord import app_commands

class Admin(commands.Cog):
    def __init__(self, bot, purge_cog):
        self.bot = bot
        self.purge_cog = purge_cog

    # ---------------- HELP ----------------
    async def help_command(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Admin only.", ephemeral=True)
            return

        embed = discord.Embed(
            title="⚔️ Be-Gone-With-You – Help & Commands ⚔️",
            description=f"**Version:** {BOT_VERSION}",
            color=discord.Color.dark_red()
        )

        embed.add_field(name="/purgeuser user_id:<ID>", value="Deletes all messages from a user with live progress, ETA, channel breakdown.", inline=False)
        embed.add_field(name="/status", value="Shows live progress of an ongoing purge.", inline=False)
        embed.add_field(name="/cancelpurge", value="Cancels the ongoing purge safely.", inline=False)
        embed.add_field(name="/setup", value="Check permissions and select log channel.", inline=False)
        embed.add_field(name="Auto purge on leave", value="Automatically purges when a member leaves the server.", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ---------------- STATUS ----------------
    async def status_command(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id not in self.purge_cog.active_purges:
            await interaction.response.send_message("✅ No purge running.", ephemeral=True)
            return

        task = self.purge_cog.active_purges[guild_id]
        if task.done():
            await interaction.response.send_message("✅ No purge running.", ephemeral=True)
            return

        info = getattr(task, "progress_info", None)
        if info:
            deleted = info.get("deleted", 0)
            total = info.get("total", 0)
            start_time = info.get("start_time", time.time())
            remaining = total - deleted
            elapsed = time.time() - start_time
            avg_time = elapsed / deleted if deleted > 0 else 0
            eta_seconds = avg_time * remaining if deleted > 0 else 0
            percent = (deleted / total * 100) if total > 0 else 0
            bar = get_progress_bar(percent)
            message = f"🧹 Purge Status\n{bar}\nDeleted: {deleted} | Remaining: {remaining}\nETA: {format_eta(eta_seconds)}"
        else:
            message = "⚠️ Unable to retrieve live progress at this moment."

        await interaction.response.send_message(message, ephemeral=True)

    # ---------------- CANCEL PURGE ----------------
    async def cancelpurge_command(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id not in self.purge_cog.active_purges:
            await interaction.response.send_message("❌ No purge running.", ephemeral=True)
            return

        task = self.purge_cog.active_purges[guild_id]
        if not task.done():
            task.cancel()
            await interaction.response.send_message("🛑 Purge cancelled.", ephemeral=True)
            return

        await interaction.response.send_message("❌ No purge running.", ephemeral=True)

    # ---------------- SETUP ----------------
    async def setup_command(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Admin only.", ephemeral=True)
            return

        bot_member = interaction.guild.me
        required_perms = {
            "Manage Messages": bot_member.guild_permissions.manage_messages,
            "Read Message History": bot_member.guild_permissions.read_message_history,
            "Manage Threads": bot_member.guild_permissions.manage_threads,
            "View Channels": bot_member.guild_permissions.view_channel,
            "Send Messages": bot_member.guild_permissions.send_messages
        }

        missing = [perm for perm, has in required_perms.items() if not has]
        if missing:
            await interaction.response.send_message(f"⚠️ Missing permissions: {', '.join(missing)}", ephemeral=True)
            return

        channels = [c for c in interaction.guild.text_channels if c.permissions_for(bot_member).send_messages]
        if not channels:
            await interaction.response.send_message("❌ No suitable text channels for logging.", ephemeral=True)
            return

        log_channel = channels[0]
        if str(interaction.guild.id) not in self.purge_cog.settings["guilds"]:
            self.purge_cog.settings["guilds"][str(interaction.guild.id)] = {}
        self.purge_cog.settings["guilds"][str(interaction.guild.id)]["log_channel_id"] = log_channel.id
        self.purge_cog.save_settings()

        await interaction.response.send_message(f"✅ Setup complete! Logs will be sent to {log_channel.mention}", ephemeral=True)


# ----------------------------
# Manual Setup Function
# ----------------------------
async def setup(bot: commands.Bot):
    purge_cog = bot.get_cog("Purge")
    if purge_cog is None:
        raise RuntimeError("Purge cog must be loaded before Admin cog")

    cog = Admin(bot, purge_cog)
    await bot.add_cog(cog)

    # Explicit manual registration
    bot.tree.add_command(app_commands.Command(name="help", description="Show bot command documentation", callback=cog.help_command),
                         guild=discord.Object(id=GUILD_ID))
    bot.tree.add_command(app_commands.Command(name="status", description="Check if a purge is running", callback=cog.status_command),
                         guild=discord.Object(id=GUILD_ID))
    bot.tree.add_command(app_commands.Command(name="cancelpurge", description="Cancel the ongoing purge", callback=cog.cancelpurge_command),
                         guild=discord.Object(id=GUILD_ID))
    bot.tree.add_command(app_commands.Command(name="setup", description="Check permissions and select log channel", callback=cog.setup_command),
                         guild=discord.Object(id=GUILD_ID))

    print("✅ Admin Cog loaded and commands registered")
