# ===== Render無料対策：ダミーWebサーバー =====
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route("/")
def home():
    return "bot is alive"

def run_web():
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = Thread(target=run_web)
    t.start()


# ===== Discord Bot 本体 =====
import discord
from discord import app_commands
import aiohttp
import os

# 環境変数（RenderのEnvironmentに設定する）
TOKEN = os.environ["DISCORD_TOKEN"]
APP_ID = int(os.environ["DISCORD_APP_ID"])
API_URL = os.environ["API_URL"]  # 例: https://xxxxx.onrender.com/ask

intents = discord.Intents.default()
client = discord.Client(intents=intents, application_id=APP_ID)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    try:
        synced = await tree.sync()
        print(f"Bot起動完了 / synced {len(synced)} commands")
    except Exception as e:
        print("tree.sync failed:", repr(e))


@tree.command(name="ask", description="攻略用AIに質問")
async def ask(interaction: discord.Interaction, question: str):
    # ★3秒以内に必ず返す（超重要）
    await interaction.response.defer(thinking=True)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                API_URL,
                json={"question": question},
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                data = await resp.json()
        answer = data.get("answer", "回答が取得できませんでした。")
    except Exception as e:
        answer = f"AIサーバーに接続できませんでした。しばらく待ってください。\n({e})"

    await interaction.followup.send(answer)


# ===== 起動 =====
keep_alive()
client.run(TOKEN)