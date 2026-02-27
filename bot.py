import discord
from discord import app_commands
import os
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.environ.get("DISCORD_TOKEN")

client = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    print("Bot起動完了")

@tree.command(name="ask", description="攻略用AIに質問")
async def ask(interaction: discord.Interaction, question: str):
    await interaction.response.send_message(
        f"質問『{question}』を受け付けました！（クラウド稼働確認OK）"
    )

client.run(TOKEN)