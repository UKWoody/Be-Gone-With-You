import discord
from discord import app_commands
from discord.ext import commands
from collections import defaultdict
import asyncio
import time
import json

from utils.helpers import format_eta, get_progress_bar
from utils.locks import get_lock
from config import SETTINGS_FILE, GUILD_ID


class Purge(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_purges = {}
        self.settings = self.load_settings()
        print("✅ Purge Cog loaded")

    # ----------------------------
    # Settings
    # ----------------------------
    def load_settings(self):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"guilds": {}}

    def save_settings(self):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f, indent=4)

    def get_log_channel(self, guild: discord.Guild):
        guild_data = self.settings.get("guilds", {}).get(str(guild.id), {})
        log_id = guild_data.get("log_channel_id")
        if log_id:
            return guild.get_channel(log_id)
        return None

    # ----------------------------
    # Slash Command
    # ----------------------------
    @app_commands.command(
        name="purgeuser",
        description="Purge all messages from a specific user"
    )
    @app_commands.describe(user="The user whose messages will be purged")
    async def purgeuser(self, interaction: discord.Interaction, user: discord.Member):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True
            )
            return

        if interaction.guild.id in self.active_purges:
            await interaction.response.send_message(
                "⚠️ A purge is already running in this server.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"🧹 Starting purge for {user.mention}...",
            ephemeral=True
        )

        self.start_purge(interaction.guild, user.id, initiated_by=interaction.user.name)

    # ----------------------------
    # Message Collection
    # ----------------------------
    async def collect_user_messages(self, guild: discord.Guild, user_id: int):
        messages = []

        async def scan_channel(channel):
            try:
                async for message in channel.history(limit=None, oldest_first=True):
                    if message.author.id == user_id:
                        messages.append(message)
            except Exception:
                pass

        for channel in guild.text_channels:
            await scan_channel(channel)
            for thread in channel.threads:
                await scan_channel(thread)
            async for thread in channel.archived_threads(limit=None):
                await scan_channel(thread)
            async for thread in channel.archived_threads(limit=None, private=True):
                await scan_channel(thread)

        return messages

    # ----------------------------
    # Purge Task
    # ----------------------------
    async def purge_task(self, guild: discord.Guild, user_id: int, initiated_by=None):
        lock = get_lock(guild.id)

        if lock.locked():
            log_channel = self.get_log_channel(guild)
            if log_channel:
                await log_channel.send(
                    f"⚠️ Purge request denied for User ID {user_id} — another purge is running."
                )
            return

        async with lock:
            log_channel = self.get_log_channel(guild)
            messages = await self.collect_user_messages(guild, user_id)
            total = len(messages)

            if total == 0:
                if log_channel:
                    await log_channel.send(f"No messages found for user ID {user_id}.")
                self.active_purges.pop(guild.id, None)
                return

            deleted = 0
            start_time = time.time()
            channel_counts = defaultdict(int)

            task = asyncio.current_task()
            task.progress_info = {"deleted": 0, "total": total, "start_time": start_time}

            if log_channel:
                progress_message = await log_channel.send(
                    f"🧹 Starting purge for User ID {user_id}\nTotal messages: {total}"
                )
            else:
                progress_message = None

            try:
                for message in messages:
                    try:
                        await message.delete()
                        channel_counts[str(message.channel)] += 1
                    except Exception:
                        pass

                    deleted += 1
                    remaining = total - deleted
                    elapsed = time.time() - start_time
                    avg_time = elapsed / deleted if deleted > 0 else 0
                    eta_seconds = avg_time * remaining if deleted > 0 else 0
                    percent = (deleted / total) * 100
                    bar = get_progress_bar(percent)

                    task.progress_info["deleted"] = deleted

                    if progress_message and (deleted % 5 == 0 or deleted == total):
                        await progress_message.edit(
                            content=(
                                f"🧹 Purging User ID {user_id}\n"
                                f"{bar}\n"
                                f"Deleted: {deleted} | Remaining: {remaining}\n"
                                f"ETA: {format_eta(eta_seconds)}"
                            )
                        )

                    await asyncio.sleep(0.4)

            except asyncio.CancelledError:
                if log_channel:
                    await log_channel.send(f"❌ Purge cancelled for User ID {user_id}.")
                raise

            finally:
                self.active_purges.pop(guild.id, None)

            if log_channel:
                breakdown = "\n".join(f"{channel}: {count}" for channel, count in channel_counts.items())
                await log_channel.send(
                    f"✅ Purge Complete\n"
                    f"User ID: {user_id}\n"
                    f"Deleted: {deleted}\n"
                    f"Initiated by: {initiated_by if initiated_by else 'Auto (Member Left)'}\n\n"
                    f"📊 Channel Breakdown:\n{breakdown}"
                )

    # ----------------------------
    # Task Management
    # ----------------------------
    def start_purge(self, guild: discord.Guild, user_id: int, initiated_by=None):
        task = self.bot.loop.create_task(self.purge_task(guild, user_id, initiated_by))
        self.active_purges[guild.id] = task
        return task


# ----------------------------
# Explicit setup function (for Python 3.13)
# ----------------------------
async def setup(bot: commands.Bot):
    cog = Purge(bot)
    await bot.add_cog(cog)

    # Explicitly add the command to bot.tree for Python 3.13
    bot.tree.add_command(cog.purgeuser, guild=discord.Object(id=GUILD_ID))
    print("✅ /purgeuser explicitly added to bot tree")
