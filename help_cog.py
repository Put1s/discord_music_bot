import logging

import discord
from discord import app_commands
from discord.ext import commands
import typing


class help_cog(commands.Cog):
    def __init__(self, bot, **kwargs):
        self.bot = bot
        self.logger = kwargs['logger']

        self.help_message = '''
General commands:
```
$help($h)            — Displays all the available commands
$play($p) <keywords> — Finds the song on youtube and plays it in your current channel. Will resume playing the current song if it was paused
$queue($q)           — Displays the current music queue
$skip($s)            — Skips the current song being played
$clear($c)           — Stops the music and clears the queue
$leave($l)           — Disconnected the bot from the voice channel
$pause               — Pauses the current song being played or resumes if already paused
$resume($r)          — Resumes playing the current song
```'''
        self.text_channel_list = []

    # some debug info so that we know the bot has started
    @commands.Cog.listener()
    async def on_ready(self):
        # for guild in self.bot.guilds:
        #     for channel in guild.text_channels:
        #         self.text_channel_list.append(channel)
        #
        # await self.send_to_all(self.help_message)
        channel = self.bot.get_channel(1052140211951378455)
        await channel.send(self.help_message)
        self.logger.info("nice")

    @commands.hybrid_command(name='help', aliases=['h'], help='Displays all the available commands')
    async def help(self, ctx):
        await ctx.send(self.help_message, ephemeral=True)

    async def send_to_all(self, msg):
        for text_channel in self.text_channel_list:
            await text_channel.send(msg)
