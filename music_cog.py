import logging

import discord
from discord import app_commands
from discord.ext import commands
import typing

from yt_dlp import YoutubeDL


class music_cog(commands.Cog):
    def __init__(self, bot, **kwargs):
        self.bot = bot
        self.logger = kwargs['logger']
        self.admins = kwargs['admins']
        self.only_admins = kwargs['only_admins']

        self.is_playing = False
        self.is_paused = False

        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio', 'quiet': 'true', 'noplaylist': 'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                               'options': '-vn'}

        self.vc = None

    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info('ytsearch:%s' % item, download=False)['entries'][0]
            except Exception:
                return False

        return {'source': info['url'], 'title': info['fulltitle']}

    def play_next(self):
        if self.music_queue:
            self.is_playing = True

            # get the first url
            m_url = self.music_queue[0][0]['source']

            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False
            self.is_paused = False

    # infinite loop checking
    async def play(self):
        if self.music_queue:
            self.is_playing = False
            self.is_paused = False

            m_url = self.music_queue[0][0]['source']

            if self.vc is None or not self.vc.is_connected():
                self.vc = await self.music_queue[0][1].connect()

                if self.vc is None:
                    return False
            else:
                await self.vc.move_to(self.music_queue[0][1])

            self.music_queue.pop(0)

            self.is_playing = True
            self.is_paused = False
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False
            self.is_paused = False
        return True

    async def play_handler(self, user, query):
        if self.only_admins:
            if user.id not in self.admins:
                self.logger.info(f'{user} tried to add "{query}" to the queue')
                return 'Sorry, you are not allowed to do this'
        self.logger.info(f'{user} requested to add "{query}" to queue')
        if user.voice is None or user.voice.channel is None:
            self.logger.info(f'Is not in voice channel')
            return 'You should connect to the voice channel first'
        elif self.is_paused:
            self.is_paused = False
            self.is_playing = True
            self.vc.resume()
            self.logger.info(f'Playback resumed')
            return 'Playback resumed'
        else:
            song = self.search_yt(query)
            if isinstance(song, bool):
                return ('Could not download the song. '
                        'Incorrect format try another keyword. This could be due to playlist or a livestream format.')
            else:
                self.music_queue.append([song, user.voice.channel])

                if not self.is_playing:
                    await self.play()
                self.logger.info(f'''"{song['title']}" added to the queue''')
                return f'''_{song['title']}_ added to the queue'''

    @commands.command(name='play', aliases=['p', 'playing'], help='Plays a selected song from youtube')
    async def play_command(self, ctx, *, query='Never Gonna Give /You Up'):
        await ctx.send(await self.play_handler(ctx.author, query))

    # @app_commands.command(name="ping", description="Test slash command")
    # async def ping(self, interaction: discord.Interaction):
    #     await interaction.response.send_message("Pong!", ephemeral=True)

    @app_commands.command(name='play', description='Plays a selected song from youtube')
    async def play_command_slash(self, interaction: discord.Interaction,
                                 query: typing.Optional[str] = 'Never Gonna Give You Up'):
        await interaction.response.defer()
        await interaction.followup.send(await self.play_handler(interaction.user, query), ephemeral=True)

    @commands.hybrid_command(help='Pauses the current song being played or resumes if already paused')
    async def pause(self, ctx):
        if self.only_admins:
            if ctx.author.id not in self.admins:
                self.logger.info(f'{ctx.author} tried to pause')
                await ctx.send('Sorry, you are not allowed to do this')
                return
        self.logger.info(f'{ctx.author} requested to pause')
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()
            self.logger.info(f'Playback stopped')
            await ctx.send("Playback stopped", ephemeral=True)
        elif self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()
            self.logger.info(f'Playback resumed')
            await ctx.send("Playback resumed", ephemeral=True)
        else:
            self.logger.info(f'Queue is empty')
            await ctx.send("Queue is empty", ephemeral=True)

    @commands.hybrid_command(name='resume', aliases=['r'], help='Resumes playing with the discord bot')
    async def resume(self, ctx):
        if self.only_admins:
            if ctx.author.id not in self.admins:
                self.logger.info(f'{ctx.author} tried to resume')
                await ctx.send('Sorry, you are not allowed to do this', ephemeral=True)
                return
        self.logger.info(f'{ctx.author} requested to resume')
        if self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()
            self.logger.info(f'Playback resumed')
            await ctx.send("Playback resumed", ephemeral=True)
        elif self.is_playing:
            self.logger.info(f'Playback is already playing')
            await ctx.send('Playback is already playing', ephemeral=True)
        else:
            self.logger.info(f'Queue is empty')
            await ctx.send('Queue is empty', ephemeral=True)

    @commands.hybrid_command(name='skip', aliases=['s'], help='Skips the current song being played')
    async def skip(self, ctx):
        if self.only_admins:
            if ctx.author.id not in self.admins:
                self.logger.info(f'{ctx.author} tried to skip')
                await ctx.send('Sorry, you are not allowed to do this', ephemeral=True)
                return
        self.logger.info(f'{ctx.author} requested to skip')
        if self.vc:
            self.vc.stop()
            await self.play()
        self.logger.info(f'Song skipped')
        await ctx.send('Song skipped', ephemeral=True)

    @commands.hybrid_command(name='queue', aliases=['q'], help='Displays the current songs in queue')
    async def queue(self, ctx):
        self.logger.info(f"{ctx.author} checked the queue")
        max_queue_length = 10
        value = ''
        for i in range(min(max_queue_length, len(self.music_queue))):
            value += f'''{i + 1}. _{self.music_queue[i][0]['title']}_\n'''
        if len(self.music_queue) > max_queue_length:
            value += f'and {len(self.music_queue) - max_queue_length} more...'
        if value:
            await ctx.send(f'Queue:\n{value}', ephemeral=True)
        else:
            await ctx.send('Queue is empty', ephemeral=True)

    @commands.hybrid_command(name='clear', aliases=['c', 'bin'], help='Stops the music and clears the queue')
    async def clear(self, ctx):
        if self.only_admins:
            if ctx.author.id not in self.admins:
                self.logger.info(f'{ctx.author} tried to clear the queue', ephemeral=True)
                await ctx.send('Sorry, you are not allowed to do this', ephemeral=True)
                return
        self.logger.info(f"{ctx.author} cleared the queue")
        if self.vc is not None and self.is_playing:
            self.is_playing = False
            self.is_paused = False
            self.vc.stop()
        self.music_queue = list()
        await ctx.send('Music queue cleared', ephemeral=True)

    @commands.hybrid_command(name='leave', aliases=['disconnect', 'l', 'd'], help='Kick the bot from VC')
    async def dc(self, ctx):
        if self.only_admins:
            if ctx.author.id not in self.admins:
                self.logger.info(f'{ctx.author} tried to kick the bot from VC')
                await ctx.send('Sorry, you are not allowed to do this', ephemeral=True)
                return
        self.logger.info(f"{ctx.author} kicked the bot from VC")
        self.is_playing = False
        self.is_paused = False
        if self.vc is not None:
            await self.vc.disconnect()
        await ctx.send('Bot kicked from VC', ephemeral=True)
