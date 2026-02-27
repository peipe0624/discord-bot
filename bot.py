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
    # deferしない最小構成（すぐ返す）
    await interaction.response.send_message(
        f"質問『{question}』を受け付けました！（クラウド稼働確認OK）"
    )

keep_alive()
client.run(TOKEN)