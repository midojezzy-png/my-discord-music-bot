From __future__ import annotations

import re
import asyncio
import os
from discord import Embed, Intents, Activity, Status, ActivityType
from discord import FFmpegOpusAudio, Message, utils
from discord.ext import commands
from yt_dlp import YoutubeDL
from youtubesearchpython import VideosSearch
 
from discord import VoiceClient, Member, VoiceState
from typing import Union, Optional

bot = commands.Bot(command_prefix='!', 
                   intents=Intents.all(), 
                   activity=Activity(type=ActivityType.listening, 
                                     name="Music Bot."),
                   status=Status.idle,
                   help_command=None)

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

def is_youtube_link(message_content):
    pattern = [r'https?://(?:www\.)?youtu\.be/([^/?]+)',r'https?://(?:www\.)?youtube\.com/watch\?v=([^&]+)']
    for valid_url in pattern:
        if re.match(valid_url,message_content):
            return True
    return False

def get_duration(time):
    if time is None:
        return "LIVE STREAM"
    hours,minutes,seconds = int(f"{time // 3600:02}"),int(f"{(time % 3600) // 60:02}"),int(f"{time % 60:02}")
    return f"{hours if hours > 0 else ''}{':' if hours > 0 else ''}{minutes:02d}:{seconds:02d}"

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None
        self.isloop = False
        self.skip = False
        self.data = {}

    def get_data(self, url, ctx):
        ytdl = YoutubeDL(ytdl_format_options)
        ytdl_info = ytdl.extract_info(url, download=False)
        return {
            'user': ctx.author,
            'title': ytdl_info.get('title', 'Unknown'),
            'url': ytdl_info.get('url'),
            'duration': ytdl_info.get('duration'),
            'thumbnail': ytdl_info.get('thumbnail')
        }
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Connected To {self.bot.user.name}")

    @commands.command(name='play', aliases=['p', 'ش'])
    async def play_command(self, ctx: commands.Context, *, message: Optional[str]):
        if ctx.author.voice is None:
            await ctx.reply("**:x: You Need To Be In A voice Channel To use This Command**")
            return
        if message is None:
            await ctx.reply(f"**{self.bot.command_prefix}play `<song name || URL>`**")
            return
        
        if not self.voice_client or not self.voice_client.is_connected():
            self.voice_client = await ctx.author.voice.channel.connect(self_deaf=True)
        elif self.voice_client.is_playing() or self.voice_client.is_paused():
            await ctx.reply("**:x: Music Bot Are Currently In Use.**")
            return
        elif self.voice_client.channel != ctx.author.voice.channel:
            await self.voice_client.move_to(ctx.author.voice.channel)
            
        async with ctx.typing():
            # دابا كيقبل ساوند كلاود ديركت
            if "soundcloud.com" in message.lower():
                url = message
            elif is_youtube_link(message):
                url = message
            else:
                try:
                    search_result = VideosSearch(message, limit=1).result()['result']
                    url = search_result[0]['link']
                except:
                    await ctx.reply(f"**:x: I Couldn't Find A Song**")
                    return
        
        self.data = self.get_data(url=url, ctx=ctx)
        
        if not self.data.get('url'):
            await ctx.reply("**:x: Cannot Fetch This Song**")
            return
        
        embed = Embed(description=f"**:arrow_forward: [{self.data['title']}]({url})**", color=0x000000)
        await ctx.send(embed=embed)

        while True:
            self.voice_client.play(FFmpegOpusAudio(self.data['url']))
            while self.voice_client.is_playing() or self.voice_client.is_paused():
                await asyncio.sleep(0.1)
                if self.skip:
                    self.voice_client.stop()
                    self.skip = False
            if self.isloop:
                continue
            self.data = {}
            return

    @commands.command(name='stop')
    async def stop_command(self, ctx):
        if self.voice_client:
            await self.voice_client.disconnect()
            self.voice_client = None
            await ctx.reply("**:wave: Bye**")

async def setup(bot):
    await bot.add_cog(Music(bot))

bot.setup_hook = lambda: asyncio.create_task(setup(bot))
bot.run(os.getenv('DISCORD_TOKEN'))
