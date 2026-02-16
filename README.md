# BIS AI Assistant

> Educational AI Assistant for Bhavans Indian School Bahrain 🎓

An educational AI-powered assistant for **Bhavans Indian School (BIS) Bahrain** featuring:
- 🎤 Real-time voice conversations using Amazon Nova 2 Sonic
- 🧑‍💼 3D animated avatar using Amazon Sumerian Host
- 💬 Text-based Q&A with RAG

## 🌟 Live Demo

| Interface | URL |
|-----------|-----|
| **Voice Chat** (3D Avatar) | https://bisai.demoaws.com/ |
| Voice Chat (Simple) | https://bisai.demoaws.com/voice1.html |
| Text Chat | https://bisai.demoaws.com/index.html |
| Admin Portal | https://bisai.demoaws.com/admin.html |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 USER BROWSER                                     │
│  ┌─────────────────────────────────┐    ┌─────────────────────────────────────┐ │
│  │    VOICE CHAT (3D Avatar)       │    │        TEXT CHAT (/index.html)      │ │
│  │  • Sumerian Host 3D character   │    │  • Type questions                   │ │
│  │  • Audio-driven lip sync        │    │  • See RAG pipeline visualization   │ │
│  │  • Gestures & body language     │    │  • View source documents            │ │
│  │  • Real-time audio playback     │    │                                     │ │
│  │  • Interrupt anytime (barge-in) │    │                                     │ │
│  └───────────────┬─────────────────┘    └──────────────────┬──────────────────┘ │
└──────────────────┼─────────────────────────────────────────┼────────────────────┘
                   │ WebSocket (WSS)                         │ HTTPS POST
                   ▼                                         ▼
┌─────────────────────────────────────┐    ┌─────────────────────────────────────┐
│      APPLICATION LOAD BALANCER      │    │           CLOUDFRONT + S3           │
│      bisai-alb.demoaws.com          │    │         bisai.demoaws.com           │
│  • SSL termination (ACM cert)       │    │  • Static file hosting              │
│  • Health checks on /health         │    │  • 3D assets (characters, anims)    │
│  • Target: EC2:8080                 │    │  • Global edge caching              │
└───────────────────┬─────────────────┘    └──────────────────┬──────────────────┘
                    │                                         │
                    ▼                                         ▼
┌─────────────────────────────────────┐    ┌─────────────────────────────────────┐
│        EC2 INSTANCE (eu-west-1)     │    │     API GATEWAY + LAMBDA            │
│        Amazon Linux 2023            │    │     /chat endpoint                  │
│  ┌─────────────────────────────┐    │    │  ┌─────────────────────────────┐    │
│  │      voice_server.py        │    │    │  │   Bedrock AgentCore         │    │
│  │  • FastAPI + Uvicorn        │    │    │  │  • Amazon Nova Lite         │    │
│  │  • BidiAgent (Strands SDK)  │    │    │  │  • KB retrieve tool         │    │
│  │  • WebSocket /voice         │    │    │  └──────────────┬──────────────┘    │
│  └──────────────┬──────────────┘    │    └─────────────────┼───────────────────┘
└─────────────────┼───────────────────┘                      │
                  │ Bedrock API                              │ Bedrock API
                  ▼                                          ▼
