from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import httpx
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

class BaseAPIHandler(ABC):
    """Abstract base class for all API handlers"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT)
    
    @abstractmethod
    async def process_message(self, message: str) -> str:
        """Process a message through the API"""
        pass
    
    def get_headers(self) -> Dict[str, str]:
        """Get common headers for API requests"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    async def make_request(self, payload: Dict[str, Any]) -> Optional[str]:
        """Make HTTP request to the API with error handling"""
        try:
            response = await self.client.post(
                self.base_url,
                headers=self.get_headers(),
                json=payload
            )
            response.raise_for_status()
            return self.extract_response_text(response.json())
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error in {self.__class__.__name__}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {self.__class__.__name__}: {str(e)}")
            raise
    
    @abstractmethod
    def extract_response_text(self, response_data: Dict[str, Any]) -> str:
        """Extract the response text from the API response"""
        pass
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()