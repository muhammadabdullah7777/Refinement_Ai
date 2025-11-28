from typing import Dict, Any
import logging
from .base import BaseAPIHandler
from config.settings import settings

logger = logging.getLogger(__name__)

class MoonshotHandler(BaseAPIHandler):
    """Handler for Moonshot Kiwi K2 API"""
    
    def __init__(self):
        super().__init__(
            api_key=settings.MOONSHOT_API_KEY,
            base_url=settings.MOONSHOT_API_URL
        )
    
    async def process_message(self, message: str) -> str:
        """Process message through Moonshot Kiwi K2 API"""
        logger.info(f"Processing message with Moonshot: {message[:100]}...")
        
        payload = {
            "model": "moonshot-v1-8k",
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
            raise ValueError("Moonshot API returned no response")
        return result
    
    def extract_response_text(self, response_data: Dict[str, Any]) -> str:
        """Extract response text from Moonshot API response"""
        try:
            return response_data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to extract response from Moonshot: {e}")
            raise ValueError("Invalid response format from Moonshot API")