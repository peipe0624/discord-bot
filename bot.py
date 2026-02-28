import os
import sqlite3
import asyncio
from aiohttp import web
from dotenv import load_dotenv

import discord
from discord.ext import commands
from discord import app_commands

from janome.tokenizer import Tokenizer

load_dotenv()

# ===== Config =====
GUILD_ID = int(os.environ["GUILD_ID"])
ALLOWED_CHANNEL_IDS = {
    int(x.strip())
    for x in os.environ.get("ALLOWED_CHANNEL_IDS", "").split(",")
    if x.strip()
}

def is_allowed(channel_id: int) -> bool:
    return channel_id in ALLOWED_CHANNEL_IDS


# ===== Tokenizer =====
tokenizer = Tokenizer()

# ===== DB (SQLite) =====
# Renderでも固まりにくい設定
conn = sqlite3.connect("messages.db", check_same_thread=False)
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA synchronous=NORMAL;")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS messages(
    message_id INTEGER PRIMARY KEY,
    channel_id INTEGER,
    author TEXT,
    content TEXT,
    created_at TEXT
)
""")
conn.commit()

db_lock = asyncio.Lock()

# ===== Discord =====
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


# ===== Save messages =====
@bot.event
async def on_message(message: discord.Message):
    if message.guild is None or message.guild.id != GUILD_ID:
        return
    if message.author.bot:
        return
    if not is_allowed(message.channel.id):
        return
    if not message.content:
        return

    async with db_lock:
        cur.execute(
            "INSERT OR IGNORE INTO messages VALUES(?,?,?,?,?)",
            (
                int(message.id),
                int(message.channel.id),
                str(message.author),
                message.content,
                message.created_at.strftime("%Y-%m-%d %H:%M"),
            ),
        )
        conn.commit()

    await bot.process_commands(message)


# ===== Search =====
def search_messages_sync(query: str):
    """
    同期関数（SQLite検索）
    - 最近のメッセージだけを対象にして高速化
    - 単語に分解して LIKE 検索
    """
    words = [t.surface for t in tokenizer.tokenize(query) if t.surface.strip()]
    if not words:
        return []

    where = " OR ".join(["content LIKE ?"] * len(words))
    params = [f"%{w}%" for w in words]

    # ★ 最近1000件だけに絞って検索（重要：速度改善）
    sql = f"""
    SELECT channel_id, author, content, created_at
    FROM (
        SELECT channel_id, author, content, created_at
        FROM messages
        ORDER BY message_id DESC
        LIMIT 1000
    )
    WHERE {where}
    ORDER BY created_at DESC
    LIMIT 5
    """

    cur.execute(sql, params)
    return cur.fetchall()


async def search_messages(query: str):
    """
    非同期ラッパー
    - DBロックを取って thread に逃がす
    """
    async with db_lock:
        return await asyncio.to_thread(search_messages_sync, query)


# ===== Slash Commands =====
@tree.command(name="ask", description="過去ログを検索します", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(question="質問内容（短めが速いです）")
async def ask(interaction: discord.Interaction, question: str):
    await interaction.response.defer(thinking=True)

    try:
        # ★ 100秒で自動中止
        results = await asyncio.wait_for(search_messages(question), timeout=100)

    except asyncio.TimeoutError:
        await interaction.followup.send("⏱ 検索に時間がかかりすぎたので中止しました。もう少し短い言葉で試してください。")
        return

    if not results:
        await interaction.followup.send("該当するログが見つかりませんでした。")
        return

    text = "過去ログから見つかりました（最新5件）\n\n"
    for ch_id, author, content, created_at in results:
        text += f"{created_at} <#{ch_id}>\n{author}:\n{content}\n\n"

    await interaction.followup.send(text[:1800])


@tree.command(name="stop", description="現在の処理を中断します（表示上のキャンセル）", guild=discord.Object(id=GUILD_ID))
async def stop(interaction: discord.Interaction):
    # Discordの“考え中”を終わらせる目的
    await interaction.response.send_message("🛑 中断しました。", ephemeral=True)


# ===== Web server (Render health check) =====
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server started on port {port}")


@bot.event
async def on_ready():
    print(f"ログイン成功: {bot.user}")
    guild = discord.Object(id=GUILD_ID)
    tree.copy_global_to(guild=guild)
    await tree.sync(guild=guild)


async def main():
    await start_web()
    token = os.environ["DISCORD_BOT_TOKEN"]
    async with bot:
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())