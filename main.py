from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging
import os
import json
import asyncio
import difflib

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
    include_models: list[str] = ["deepseek", "moonshot"]
    stream: bool = False

class ModelOutput(BaseModel):
    content: str
    processing_time: float
    token_count: int | None = None
    model_name: str
    timestamp: str

class ChatResponse(BaseModel):
    primary_response: str
    model_outputs: dict[str, ModelOutput]
    status: str
    error: str | None = None
    total_processing_time: float

class ComparisonResponse(BaseModel):
    similarity_score: float
    differences: list[str]
    deepseek_content: str
    moonshot_content: str
    processing_times: dict[str, float]

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
        
        # Check if streaming is requested
        if request.stream:
            return StreamingResponse(
                stream_chat_response(request.message),
                media_type="text/plain"
            )
        
        # Process the message through both APIs
        result = await orchestrator.process_message(request.message)
        
        # Convert model outputs to ModelOutput objects
        model_outputs = {}
        for model_name, output_data in result["model_outputs"].items():
            model_outputs[model_name] = ModelOutput(**output_data)
        
        return ChatResponse(
            primary_response=result["primary_response"],
            model_outputs=model_outputs,
            status="success",
            total_processing_time=result["total_processing_time"]
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        return ChatResponse(
            primary_response="Sorry, I encountered an error processing your request.",
            model_outputs={},
            status="error",
            error=str(e),
            total_processing_time=0.0
        )

async def stream_chat_response(message: str):
    """Stream chat responses from both models"""
    try:
        # Stream DeepSeek response first
        yield json.dumps({
            "type": "status",
            "data": {"status": "processing", "model": "deepseek"}
        }) + "\n"
        
        # Simulate DeepSeek processing (in real implementation, use actual streaming API)
        deepseek_result = await orchestrator.deepseek_handler.process_message(message)
        yield json.dumps({
            "type": "model_output",
            "data": {
                "model": "deepseek",
                "content": deepseek_result,
                "status": "completed"
            }
        }) + "\n"
        
        # Stream Moonshot refinement
        yield json.dumps({
            "type": "status",
            "data": {"status": "processing", "model": "moonshot"}
        }) + "\n"
        
        # Simulate Moonshot processing
        moonshot_result = await orchestrator.moonshot_handler.process_message(deepseek_result)
        yield json.dumps({
            "type": "model_output",
            "data": {
                "model": "moonshot",
                "content": moonshot_result,
                "status": "completed"
            }
        }) + "\n"
        
        # Final completion
        yield json.dumps({
            "type": "complete",
            "data": {"status": "success"}
        }) + "\n"
        
    except Exception as e:
        yield json.dumps({
            "type": "error",
            "data": {"error": str(e)}
        }) + "\n"

@app.post("/compare", response_model=ComparisonResponse)
async def compare_responses(request: ChatRequest):
    """Compare DeepSeek and Moonshot responses for the same input"""
    try:
        logger.info(f"Comparing responses for: {request.message[:100]}...")
        
        # Process the message through both APIs
        result = await orchestrator.process_message(request.message)
        
        deepseek_content = result["model_outputs"]["deepseek"]["content"]
        moonshot_content = result["model_outputs"]["moonshot"]["content"]
        
        # Calculate similarity score
        similarity = difflib.SequenceMatcher(None, deepseek_content, moonshot_content).ratio()
        
        # Generate differences
        differences = []
        diff = difflib.unified_diff(
            deepseek_content.splitlines(keepends=True),
            moonshot_content.splitlines(keepends=True),
            fromfile='deepseek',
            tofile='moonshot',
            n=3
        )
        
        for line in diff:
            if line.startswith('+') or line.startswith('-'):
                differences.append(line.strip())
        
        # Limit the number of differences for performance
        differences = differences[:20]
        
        return ComparisonResponse(
            similarity_score=similarity,
            differences=differences,
            deepseek_content=deepseek_content,
            moonshot_content=moonshot_content,
            processing_times={
                "deepseek": result["model_outputs"]["deepseek"]["processing_time"],
                "moonshot": result["model_outputs"]["moonshot"]["processing_time"]
            }
        )
        
    except Exception as e:
        logger.error(f"Error comparing responses: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENVIRONMENT") == "development"
    )