import logging
from typing import Optional
from .handlers.deepseek import DeepSeekHandler
from .handlers.moonshot import MoonshotHandler

logger = logging.getLogger(__name__)

class AIChatOrchestrator:
    """Orchestrates sequential processing of messages through multiple AI APIs"""
    
    def __init__(self):
        self.deepseek_handler = DeepSeekHandler()
        self.moonshot_handler = MoonshotHandler()
        logger.info("AI Chat Orchestrator initialized")
    
    async def process_message(self, message: str) -> str:
        """Process message sequentially through DeepSeek and then Moonshot"""
        try:
            # Step 1: Process with DeepSeek Reasoner
            logger.info("Starting DeepSeek processing")
            deepseek_result = await self.deepseek_handler.process_message(message)
            logger.info(f"DeepSeek processing completed: {deepseek_result[:100]}...")
            
            # Step 2: Refine with Moonshot Kiwi K2
            logger.info("Starting Moonshot refinement")
            moonshot_result = await self.moonshot_handler.process_message(deepseek_result)
            logger.info(f"Moonshot refinement completed: {moonshot_result[:100]}...")
            
            return moonshot_result
            
        except Exception as e:
            logger.error(f"Error in sequential processing: {str(e)}")
            # Fallback: Try direct Moonshot processing if DeepSeek fails
            try:
                logger.info("Attempting fallback with Moonshot only")
                return await self.moonshot_handler.process_message(message)
            except Exception as fallback_error:
                logger.error(f"Fallback processing also failed: {str(fallback_error)}")
                raise RuntimeError("Both primary and fallback processing failed") from e
    
    async def close(self):
        """Close all handlers"""
        await self.deepseek_handler.close()
        await self.moonshot_handler.close()
        logger.info("AI Chat Orchestrator closed")