┌─────────────────────────────────────┐    ┌─────────────────────────────────────┐
│     AMAZON NOVA 2 SONIC             │    │     AMAZON BEDROCK KNOWLEDGE BASE   │
│     (eu-north-1)                    │    │     ID: MNAX9DFME0 (eu-west-1)      │
│  • Model: amazon.nova-2-sonic-v1:0  │    │  • School newsletters indexed       │
│  • Bidirectional audio streaming    │    │  • OpenSearch Serverless vectors    │
│  • Voice: "arjun"                   │    │  • Semantic search (top 10 results) │
│  • max_tokens: 8192                 │    │  • Score threshold: 0.3             │
└─────────────────────────────────────┘    └─────────────────────────────────────┘
```

---

## 🧑‍💼 3D Avatar (Amazon Sumerian Host)

The voice assistant features a realistic 3D animated character powered by the open-source Amazon Sumerian Host SDK.

### Features

| Feature | Implementation |
|---------|----------------|
| **Lip Sync** | Audio-driven viseme animation using Web Audio API AnalyserNode |
| **Gestures** | Random gestures during speech (every 3-7s) |
| **Eye Tracking** | Point of Interest (POI) tracking toward camera |
| **Blinking** | Natural random blink animation (~3s interval) |
| **Idle Animation** | Face and body idle animations |
| **Loading** | Parallel asset loading with progress indicator |

### Available Characters

| Character | Type | Status |
|-----------|------|--------|
| **Jay** | Adult Male | ✅ Active |
| Luke | Adult Male | Available |
| Preston | Adult Male | Available |
| Wes | Adult Male | Available |
| Alien | Alien | Available |

### Technical Details

- **SDK**: Amazon Sumerian Host (open source) + Three.js v0.127.0
- **Viseme weights**: Amplified 2x for visible mouth movement
- **Smoothing**: 40% lerp between viseme frames
- **Gestures**: generic_a/b/c, big, one, many, self, you, in, movement
- **Cache**: 7-day browser cache on all 3D assets

---

## 🔊 Voice Chat Component Details

### Frontend (`static/voice.html`)

| Feature | Implementation |
|---------|----------------|
| Audio Capture | Web Audio API `ScriptProcessor` at 16kHz mono |
| Audio Format | PCM Int16, base64 encoded for WebSocket |
| Playback | Scheduled `AudioBufferSource` for gapless audio |
| Interruption | Clears audio queue on `interruption` event |
| 3D Rendering | Three.js with Sumerian Host SDK |

### Backend (`voice_server.py`)

```python
# Key Components
BidiNovaSonicModel      # Nova 2 Sonic with bidirectional streaming
BidiAgent               # Strands agent for voice conversations  
BidiAudioInputEvent     # Audio input events (PCM, 16kHz, mono)
WebSocket               # FastAPI WebSocket for browser connection
```

| Event Type | Direction | Description |
|------------|-----------|-------------|
| `audio` | Both | Base64 PCM audio chunks |
| `transcript` | Server→Client | Speech-to-text with `is_final` flag |
| `interruption` | Server→Client | User interrupted assistant |
| `response_end` | Server→Client | Assistant finished speaking |
| `error` | Server→Client | Error message |

### Nova 2 Sonic Configuration

```python
BidiNovaSonicModel(
    model_id="amazon.nova-2-sonic-v1:0",
    provider_config={
        "audio": {"voice": "arjun"},
        "inference": {"max_tokens": 8192, "temperature": 0.7, "top_p": 0.9}
    },
    client_config={"region": "eu-north-1"}
)
```

---

## 📚 Knowledge Base Integration

### Tool Definition

```python
@tool
def search_school_info(query: str) -> str:
    """Search BIS school knowledge base for:
    - Events, activities, sports days
    - Academic programs, curriculum
    - Policies, rules, timings
    - Staff contacts, admissions
    - Calendar, holidays, achievements
    """
    client = boto3.client("bedrock-agent-runtime", region_name="eu-west-1")
    response = client.retrieve(
        knowledgeBaseId="MNAX9DFME0",
        retrievalQuery={"text": query},
        retrievalConfiguration={
            "vectorSearchConfiguration": {"numberOfResults": 10}
        }
    )
    # Filter by relevance score > 0.3
```

### System Prompt

```
You are a friendly AI voice assistant for Bhavans Indian School (BIS) Bahrain.

RULES:
1. ALWAYS use search_school_info tool FIRST for school questions
2. Base answers ONLY on search results - never make up information
3. If no results, say "I don't have that information, please check with the school office"
4. Keep responses concise but ALWAYS complete your sentences. Aim for 2-4 sentences.
5. Be warm and helpful like a school receptionist
```

---

## 🛠️ Technology Stack

| Layer | Component | Technology | Region |
|-------|-----------|------------|--------|
| **Frontend** | Static hosting | CloudFront + S3 | Global |
| **Frontend** | 3D Avatar | Sumerian Host + Three.js | Browser |
| **Frontend** | Voice UI | Web Audio API, WebSocket | Browser |
| **Backend** | Voice server | FastAPI + Uvicorn | eu-west-1 |
| **Backend** | Text API | Lambda + API Gateway | eu-west-1 |
| **AI** | Voice model | Amazon Nova 2 Sonic | eu-north-1 |
| **AI** | Text model | Amazon Nova Lite | eu-west-1 |
| **AI** | Agent framework | Strands Agents SDK | - |
| **Data** | Knowledge base | Bedrock KB + OpenSearch | eu-west-1 |
| **Infra** | Load balancer | Application Load Balancer | eu-west-1 |
| **Infra** | Compute | EC2 (t3.small) | eu-west-1 |

---

## 📁 Project Structure

```
bis-ai-assistant/
├── voice_server.py        # 🎤 Voice chat server (Nova 2 Sonic)
├── agent.py               # 💬 Text chat agent (Nova Lite)
├── app.py                 # 🌐 Text chat FastAPI server
├── requirements.txt       # 📦 Text chat dependencies
├── requirements-voice.txt # 📦 Voice chat dependencies
├── bis-assistant.service  # ⚙️ Text chat systemd service
├── bis-voice.service      # ⚙️ Voice chat systemd service
├── static/
│   ├── voice.html         # 🎤 Voice chat UI with 3D avatar
│   ├── index.html         # 💬 Text chat UI
│   └── admin.html         # 🔧 Admin portal for KB management
└── README.md              # 📖 This file
```

---

## 🎓 Educational Value

This project demonstrates:

| Concept | Implementation |
|---------|----------------|
| **RAG** | Knowledge Base retrieval before LLM generation |
| **Voice AI** | Real-time speech-to-speech with Nova Sonic |
| **3D Animation** | Sumerian Host with lip sync and gestures |
| **Bidirectional Streaming** | WebSocket audio streaming patterns |
| **Interruption Handling** | Barge-in detection and audio queue clearing |
| **Agent Tools** | Function calling for grounded responses |
| **Multi-region** | Optimizing for model availability |

---

## 👨‍🎓 Author

**Anirudh Nair**  
Student, Bhavans Indian School (BIS) Bahrain

---

## 📄 License

Educational project for Bhavans Indian School Bahrain.

---

*Built with ❤️ using Amazon Bedrock, Nova 2 Sonic, Sumerian Host, and Strands Agents SDK*
