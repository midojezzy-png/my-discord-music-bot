from __future__ import annotations
import asyncio
import os
import discord
from discord.ext import commands
from yt_dlp import YoutubeDL

# إعدادات البوت
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

ytdl_format_options = {
    'format': 'bestaudio/best',
    'noplaylist': False,  # باش يقبل الـ Playlist
    'quiet': True,
}

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []  # قائمة الأغاني
        self.voice_client = None

    async def play_next(self, ctx):
        if len(self.queue) > 0:
            url = self.queue.pop(0)
            with YoutubeDL(ytdl_format_options) as ytdl:
                info = ytdl.extract_info(url, download=False)
                audio_url = info.get('url')
                title = info.get('title', 'Unknown')
            
            self.voice_client.play(discord.FFmpegOpusAudio(audio_url), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
            await ctx.send(f"**:notes: دابا خدام: {title}**")
        else:
            await ctx.send("**:white_check_mark: سالات القائمة!**")

    @commands.command(name='play', aliases=['p'])
    async def play(self, ctx, *, url: str):
        if not ctx.author.voice:
            return await ctx.send("**:x: خاصك تكون فـ Voice Channel**")
        
        if not self.voice_client or not self.voice_client.is_connected():
            self.voice_client = await ctx.author.voice.channel.connect()

        self.queue.append(url)
        await ctx.send(f"**:white_check_mark: تزادت الأغنية للـ Queue (الترتيب: {len(self.queue)})**")
        
        if not self.voice_client.is_playing():
            await self.play_next(ctx)

    @commands.command(name='skip', aliases=['s'])
    async def skip(self, ctx):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
            await ctx.send("**:track_next: دزنا للأغنية اللي موراها**")

    @commands.command(name='stop')
    async def stop(self, ctx):
        self.queue = []
        if self.voice_client:
            await self.voice_client.disconnect()
            self.voice_client = None

async def setup(bot):
    await bot.add_cog(Music(bot))

bot.setup_hook = lambda: asyncio.create_task(setup(bot))
bot.run(os.getenv('DISCORD_TOKEN'))
