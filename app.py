from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time

app = FastAPI(title="BIS Newsletter Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    answer: str
    model: str
    knowledge_base: str
    steps: list

from agent import get_response

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    steps = [
        {"step": 1, "name": "Received", "ts": time.time()},
        {"step": 2, "name": "Searching KB", "ts": time.time()},
    ]
    result = get_response(request.message)
    steps.append({"step": 3, "name": "Generating", "ts": time.time()})
    steps.append({"step": 4, "name": "Complete", "ts": time.time()})
    return ChatResponse(
        answer=result["answer"],
        model=result["model"],
        knowledge_base=result["knowledge_base"],
        steps=steps
    )

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")
