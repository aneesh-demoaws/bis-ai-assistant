# BIS AI Newsletter Assistant 🎓

An educational AI-powered chatbot for Bhavans Indian School (BIS) Bahrain that answers questions about school newsletters using **Generative AI** and **RAG (Retrieval-Augmented Generation)**.

## 🌟 Features

- **AI-Powered Q&A**: Ask questions about the school newsletter and get instant answers
- **Educational Interface**: Learn how RAG and Generative AI work behind the scenes
- **Real-time Pipeline Visualization**: See each step of the AI process as it happens
- **Student-Friendly Design**: Clean, modern interface designed for students to experiment
- **Future Voice Support**: Ready for Amazon Nova Sonic voice-to-voice integration

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Browser (User)                        │
│  ┌─────────────────────┐  ┌───────────────────────────────┐ │
│  │    Chat Interface   │  │   "How It Works" Panel        │ │
│  │  - Ask questions    │  │   - RAG pipeline steps        │ │
│  │  - View responses   │  │   - Model info                │ │
│  └─────────────────────┘  └───────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend + Strands Agent                 │
│         Amazon Nova Lite 2 + Bedrock Knowledge Base          │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| **LLM Model** | Amazon Nova Lite 2 |
| **Agent Framework** | Strands Agents SDK |
| **Knowledge Base** | Amazon Bedrock Knowledge Base |
| **Vector Store** | Amazon OpenSearch |
| **Backend** | FastAPI + Python |
| **Frontend** | HTML/CSS/JavaScript |
| **Hosting** | Amazon Linux 2023 |

## 📋 Prerequisites

- Python 3.9+
- AWS Account with Bedrock access
- Amazon Bedrock Knowledge Base configured
- AWS credentials configured

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/aneesh-demoaws/bis-ai-assistant.git
cd bis-ai-assistant
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
export AWS_REGION=eu-west-1
export STRANDS_KNOWLEDGE_BASE_ID=YOUR_KB_ID
```

### 4. Run the application
```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8080
```

### 5. Open in browser
Navigate to `http://localhost:8080`

## 📁 Project Structure

```
bis-ai-assistant/
├── app.py              # FastAPI backend server
├── agent.py            # Strands Agent with RAG
├── requirements.txt    # Python dependencies
├── start.sh           # Startup script
├── bis-assistant.service  # Systemd service file
├── static/
│   └── index.html     # Educational web interface
└── README.md
```

## 🎓 Learning Objectives

This project helps students understand:

1. **RAG (Retrieval-Augmented Generation)**: How AI searches documents before answering
2. **Large Language Models (LLMs)**: AI trained to understand and generate text
3. **Vector Search**: Finding similar content by meaning, not just keywords
4. **Knowledge Bases**: Indexed documents the AI can search and reference
5. **API Development**: How frontend and backend communicate

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_REGION` | AWS region for Bedrock | `eu-west-1` |
| `STRANDS_KNOWLEDGE_BASE_ID` | Bedrock KB ID | Required |

### Systemd Service (Production)

```bash
# Copy service file
sudo cp bis-assistant.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable bis-assistant
sudo systemctl start bis-assistant

# Check status
sudo systemctl status bis-assistant
```

## 🎤 Future: Voice Support

The interface includes a microphone button placeholder for future integration with **Amazon Nova Sonic** for voice-to-voice conversations.

## 📝 License

This project is for educational purposes at Bhavans Indian School Bahrain.

## 👨‍🎓 Author

**Anirudh Nair**  
Student, Bhavans Indian School (BIS) Bahrain

---

*Built with ❤️ using Amazon Bedrock, Strands Agents SDK, and FastAPI*
