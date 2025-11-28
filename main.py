from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import os

from core.orchestrator import AIChatOrchestrator
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Agent API",
    description="Sequential AI processing with DeepSeek and Moonshot APIs",
    version="1.0.0"
)

# CORS middleware for Firebase integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your Firebase domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    status: str
    error: str | None = None

# Initialize orchestrator
orchestrator = AIChatOrchestrator()

@app.get("/")
async def root():
    return {"message": "AI Agent API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai_agent"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        logger.info(f"Received chat request: {request.message[:100]}...")
        
        # Process the message through both APIs
        result = await orchestrator.process_message(request.message)
        
        return ChatResponse(
            response=result,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        return ChatResponse(
            response="Sorry, I encountered an error processing your request.",
            status="error",
            error=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENVIRONMENT") == "development"
    )