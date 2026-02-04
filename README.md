# BIS AI Assistant 🎓

An educational AI-powered assistant for Bhavans Indian School (BIS) Bahrain featuring:
- **Text Chat**: RAG-powered Q&A using Amazon Bedrock Knowledge Base
- **Voice Chat**: Real-time voice-to-voice using Amazon Nova 2 Sonic

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              User Browser                                    │
│  ┌──────────────────────┐              ┌──────────────────────┐             │
│  │   Text Chat (/)      │              │  Voice Chat (/voice) │             │
│  │   - Type questions   │              │  - Speak questions   │             │
│  │   - See RAG pipeline │              │  - Hear responses    │             │
│  └──────────┬───────────┘              └──────────┬───────────┘             │
└─────────────┼──────────────────────────────────────┼────────────────────────┘
              │ HTTPS                                │ WSS (WebSocket)
              ▼                                      ▼
┌─────────────────────────────┐    ┌─────────────────────────────────────────┐
│   CloudFront + S3           │    │   ALB (bisai-alb.demoaws.com)           │
│   bisai.demoaws.com         │    │   HTTPS → EC2:8080                      │
└─────────────┬───────────────┘    └──────────────────┬──────────────────────┘
              │                                       │
              ▼                                       ▼
┌─────────────────────────────┐    ┌─────────────────────────────────────────┐
│   API Gateway + Lambda      │    │   EC2 (Amazon Linux 2023)               │
│   /chat endpoint            │    │   voice_server.py                       │
│   Strands Agent             │    │   - BidiAgent + Nova 2 Sonic            │
│   + Nova Lite               │    │   - WebSocket audio streaming           │
└─────────────┬───────────────┘    │   - Interruption support                │
              │                    └──────────────────┬──────────────────────┘
              │                                       │
              └───────────────┬───────────────────────┘
                              ▼
              ┌───────────────────────────────────────┐
              │   Amazon Bedrock Knowledge Base       │
              │   ID: MNAX9DFME0 (eu-west-1)          │
              │   - School newsletters                │
              │   - OpenSearch vector store           │
              └───────────────────────────────────────┘
```

## 🛠️ Technology Stack

| Component | Technology | Region |
|-----------|------------|--------|
| **Text LLM** | Amazon Nova Lite | eu-west-1 |
| **Voice LLM** | Amazon Nova 2 Sonic | eu-north-1 |
| **Agent Framework** | Strands Agents SDK | - |
| **Voice Streaming** | BidiAgent (bidirectional) | - |
| **Knowledge Base** | Amazon Bedrock KB | eu-west-1 |
| **Vector Store** | Amazon OpenSearch | eu-west-1 |
| **Text Backend** | Lambda + API Gateway | eu-west-1 |
| **Voice Backend** | EC2 + ALB | eu-west-1 |
| **Frontend** | CloudFront + S3 | Global |

## 🎤 Voice Features (Nova 2 Sonic)

- **Bidirectional Streaming**: Continuous audio flow in both directions
- **Barge-in/Interruption**: Speak anytime to interrupt the assistant
- **Voice Activity Detection**: Automatic speech detection
- **Real-time Transcripts**: See what you say and hear
- **Low Latency**: Optimized for natural conversation

## 📋 Prerequisites

- Python 3.12+ (required for Nova Sonic)
- AWS Account with Bedrock access
- Amazon Bedrock Knowledge Base configured
- PyAudio dependencies (portaudio)

## 🚀 Quick Start

### Text Chat (Lambda)
```bash
# Deploy via SAM or manually configure Lambda
pip install strands-agents boto3
```

### Voice Chat (EC2)
```bash
# Install dependencies
pip install 'strands-agents[bidi]' fastapi uvicorn boto3

# Run server
python voice_server.py
```

## 📁 Project Structure

```
bis-ai-assistant/
├── app.py                 # Text chat FastAPI server
├── agent.py               # Text chat Strands Agent
├── voice_server.py        # Voice chat with BidiAgent
├── requirements.txt       # Text chat dependencies
├── requirements-voice.txt # Voice chat dependencies
├── bis-assistant.service  # Text chat systemd service
├── bis-voice.service      # Voice chat systemd service
├── static/
│   ├── index.html        # Text chat interface
│   └── voice.html        # Voice chat interface
└── README.md
```

## 🌐 Live URLs

| Interface | URL |
|-----------|-----|
| Text Chat | https://bisai.demoaws.com/ |
| Voice Chat | https://bisai.demoaws.com/voice.html |
| Voice API | wss://bisai-alb.demoaws.com/voice |

## 🎓 Learning Objectives

This project demonstrates:

1. **RAG (Retrieval-Augmented Generation)**: Grounding AI responses in documents
2. **Voice-to-Voice AI**: Real-time speech conversation with LLMs
3. **Bidirectional Streaming**: WebSocket audio streaming patterns
4. **Interruption Handling**: Natural conversation flow with barge-in
5. **Multi-region Architecture**: Optimizing for service availability

## 👨‍🎓 Author

**Anirudh Nair**  
Student, Bhavans Indian School (BIS) Bahrain

---

*Built with ❤️ using Amazon Bedrock, Nova 2 Sonic, Strands Agents SDK*
