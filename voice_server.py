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
    
    # Nova 2 Sonic with optimized settings
    model = BidiNovaSonicModel(
        model_id="amazon.nova-sonic-v1:0",
        provider_config={
            "audio": {
                "voice": "tiffany",
                "sampleRateHertz": 16000
            },
            "inference": {
                "temperature": 0.4,  # Slightly higher for more natural speech
                "maxTokens": 2048,
                "topP": 0.9
            },
            # Nova 2 Sonic turn detection - MEDIUM for balanced conversation
            "turnDetection": {
                "endpointingSensitivity": "MEDIUM"
            }
        },
        client_config={"region": "eu-north-1"}
    )
    
    # Optimized system prompt for natural conversation
    system_prompt = """You are a friendly, helpful AI voice assistant for Bhavans Indian School (BIS) Bahrain.

PERSONALITY:
- Warm and welcoming like a helpful school receptionist
- Patient and clear, suitable for students of all ages
- Enthusiastic about helping with school questions

CRITICAL RULES:
1. ALWAYS use search_school_info tool FIRST for ANY school-related question
2. Base answers ONLY on search results - never make up information
3. If no results found, say "I don't have that specific information, but you can check with the school office"
4. Quote specific details (dates, names, numbers) when available

CONVERSATION STYLE:
- Keep responses concise: 1-2 sentences for simple questions
- Speak naturally with appropriate pauses
- Use friendly phrases like "Great question!" or "Let me check that for you"
- For lists, mention top 3 items then offer to share more
- End with helpful follow-ups like "Is there anything else about the school I can help with?"

HANDLING INTERRUPTIONS:
- If interrupted, acknowledge briefly and address the new question
- Stay focused on the user's current need"""

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
