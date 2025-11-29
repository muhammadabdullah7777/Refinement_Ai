import logging
import time
from typing import Optional, Dict, Any
from datetime import datetime
from .handlers.deepseek import DeepSeekHandler
from .handlers.moonshot import MoonshotHandler

logger = logging.getLogger(__name__)

class AIChatOrchestrator:
    """Orchestrates sequential processing of messages through multiple AI APIs"""
    
    def __init__(self):
        self.deepseek_handler = DeepSeekHandler()
        self.moonshot_handler = MoonshotHandler()
        logger.info("AI Chat Orchestrator initialized")
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process message sequentially through DeepSeek and then Moonshot"""
        start_time = time.time()
        model_outputs = {}
        
        try:
            # Step 1: Process with DeepSeek Reasoner
            logger.info("Starting DeepSeek processing")
            deepseek_start = time.time()
            deepseek_result = await self.deepseek_handler.process_message(message)
            deepseek_time = time.time() - deepseek_start
            
            model_outputs["deepseek"] = {
                "content": deepseek_result,
                "processing_time": deepseek_time,
                "token_count": len(deepseek_result.split()),  # Approximate token count
                "model_name": "deepseek-reasoner",
                "timestamp": datetime.utcnow().isoformat()
            }
            logger.info(f"DeepSeek processing completed in {deepseek_time:.2f}s: {deepseek_result[:100]}...")
            
            # Step 2: Refine with Moonshot Kiwi K2
            logger.info("Starting Moonshot refinement")
            moonshot_start = time.time()
            moonshot_result = await self.moonshot_handler.process_message(deepseek_result)
            moonshot_time = time.time() - moonshot_start
            
            model_outputs["moonshot"] = {
                "content": moonshot_result,
                "processing_time": moonshot_time,
                "token_count": len(moonshot_result.split()),  # Approximate token count
                "model_name": "moonshot-v1-8k",
                "timestamp": datetime.utcnow().isoformat()
            }
            logger.info(f"Moonshot refinement completed in {moonshot_time:.2f}s: {moonshot_result[:100]}...")
            
            total_time = time.time() - start_time
            return {
                "primary_response": moonshot_result,
                "model_outputs": model_outputs,
                "total_processing_time": total_time
            }
            
        except Exception as e:
            logger.error(f"Error in sequential processing: {str(e)}")
            # Fallback: Try direct Moonshot processing if DeepSeek fails
            try:
                logger.info("Attempting fallback with Moonshot only")
                fallback_start = time.time()
                fallback_result = await self.moonshot_handler.process_message(message)
                fallback_time = time.time() - fallback_start
                
                model_outputs["moonshot"] = {
                    "content": fallback_result,
                    "processing_time": fallback_time,
                    "token_count": len(fallback_result.split()),
                    "model_name": "moonshot-v1-8k",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                total_time = time.time() - start_time
                return {
                    "primary_response": fallback_result,
                    "model_outputs": model_outputs,
                    "total_processing_time": total_time
                }
            except Exception as fallback_error:
                logger.error(f"Fallback processing also failed: {str(fallback_error)}")
                raise RuntimeError("Both primary and fallback processing failed") from e
    
    async def close(self):
        """Close all handlers"""
        await self.deepseek_handler.close()
        await self.moonshot_handler.close()
        logger.info("AI Chat Orchestrator closed")