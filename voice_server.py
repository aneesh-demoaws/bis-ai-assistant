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
    """Search the BIS Bahrain school knowledge base. Use this tool for ANY question about:
    - School events, activities, competitions, sports days
    - Academic programs, curriculum, subjects, exams
    - School policies, rules, uniforms, timings
    - Teachers, staff, administration contacts
    - Admissions, fees, registration
    - Facilities, clubs, extracurricular activities
    - School calendar, holidays, important dates
    - Student achievements, awards, results
    Always search before answering school-related questions."""
    client = boto3.client("bedrock-agent-runtime", region_name="eu-west-1")
    response = client.retrieve(
        knowledgeBaseId="MNAX9DFME0",
        retrievalQuery={"text": query},
        retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 5}}
    )
    results = []
    for r in response.get("retrievalResults", []):
        content = r.get("content", {}).get("text", "")
        score = r.get("score", 0)
        if content and score > 0.3:
            results.append(content[:800])
    return "\n---\n".join(results) if results else "No specific information found in the school database."

@app.get("/health")
async def health():
    return JSONResponse({"status": "healthy"})

@app.websocket("/voice")
async def voice_chat(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connected")
    
    model = BidiNovaSonicModel(
        model_id="amazon.nova-sonic-v1:0",
        provider_config={
            "audio": {"voice": "tiffany"},
            "inference": {"temperature": 0.3}
        },
        client_config={"region": "eu-north-1"}
    )
    
    system_prompt = """You are the official AI voice assistant for Bhavans Indian School (BIS) Bahrain.

CRITICAL INSTRUCTIONS:
1. ALWAYS use the search_school_info tool FIRST before answering ANY question about the school
2. Base your answers ONLY on information returned by the tool - do not make up information
3. If the tool returns no results, say "I don't have that specific information in my database"
4. Quote specific details from the search results (dates, names, numbers) when available

RESPONSE STYLE:
- Keep responses concise (2-3 sentences for simple questions)
- Speak clearly and naturally for students of all ages
- Be warm and helpful like a school receptionist
- For lists, mention only the top 3-4 items unless asked for more"""

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
                return None if data is None else data
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
                    await input_queue.put(BidiAudioInputEvent(
                        audio=data["data"], format="pcm", sample_rate=16000, channels=1
                    ))
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
