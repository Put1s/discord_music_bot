import logging
import logging.handlers

import discord
from discord import app_commands
from discord.ext import commands

from config import *

from help_cog import help_cog
from music_cog import music_cog

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
logging.getLogger('discord.http').setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
    filename='discord.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

intents = discord.Intents.all()

bot = commands.Bot(command_prefix='$', intents=intents, log_handler=handler)


@bot.event
async def on_ready():
    try:
        bot.remove_command('help')

        params = {"logger": logger, "admins": ADMINS, "only_admins": ONLY_ADMINS}

        await bot.add_cog(help_cog(bot, **params))
        await bot.add_cog(music_cog(bot, **params))

        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(e)

if __name__ == '__main__':
    bot.run(TOKEN, log_level=logging.INFO, log_formatter=formatter)
