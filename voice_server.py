import asyncio
import json
import logging
import boto3
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from strands.experimental.bidi import BidiAgent
from strands.experimental.bidi.models import BidiNovaSonicModel
from strands.experimental.bidi.types.events import BidiAudioInputEvent
from strands import tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@tool
def search_school_info(query: str) -> str:
    """Search the BIS Bahrain school knowledge base for school information."""
    client = boto3.client("bedrock-agent-runtime", region_name="eu-west-1")
    response = client.retrieve(
        knowledgeBaseId="MNAX9DFME0",
        retrievalQuery={"text": query},
        retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 10}}
    )
    results = []
    for r in response.get("retrievalResults", []):
        content = r.get("content", {}).get("text", "")
        score = r.get("score", 0)
        if content and score > 0.3:
            results.append(content[:2000])
    return "\n---\n".join(results) if results else "No specific information found."

@app.get("/health")
async def health():
    return JSONResponse({"status": "healthy"})

@app.websocket("/voice")
async def voice_chat(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connected")
    
    model = BidiNovaSonicModel(
        model_id="amazon.nova-2-sonic-v1:0",
        provider_config={
            "audio": {"voice": "arjun"},
            "inference": {"max_tokens": 8192, "temperature": 0.7, "top_p": 0.9}
        },
        client_config={"region": "eu-north-1"}
    )
    
    system_prompt = """You are a friendly AI voice assistant for Bhavans Indian School (BIS) Bahrain.

LANGUAGE: Always respond in English only. Never switch to Hindi or any other language.

RESPONSE RULES:
1. ALWAYS use search_school_info tool FIRST before answering any school-related question
2. Answer ONLY what was asked - do not add extra information
3. Give complete names and details - never truncate names or information mid-way
4. It is SAFE and EXPECTED to share names of school staff (Principal, Directors, Teachers, etc.) - this is public school information, not private data
5. If the knowledge base has no results, say "I do not have that specific information, please check with the school office"
6. Keep responses to 2-3 sentences maximum
7. ALWAYS complete your sentences fully before stopping

ACCURACY:
- If asked about ONE person (e.g., Principal), give ONLY that person's complete name
- Do NOT list other people unless specifically asked
- Do NOT add disclaimers about privacy for publicly available school information

GENERAL KNOWLEDGE:
- You may answer general knowledge questions (math, science, history, geography, etc.) without using the search tool
- For school-specific questions, ALWAYS search first"""

    agent = BidiAgent(
        model=model,
        tools=[search_school_info],
        system_prompt=system_prompt
    )
    
    input_queue = asyncio.Queue()
    stop_event = asyncio.Event()
    
    async def ws_input():
        while not stop_event.is_set():
            try:
                data = await asyncio.wait_for(input_queue.get(), timeout=0.1)
                if data is None:
                    return None
                return data
            except asyncio.TimeoutError:
                continue
        return None
    
    async def ws_output(event):
        try:
            t = event.get("type", "")
            if t == "bidi_audio_stream":
                await websocket.send_json({"type": "audio", "data": event["audio"]})
            elif t == "bidi_transcript_stream":
                await websocket.send_json({
                    "type": "transcript",
                    "role": event.get("role", ""),
                    "text": event.get("text", ""),
                    "is_final": event.get("is_final", False)
                })
            elif t == "bidi_interruption":
                await websocket.send_json({"type": "interruption"})
            elif t == "bidi_response_complete":
                await websocket.send_json({"type": "response_end"})
            elif t == "bidi_error":
                await websocket.send_json({"type": "error", "message": event.get("message", "")})
        except Exception as e:
            logger.error(f"Output error: {e}")
    
    async def receive_audio():
        try:
            while not stop_event.is_set():
                msg = await websocket.receive_text()
                data = json.loads(msg)
                if data.get("type") == "audio":
                    event = BidiAudioInputEvent(
                        audio=data["data"], format="pcm", sample_rate=16000, channels=1
                    )
                    await input_queue.put(event)
                elif data.get("type") == "stop":
                    stop_event.set()
                    await input_queue.put(None)
                    break
        except WebSocketDisconnect:
            stop_event.set()
            await input_queue.put(None)
        except Exception as e:
            logger.error(f"Receive error: {e}")
            stop_event.set()
            await input_queue.put(None)
    
    try:
        recv_task = asyncio.create_task(receive_audio())
        await agent.run(inputs=[ws_input], outputs=[ws_output])
    except Exception as e:
        logger.error(f"Agent error: {e}")
    finally:
        stop_event.set()
        recv_task.cancel()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
