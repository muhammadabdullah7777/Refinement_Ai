from typing import Dict, Any
import logging
from .base import BaseAPIHandler
from config.settings import settings

logger = logging.getLogger(__name__)

class DeepSeekHandler(BaseAPIHandler):
    """Handler for DeepSeek Reasoner API"""
    
    def __init__(self):
        super().__init__(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_API_URL
        )
    
    async def process_message(self, message: str) -> str:
        """Process message through DeepSeek Reasoner API"""
        logger.info(f"Processing message with DeepSeek: {message[:100]}...")
        
        payload = {
            "model": "deepseek-reasoner",
            "messages": [
                {
                    "role": "user",
                    "content": message
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        result = await self.make_request(payload)
        if result is None:
            raise ValueError("DeepSeek API returned no response")
        return result
    
    def extract_response_text(self, response_data: Dict[str, Any]) -> str:
        """Extract response text from DeepSeek API response"""
        try:
            return response_data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to extract response from DeepSeek: {e}")
            raise ValueError("Invalid response format from DeepSeek API")