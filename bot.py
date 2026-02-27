from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "bot is alive"

def run_web():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

import discord
from discord import app_commands
import os

TOKEN = os.environ.get("DISCORD_TOKEN")

client = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    print("Bot起動完了")

@tree.command(name="ask", description="攻略用AIに質問")
async def ask(interaction: discord.Interaction, question: str):

    # ★まず3秒以内に必ず返事（超重要）
    await interaction.response.defer(thinking=True)

    try:
        r = requests.post(API_URL, json={"question": question}, timeout=120)
        answer = r.json()["answer"]
    except Exception as e:
        answer = "AIサーバーに接続できませんでした。しばらく待ってから再度お試しください。"

    # ★あとから本当の返事を送る
    await interaction.followup.send(answer)

keep_alive()
client.run(TOKEN)