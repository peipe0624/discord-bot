import discord
from discord import app_commands
import requests
import os
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.environ.get("DISCORD_TOKEN")
API_URL = "http://localhost:8000/ask"

client = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    print("Bot起動完了")

@tree.command(name="ask", description="攻略用AIに質問")
async def ask(interaction: discord.Interaction, question: str):
    await interaction.response.defer()

    r = requests.post(API_URL, json={"question": question})
    answer = r.json()["answer"]

    await interaction.followup.send(answer)

client.run(TOKEN)