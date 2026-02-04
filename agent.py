import os
from strands import Agent
from strands.models import BedrockModel
from strands_tools import retrieve

os.environ.setdefault("AWS_REGION", "eu-west-1")
os.environ.setdefault("STRANDS_KNOWLEDGE_BASE_ID", "MNAX9DFME0")

SYSTEM_PROMPT = """You are the BIS Newsletter Assistant for Bhavans Indian School (BIS) Bahrain.

Your role is to help teachers, students, and guests find information from the school newsletter (December 2025).

Guidelines:
- Be friendly and helpful to students of all ages
- Answer questions based ONLY on the newsletter content retrieved
- If information is not found in the newsletter, politely say so
- Keep responses concise and easy to understand
- When you find relevant information, cite which part of the newsletter it came from

Always use the retrieve tool to search the knowledge base before answering questions."""

bedrock_model = BedrockModel(
    model_id="eu.amazon.nova-lite-v1:0",
    region_name="eu-west-1"
)

agent = Agent(
    model=bedrock_model,
    system_prompt=SYSTEM_PROMPT,
    tools=[retrieve]
)

def get_response(user_message: str) -> dict:
    """Process user message and return response with metadata."""
    result = agent(user_message)
    return {
        "answer": str(result),
        "model": "Amazon Nova Lite 2",
        "knowledge_base": "MNAX9DFME0",
        "region": "eu-west-1"
    }
