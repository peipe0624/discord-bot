import os
import requests

APP_ID = os.environ["DISCORD_APP_ID"]
BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
GUILD_ID = os.environ["DISCORD_GUILD_ID"]

url = f"https://discord.com/api/v10/applications/{APP_ID}/guilds/{GUILD_ID}/commands"

headers = {
    "Authorization": f"Bot {BOT_TOKEN}",
    "Content-Type": "application/json"
}

data = {
    "name": "ask",
    "description": "攻略AIに質問",
    "options": [
        {
            "name": "question",
            "description": "質問内容",
            "type": 3,
            "required": True
        }
    ]
}

r = requests.post(url, headers=headers, json=data)

print(r.status_code)
print(r.text)