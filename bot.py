import discord
from discord.ext import commands
from config import TOKEN, GUILD_ID
from cogs.purge import Purge
from cogs.admin import Admin
from cogs.events import Events

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Logged in as {bot.user}")

# Load cogs
purge_cog = Purge(bot)
bot.add_cog(purge_cog)
bot.add_cog(Admin(bot, purge_cog))
bot.add_cog(Events(bot, purge_cog))

bot.run(TOKEN)
