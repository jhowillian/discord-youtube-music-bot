import os
import asyncio
import discord
from discord.ext import commands
from discord.ui import View, Select, Button
import yt_dlp
from concurrent.futures import ThreadPoolExecutor

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)
queues = {}
executor = ThreadPoolExecutor()

def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = {'playlist': asyncio.Queue(), 'manual': asyncio.Queue()}
    return queues[guild_id]

async def yt_search(search):
    ydl_opts = {
        'format': 'bestaudio',
        'quiet': True,
        'noplaylist': False,
        'extract_flat': 'in_playlist'
    }
    def run():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(search, download=False)
    return await asyncio.get_event_loop().run_in_executor(executor, run)

async def yt_audio(url):
    ydl_opts = {'format': 'bestaudio', 'quiet': True}
    def run():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info['url'], info.get('title', 'Unknown')
    return await asyncio.get_event_loop().run_in_executor(executor, run)

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

@bot.command()
async def play(ctx, *, search: str):
    if not ctx.author.voice:
        return await ctx.send("Você precisa estar em um canal de voz.")
    
    channel = ctx.author.voice.channel
    vc = ctx.voice_client or await channel.connect()
    if vc.channel != channel:
        await vc.move_to(channel)

    try:
        info = await yt_search(search)
    except Exception as e:
        return await ctx.send(f"Erro ao buscar: {e}")

    q = get_queue(ctx.guild.id)
    if 'entries' in info:
        added = 0
        for entry in info['entries']:
            if entry:
                await q['playlist'].put({'title': entry.get('title'), 'url': entry.get('url')})
                added += 1
        await ctx.send(f"Adicionado {added} músicas da playlist à fila.")
    else:
        await q['manual'].put({'title': info.get('title'), 'url': info.get('url')})
        await ctx.send(f"Adicionado à fila: **{info.get('title')}**")

    if not ctx.voice_client.is_playing():
        await _play_next(ctx)

async def _play_next(ctx):
    vc = ctx.voice_client
    if vc is None or not vc.is_connected():
        return

    q = get_queue(ctx.guild.id)

    while True:
        song = None
        if not q['manual'].empty():
            song = await q['manual'].get()
        elif not q['playlist'].empty():
            song = await q['playlist'].get()
        else:
            await vc.disconnect()
            return await ctx.send("Fila vazia. Saindo do canal de voz.")

        try:
            audio_url, title = await yt_audio(song['url'])
            break
        except Exception as e:
            await ctx.send(f"⚠️ Erro ao extrair áudio: **{song.get('title', 'Desconhecida')}**\n`{e}`")
            continue

    def after_play(error):
        if error:
            print("Erro após tocar:", error)
        bot.loop.create_task(_play_next(ctx))

    vc.play(
        discord.FFmpegPCMAudio(
            audio_url,
            before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            options='-vn'
        ),
        after=after_play
    )
    await ctx.send(f"Tocando agora ▶️ **{title}**")

@bot.command()
async def skip(ctx):
    vc = ctx.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await ctx.send("⏭️ Pulando para a próxima música.")
    else:
        await ctx.send("❌ Nada está sendo tocado.")

@bot.command()
async def stop(ctx):
    q = get_queue(ctx.guild.id)
    while not q['manual'].empty():
        q['manual'].get_nowait()
    while not q['playlist'].empty():
        q['playlist'].get_nowait()
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    await ctx.send("⏹️ Música parada e bot desconectado.")

class QueueSelect(View):
    def __init__(self, queue_obj: asyncio.Queue, max_per_page: int = 25):
        super().__init__(timeout=60)
        self.queue_obj = queue_obj
        self.max_per_page = max_per_page
        self.current_page = 0
        all_items = list(queue_obj._queue)
        self.total_pages = (len(all_items) + max_per_page - 1) // max_per_page
        self.update_view()

    def update_view(self):
        self.clear_items()
        items = list(self.queue_obj._queue)
        start = self.current_page * self.max_per_page
        end = min(len(items), start + self.max_per_page)
        page_items = items[start:end]

        select = Select(
            placeholder="Escolha uma música…",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label=(it['title'][:100] + "…") if len(it['title']) > 100 else it['title'],
                    value=str(i)
                )
                for i, it in enumerate(page_items, start=1)
            ]
        )
        select.callback = self.select_callback
        self.add_item(select)

        if self.current_page > 0:
            btn_prev = Button(label="« Anterior", style=discord.ButtonStyle.primary)
            btn_prev.callback = self.prev_callback
            self.add_item(btn_prev)

        page_indicator = Button(
            label=f"{self.current_page+1}/{self.total_pages}",
            style=discord.ButtonStyle.secondary,
            disabled=True
        )
        self.add_item(page_indicator)

        if self.current_page < self.total_pages - 1:
            btn_next = Button(label="Próximo »", style=discord.ButtonStyle.primary)
            btn_next.callback = self.next_callback
            self.add_item(btn_next)

    async def select_callback(self, interaction: discord.Interaction):
        choice = int(interaction.data['values'][0]) - 1
        idx_global = self.current_page * self.max_per_page + choice
        items = list(self.queue_obj._queue)
        chosen = items.pop(idx_global)

        self.queue_obj._queue.clear()
        for it in [chosen] + items:
            self.queue_obj._queue.append(it)

        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()

        await interaction.response.edit_message(
            content=f"▶️ Agora selecionado: **{chosen['title']}**",
            view=None
        )

    async def prev_callback(self, interaction: discord.Interaction):
        self.current_page -= 1
        self.update_view()
        await interaction.response.edit_message(view=self)

    async def next_callback(self, interaction: discord.Interaction):
        self.current_page += 1
        self.update_view()
        await interaction.response.edit_message(view=self)

@bot.command()
async def queue(ctx):
    q = get_queue(ctx.guild.id)
    if not q['manual'].empty():
        queue_obj = q['manual']
    elif not q['playlist'].empty():
        queue_obj = q['playlist']
    else:
        return await ctx.send("A fila está vazia.")

    view = QueueSelect(queue_obj)
    await ctx.send("📋 **Fila de músicas** — escolha uma para tocar agora:", view=view)

bot.run(os.getenv("DISCORD_TOKEN"))
