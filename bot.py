import os
import asyncio
from aiohttp import web
from dotenv import load_dotenv
import discord
from discord.ext import commands

# .env を読み込む（ローカル用）
load_dotenv()

# ===== Discord Bot =====
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"ログイン成功: {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! ボットは正常に動いています！")

# ===== Render用 Webサーバー =====
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

async def main():
    # Webサーバー起動（Renderがここを見に来る）
    await start_web()

    # Discord起動
    token = os.environ["DISCORD_BOT_TOKEN"]
    async with bot:
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())