import discord
from discord.ext import commands
import yt_dlp
import asyncio
import random
from keep_alive import keep_alive  # File keep_alive.py đơn giản chạy Flask server giữ bot luôn online

TOKEN = "MTM4MDA3MDIzMTY5NDc3NDI4Mg.G1x_EJ.yDlDFViQiMsBvHpW-XDwmXW-evGuAYUydJGsRc"  # Thay token bot của bạn vào đây
GUILD_ID = 1377987973361959014  # Thay ID server của bạn

CHICOLUS_YT = "https://www.youtube.com/@Chicolus/videos"

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

ffmpeg_options = {"options": "-vn"}
song_data = []


async def fetch_songs():
    global song_data
    ydl_opts = {'format': 'bestaudio', 'extract_flat': 'in_playlist', 'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(CHICOLUS_YT, download=False)
        entries = info.get("entries", [])
        song_data = [
            {"title": e["title"], "url": f"https://www.youtube.com/watch?v={e['id']}"}
            for e in entries if "title" in e and "id" in e
        ]
    random.shuffle(song_data)


async def play_song(vc, url):
    with yt_dlp.YoutubeDL({'format': 'bestaudio'}) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info['url']
    vc.play(discord.FFmpegPCMAudio(audio_url, **ffmpeg_options))
    while vc.is_playing():
        await asyncio.sleep(1)


class SongSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="🎧 Chọn bài để phát", options=options)

    async def callback(self, interaction: discord.Interaction):
        url = self.values[0]
        title = next((s["title"] for s in song_data if s["url"] == url), "Không rõ")

        await interaction.response.send_message(f"🎶 Đang phát: **{title}**", ephemeral=False)

        vc = discord.utils.get(bot.voice_clients, guild=interaction.guild)
        if not vc or not vc.is_connected():
            channel = interaction.user.voice.channel if interaction.user.voice else None
            if not channel:
                await interaction.followup.send("❌ Bạn cần vào voice trước.", ephemeral=True)
                return
            vc = await channel.connect()

        await play_song(vc, url)


class DropdownView(discord.ui.View):
    def __init__(self, options):
        super().__init__(timeout=None)
        self.add_item(SongSelect(options))


@tree.command(name="chicolus", description="Nghe nhạc của Chicolus")
async def chicolus(interaction: discord.Interaction):
    if not song_data:
        await fetch_songs()

    options = [discord.SelectOption(label=s["title"][:100], value=s["url"]) for s in song_data[:10]]
    await interaction.response.send_message("🎵 Chọn một bài hát từ danh sách:", view=DropdownView(options))


@bot.event
async def on_ready():
    print(f"✅ Bot online: {bot.user}")
    await fetch_songs()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Cùng lắng nghe cùng Chicolus"))

    await asyncio.sleep(5)  # Đợi bot ổn định

    try:
        tree.clear_commands(guild=discord.Object(id=GUILD_ID))
        synced = await tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Slash commands synced ({len(synced)} lệnh):")
        for cmd in synced:
            print(f"  - /{cmd.name}: {cmd.description}")
    except Exception as e:
        print(f"❌ Lỗi sync lệnh: {e}")


keep_alive()
bot.run(TOKEN)
      
