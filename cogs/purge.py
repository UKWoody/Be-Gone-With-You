import discord
from discord.ext import commands
from collections import defaultdict
import asyncio, time
import json
from utils.helpers import format_eta, get_progress_bar
from utils.locks import get_lock
from config import SETTINGS_FILE

class Purge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_purges = {}  # guild_id: asyncio.Task
        self.settings = self.load_settings()

    def load_settings(self):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"guilds": {}}

    def save_settings(self):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f, indent=4)

    def get_log_channel(self, guild):
        guild_data = self.settings.get("guilds", {}).get(str(guild.id), {})
        log_id = guild_data.get("log_channel_id")
        if log_id:
            return guild.get_channel(log_id)
        return None

    async def collect_user_messages(self, guild, user_id):
        messages = []

        async def scan_channel(channel):
            try:
                async for message in channel.history(limit=None, oldest_first=True):
                    if message.author.id == user_id:
                        messages.append(message)
            except:
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

    async def purge_task(self, guild, user_id, initiated_by=None):
        lock = get_lock(guild.id)
        if lock.locked():
            log_channel = self.get_log_channel(guild)
            if log_channel:
                await log_channel.send(f"⚠️ Purge request denied for User ID {user_id} — another purge is running.")
            return

        async with lock:
            log_channel = self.get_log_channel(guild)
            messages = await self.collect_user_messages(guild, user_id)
            total = len(messages)
            if total == 0:
                if log_channel:
                    await log_channel.send(f"No messages found for user ID {user_id}.")
                return

            deleted = 0
            start_time = time.time()
            channel_counts = defaultdict(int)

            # Store task progress for live /status
            task = asyncio.current_task()
            task.progress_info = {"deleted": 0, "total": total, "start_time": start_time}

            if log_channel:
                progress_message = await log_channel.send(f"🧹 Starting purge for User ID {user_id}\nTotal messages: {total}")
            else:
                progress_message = None

            for message in messages:
                try:
                    await message.delete()
                    channel_counts[str(message.channel)] += 1
                except:
                    pass

                deleted += 1
                remaining = total - deleted
                elapsed = time.time() - start_time
                avg_time = elapsed / deleted if deleted > 0 else 0
                eta_seconds = avg_time * remaining if deleted > 0 else 0
                percent = (deleted / total) * 100
                bar = get_progress_bar(percent)

                task.progress_info["deleted"] = deleted  # update for /status

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

            # Final breakdown
            if log_channel:
                breakdown = "\n".join(f"{channel}: {count}" for channel, count in channel_counts.items())
                await log_channel.send(
                    f"✅ Purge Complete\n"
                    f"User ID: {user_id}\n"
                    f"Deleted: {deleted}\n"
                    f"Initiated by: {initiated_by if initiated_by else 'Auto (Member Left)'}\n\n"
                    f"📊 Channel Breakdown:\n{breakdown}"
                )

    def start_purge(self, guild, user_id, initiated_by=None):
        task = self.bot.loop.create_task(self.purge_task(guild, user_id, initiated_by))
        self.active_purges[guild.id] = task
        return task
