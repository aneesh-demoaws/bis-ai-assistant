import boto3
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent, tool
from strands.models import BedrockModel

KNOWLEDGE_BASE_ID = "MNAX9DFME0"
REGION = "eu-west-1"

SYSTEM_PROMPT = """You are the BIS Newsletter Assistant for Bhavans Indian School (BIS) Bahrain.

Your role is to help teachers, students, and guests find information from the school newsletter.

Guidelines:
- Be friendly and helpful to students of all ages
- Answer questions based ONLY on the newsletter content retrieved
- If information is not found in the newsletter, politely say so
- Keep responses concise and easy to understand

Always use the search_newsletter tool to search the knowledge base before answering questions."""

@tool
def search_newsletter(query: str) -> str:
    """Search the BIS newsletter knowledge base for information.
    
    Args:
        query: The search query to find relevant information from the newsletter
    
    Returns:
        Retrieved content from the newsletter knowledge base
    """
    client = boto3.client("bedrock-agent-runtime", region_name=REGION)
    response = client.retrieve(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        retrievalQuery={"text": query},
        retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 5}}
    )
    results = []
    for item in response.get("retrievalResults", []):
        content = item.get("content", {}).get("text", "")
        if content:
            results.append(content)
    return "\n\n---\n\n".join(results) if results else "No relevant information found in the newsletter."

bedrock_model = BedrockModel(
    model_id="eu.amazon.nova-lite-v1:0",
    region_name=REGION
)

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload):
    """Process user input and return a response"""
    user_message = payload.get("prompt", "Hello")
    agent = Agent(
        model=bedrock_model,
        system_prompt=SYSTEM_PROMPT,
        tools=[search_newsletter]
    )
    result = agent(user_message)
    return {"answer": str(result), "model": "Amazon Nova Lite 2", "knowledge_base": KNOWLEDGE_BASE_ID}

if __name__ == "__main__":
    app.run()
