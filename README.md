# BIS AI Assistant 🎓

An educational AI-powered assistant for **Bhavans Indian School (BIS) Bahrain** featuring real-time voice conversations using Amazon Nova 2 Sonic and text-based Q&A with RAG.

## 🌟 Live Demo

| Interface | URL |
|-----------|-----|
| **Voice Chat** (default) | https://bisai.demoaws.com/ |
| Text Chat | https://bisai.demoaws.com/text.html |
| Voice WebSocket API | wss://bisai-alb.demoaws.com/voice |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 USER BROWSER                                     │
│  ┌─────────────────────────────────┐    ┌─────────────────────────────────────┐ │
│  │         VOICE CHAT (/)          │    │        TEXT CHAT (/text.html)       │ │
│  │  • Microphone capture (16kHz)   │    │  • Type questions                   │ │
│  │  • Real-time audio playback     │    │  • See RAG pipeline visualization   │ │
│  │  • Interrupt anytime (barge-in) │    │  • View source documents            │ │
│  │  • Live transcription           │    │                                     │ │
│  └───────────────┬─────────────────┘    └──────────────────┬──────────────────┘ │
└──────────────────┼─────────────────────────────────────────┼────────────────────┘
                   │ WebSocket (WSS)                         │ HTTPS POST
                   ▼                                         ▼
┌─────────────────────────────────────┐    ┌─────────────────────────────────────┐
│      APPLICATION LOAD BALANCER      │    │           CLOUDFRONT + S3           │
│      bisai-alb.demoaws.com          │    │         bisai.demoaws.com           │
│  • SSL termination (ACM cert)       │    │  • Static file hosting              │
│  • Health checks on /health         │    │  • Global edge caching              │
│  • Target: EC2:8080                 │    │  • Custom domain + SSL              │
└───────────────────┬─────────────────┘    └──────────────────┬──────────────────┘
                    │                                         │
                    ▼                                         ▼
┌─────────────────────────────────────┐    ┌─────────────────────────────────────┐
│        EC2 INSTANCE (eu-west-1)     │    │     API GATEWAY + LAMBDA            │
│        Amazon Linux 2023            │    │     /chat endpoint                  │
│  ┌─────────────────────────────┐    │    │  ┌─────────────────────────────┐    │
│  │      voice_server.py        │    │    │  │       agent.py              │    │
│  │  • FastAPI + Uvicorn        │    │    │  │  • Strands Agent            │    │
│  │  • BidiAgent (Strands SDK)  │    │    │  │  • Amazon Nova Lite         │    │
│  │  • WebSocket /voice         │    │    │  │  • KB retrieve tool         │    │
│  │  • Audio streaming (PCM)    │    │    │  └──────────────┬──────────────┘    │
│  └──────────────┬──────────────┘    │    └─────────────────┼───────────────────┘
└─────────────────┼───────────────────┘                      │
                  │                                          │
                  │ Bedrock API                              │ Bedrock API
                  ▼                                          ▼
┌─────────────────────────────────────┐    ┌─────────────────────────────────────┐
│     AMAZON NOVA 2 SONIC             │    │     AMAZON BEDROCK KNOWLEDGE BASE   │
│     (eu-north-1)                    │    │     ID: MNAX9DFME0 (eu-west-1)      │
│  • Model: amazon.nova-sonic-v1:0    │    │  • School newsletters indexed       │
│  • Bidirectional audio streaming    │    │  • OpenSearch Serverless vectors    │
│  • Voice: "tiffany"                 │    │  • Semantic search (top 5 results)  │
│  • Interruption detection           │    │  • Score threshold: 0.3             │
│  • Temperature: 0.3                 │    │                                     │
└─────────────────────────────────────┘    └─────────────────────────────────────┘
```

---

## 🔊 Voice Chat Component Details

### Frontend (`static/voice.html`)

| Feature | Implementation |
|---------|----------------|
| Audio Capture | Web Audio API `ScriptProcessor` at 16kHz mono |
| Audio Format | PCM Int16, base64 encoded for WebSocket |
| Playback | Scheduled `AudioBufferSource` for gapless audio |
| Interruption | Clears audio queue on `interruption` event |
| UI States | Recording (green), Speaking (blue), Idle (red) |

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
    model_id="amazon.nova-sonic-v1:0",
    provider_config={
        "audio": {"voice": "tiffany"},
        "inference": {"temperature": 0.3}  # Lower = more factual
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
            "vectorSearchConfiguration": {"numberOfResults": 5}
        }
    )
    # Filter by relevance score > 0.3
    # Return up to 800 chars per result
```

