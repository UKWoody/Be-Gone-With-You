from discord.ext import commands

class Events(commands.Cog):
    def __init__(self, bot, purge_cog):
        self.bot = bot
        self.purge_cog = purge_cog

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild_id = member.guild.id
        if guild_id in self.purge_cog.active_purges:
            task = self.purge_cog.active_purges[guild_id]
            if not task.done():
                log_channel = self.purge_cog.get_log_channel(member.guild)
                if log_channel:
                    await log_channel.send(f"⚠️ Auto purge skipped for {member} because a purge is already running.")
                return
        self.purge_cog.start_purge(member.guild, member.id)


# ----------------------------
# Manual Setup Function
# ----------------------------
async def setup(bot: commands.Bot):
    purge_cog = bot.get_cog("Purge")
    if purge_cog is None:
        raise RuntimeError("Purge cog must be loaded before Events cog")

    cog = Events(bot, purge_cog)
    await bot.add_cog(cog)

    print("✅ Events Cog loaded")
