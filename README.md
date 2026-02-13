# Be-Gone-With-You

A Discord moderation bot to purge messages from members, with:

- Live progress bar + ETA
- Automatic purge on member leave
- Slash commands: /purgeuser, /status, /cancelpurge, /help, /setup
- Persistent settings per guild
- Version tracking

## Setup

1. Create a Discord application and bot via the [Developer Portal](https://discord.com/developers/applications)
2. Copy the bot token and paste it in `config.py`
3. Replace `GUILD_ID` in `config.py` with your server ID
4. Run `pip install -r requirements.txt`
5. Run `bot.py`
6. In your server, run `/setup` to select the logging channel
7. Use `/purgeuser` to purge a user, `/status` to check progress, and `/cancelpurge` to stop

Ensure the bot has the following permissions:

- Manage Messages
- Read Message History
- Manage Threads
- View Channels
- Send Messages
