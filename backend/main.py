import os
from typing import Literal
from dotenv import load_dotenv
load_dotenv(override=True)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from agent import run_agent
from tools import init_db

init_db()
app = FastAPI(title="PlayAssist")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
                   allow_methods=["*"], allow_headers=["*"])

class Msg(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=2000)

class ChatReq(BaseModel):
    messages: list[Msg] = Field(min_length=1, max_length=20)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
def chat(req: ChatReq):
    try:
        answer, trace = run_agent([m.model_dump() for m in req.messages])
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM provider error: {type(e).__name__}")
    return {"answer": answer, "trace": trace}