### System Prompt Strategy

```
1. ALWAYS use search_school_info FIRST before answering
2. Base answers ONLY on tool results - no hallucination
3. If no results, admit "I don't have that information"
4. Quote specific details (dates, names, numbers)
5. Keep responses concise (2-3 sentences)
```

---

## 🛠️ Technology Stack

| Layer | Component | Technology | Region |
|-------|-----------|------------|--------|
| **Frontend** | Static hosting | CloudFront + S3 | Global |
| **Frontend** | Voice UI | Web Audio API, WebSocket | Browser |
| **Backend** | Voice server | FastAPI + Uvicorn | eu-west-1 |
| **Backend** | Text API | Lambda + API Gateway | eu-west-1 |
| **AI** | Voice model | Amazon Nova 2 Sonic | eu-north-1 |
| **AI** | Text model | Amazon Nova Lite | eu-west-1 |
| **AI** | Agent framework | Strands Agents SDK | - |
| **Data** | Knowledge base | Bedrock KB + OpenSearch | eu-west-1 |
| **Infra** | Load balancer | Application Load Balancer | eu-west-1 |
| **Infra** | Compute | EC2 (t3.small) | eu-west-1 |
| **Infra** | DNS | Route 53 | Global |
| **Infra** | SSL | AWS Certificate Manager | us-east-1, eu-west-1 |

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
│   ├── index.html         # 🎤 Voice chat UI (default)
│   └── text.html          # 💬 Text chat UI
└── README.md              # 📖 This file
```

---

## 🚀 Deployment Guide

### Prerequisites

- AWS Account with Bedrock access (Nova Lite, Nova Sonic)
- Bedrock Knowledge Base configured
- Python 3.12+ (required for Nova Sonic)
- Domain with SSL certificates

### Voice Server (EC2)

```bash
# 1. Launch EC2 (Amazon Linux 2023, t3.small+)
# 2. Install dependencies
sudo dnf install -y python3.12 python3.12-devel gcc make alsa-lib-devel

# 3. Build PortAudio (required for PyAudio)
wget http://files.portaudio.com/archives/pa_stable_v190700_20210406.tgz
tar xzf pa_stable_v190700_20210406.tgz && cd portaudio
./configure && make && sudo make install
echo '/usr/local/lib' | sudo tee /etc/ld.so.conf.d/local.conf
sudo ldconfig

# 4. Setup Python environment
python3.12 -m venv venv
source venv/bin/activate
pip install 'strands-agents[bidi]' fastapi uvicorn boto3

# 5. Run server
python voice_server.py

# 6. Setup systemd service
sudo cp bis-voice.service /etc/systemd/system/
sudo systemctl enable --now bis-voice
```

### ALB Configuration

| Setting | Value |
|---------|-------|
| Scheme | Internet-facing |
| Listener | HTTPS:443 → Target Group |
| Target | EC2 instance, port 8080 |
| Health check | GET /health |
| SSL Certificate | ACM (for custom domain) |
| Stickiness | Enabled (WebSocket) |

---

## 🎓 Educational Value

This project demonstrates:

| Concept | Implementation |
|---------|----------------|
| **RAG** | Knowledge Base retrieval before LLM generation |
| **Voice AI** | Real-time speech-to-speech with Nova Sonic |
| **Bidirectional Streaming** | WebSocket audio streaming patterns |
| **Interruption Handling** | Barge-in detection and audio queue clearing |
| **Agent Tools** | Function calling for grounded responses |
| **Multi-region** | Optimizing for model availability |
| **Serverless + Server** | Lambda for text, EC2 for stateful voice |

---

## 👨‍🎓 Author

**Anirudh Nair**  
Student, Bhavans Indian School (BIS) Bahrain

---

## 📄 License

Educational project for Bhavans Indian School Bahrain.

---

*Built with ❤️ using Amazon Bedrock, Nova 2 Sonic, and Strands Agents SDK*
