import os
import json
import asyncio
import httpx
from fastapi import FastAPI, Request, HTTPException
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

app = FastAPI()

DISCORD_PUBLIC_KEY = os.environ["DISCORD_PUBLIC_KEY"]  # Developer PortalのPublic Key
APP_ID = os.environ["DISCORD_APP_ID"]                  # Application ID
API_URL = os.environ["API_URL"]                        # 例: https://ai-api-dn8h.onrender.com/ask


@app.get("/")
def health():
    return {"status": "ok"}


def verify_discord_signature(public_key: str, signature: str, timestamp: str, body: bytes) -> bool:
    try:
        verify_key = VerifyKey(bytes.fromhex(public_key))
        verify_key.verify(timestamp.encode() + body, bytes.fromhex(signature))
        return True
    except BadSignatureError:
        return False


async def send_followup(interaction_token: str, content: str):
    # FollowupはBot Token不要（interaction tokenで送れる）
    url = f"https://discord.com/api/v10/webhooks/{APP_ID}/{interaction_token}"
    async with httpx.AsyncClient(timeout=30) as client:
        await client.post(url, json={"content": content})


async def handle_ask(interaction_token: str, question: str):
    # AI APIへ問い合わせ → followup送信
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(API_URL, json={"question": question})
            r.raise_for_status()
            data = r.json()
        answer = data.get("answer") or "回答が取得できませんでした。"
    except Exception as e:
        answer = f"AIサーバーに接続できませんでした。しばらく待ってから再度お試しください。\n({e})"

    await send_followup(interaction_token, answer)


@app.post("/interactions")
async def interactions(req: Request):
    body = await req.body()

    sig = req.headers.get("X-Signature-Ed25519")
    ts = req.headers.get("X-Signature-Timestamp")
    if not sig or not ts:
        raise HTTPException(status_code=401, detail="Missing signature headers")

    if not verify_discord_signature(DISCORD_PUBLIC_KEY, sig, ts, body):
        raise HTTPException(status_code=401, detail="Bad signature")

    payload = json.loads(body.decode("utf-8"))
    t = payload.get("type")

    # 1) Discordの疎通(PING)
    if t == 1:
        return {"type": 1}

    # 2) スラッシュコマンド
    if t == 2:
        data = payload.get("data", {})
        name = data.get("name")

        if name == "ask":
            options = data.get("options", [])
            question = ""
            if options and isinstance(options, list):
                # /ask question:xxx を想定
                question = options[0].get("value", "")

            interaction_token = payload["token"]

            # まず3秒以内にACK（超重要）
            # type=5: DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
            # ここでバックグラウンド処理開始
            asyncio.create_task(handle_ask(interaction_token, question))

            return {"type": 5}

        # 不明コマンド
        return {
            "type": 4,
            "data": {"content": "不明なコマンドです。"}
        }

    # その他イベント
    return {"type": 4, "data": {"content": "未対応のイベントです。"}}