import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio

from utils.config import settings
from utils.database import Database
from utils.logger_config import logger

load_dotenv()

PREFIX = "!"
TOKEN = settings.DISCORD_BOT_TOKEN

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)


@bot.event
async def on_ready():
    Database().create_all()
    print(f"Logged in as {bot.user}.")
    try:
        synced = await bot.tree.sync()
        print(f"Slash commands synced: {len(synced)} commands")
    except Exception as e:
        print(e)


async def main():
    await bot.load_extension("cogs.raids")
    await bot.load_extension("cogs.expedition")
    await bot.load_extension("cogs.utils")
    logger.info("Bot loaded successfully.")
    await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
