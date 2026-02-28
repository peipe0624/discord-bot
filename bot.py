import os
import asyncio
from aiohttp import web
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

# ===== Discord bot =====
intents = discord.Intents.default()
intents.message_content = True  # !ping を使うなら必要（Developer Portal側もON済み前提）

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"ログイン成功: {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! ボットは正常に動いています！")

# ===== Web server (for Render Web Service health check) =====
async def handle_root(request):
    return web.Response(text="ok")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_root)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", "8080"))  # RenderはPORTを環境変数で渡す
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()

    print(f"Web server started on 0.0.0.0:{port}")
    return runner

async def main():
    # Webを先に起動（Renderがここを見に来る）
    runner = await start_web_server()

    # Discord bot を起動
    token = os.environ["DISCORD_BOT_TOKEN"]
    async with bot:
        await bot.start(token)

    # botが落ちた場合はwebも閉じる（通常ここには来ない）
    await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())