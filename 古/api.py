from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Ask(BaseModel):
    question: str

@app.post("/ask")
def ask(data: Ask):
    return {
        "answer": f"ローカルBotです。『{data.question}』に対する回答（仮）です。"
    }