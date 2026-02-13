import asyncio

guild_locks = {}

def get_lock(guild_id):
    if guild_id not in guild_locks:
        guild_locks[guild_id] = asyncio.Lock()
    return guild_locks[guild_id]
