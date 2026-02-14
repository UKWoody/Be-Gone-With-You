import discord
from discord.ext import commands
from config import TOKEN, GUILD_ID

# Import your Cogs
from cogs.purge import setup as purge_setup
from cogs.admin import setup as admin_setup
from cogs.events import setup as events_setup

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # ----------------------------
        # Load all Cogs
        # ----------------------------
        await purge_setup(self)
        await admin_setup(self)
        await events_setup(self)
        print("✅ All Cogs loaded")

        # ----------------------------
        # Force a guild sync for all slash commands
        # ----------------------------
        guild = discord.Object(id=GUILD_ID)
        await self.tree.sync(guild=guild)
        print("✅ Guild commands synced")

        # Print all registered commands for verification
        print("Registered guild commands:")
        for cmd in self.tree.get_commands(guild=guild):
            print(f"- {cmd.name}")


bot = MyBot()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


bot.run(TOKEN)
