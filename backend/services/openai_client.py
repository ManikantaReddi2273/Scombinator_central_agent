"""
OpenAI Client Service
"""
from openai import AsyncOpenAI
from openai import APIError, RateLimitError, APIConnectionError
from config import settings
from typing import Optional, Dict, List
import logging
import json
import asyncio

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI client wrapper with async support"""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set in environment variables")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = settings.OPENAI_MODEL  # Use model from config (default: gpt-4o)
        logger.info(f"OpenAI client initialized with model: {self.model}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        response_format: Optional[Dict] = None,
        max_retries: int = 3
    ) -> str:
        """
        Make async chat completion request with retry logic
        
        Args:
            messages: List of message dicts with "role" and "content"
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            response_format: Optional JSON schema for structured output (e.g., {"type": "json_object"})
            max_retries: Maximum number of retry attempts for transient errors
        
        Returns:
            Response text content
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Prepare request parameters
                request_params = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                
                # Add response format if provided (for JSON mode)
                if response_format:
                    request_params["response_format"] = response_format
                
                response = await self.client.chat.completions.create(**request_params)
                
                if not response.choices or len(response.choices) == 0:
                    raise ValueError("Empty response from OpenAI")
                
                content = response.choices[0].message.content
                
                # Log token usage if available
                if hasattr(response, 'usage') and response.usage:
                    logger.debug(
                        f"OpenAI API usage - prompt_tokens: {response.usage.prompt_tokens}, "
                        f"completion_tokens: {response.usage.completion_tokens}, "
                        f"total_tokens: {response.usage.total_tokens}"
                    )
                
                return content
                
            except RateLimitError as e:
                last_error = e
                wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                logger.warning(f"Rate limit error (attempt {attempt + 1}/{max_retries}): {str(e)}. Retrying in {wait_time}s...")
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Rate limit error after {max_retries} attempts")
                    raise
                    
            except APIConnectionError as e:
                last_error = e
                wait_time = (attempt + 1) * 1  # Shorter backoff for connection errors: 1s, 2s, 3s
                logger.warning(f"API connection error (attempt {attempt + 1}/{max_retries}): {str(e)}. Retrying in {wait_time}s...")
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"API connection error after {max_retries} attempts")
                    raise
                    
            except APIError as e:
                # For other API errors, don't retry (likely invalid request)
                logger.error(f"OpenAI API error: {str(e)}")
                raise
                
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error in OpenAI API call: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                else:
                    raise
        
        # Should not reach here, but just in case
        if last_error:
            raise last_error
        raise ValueError("Failed to get response from OpenAI after retries")
    
    def parse_json_response(self, response: str) -> Dict:
        """
        Parse JSON response, handling markdown code blocks
        
        Args:
            response: Raw response string that may contain JSON
        
        Returns:
            Parsed JSON dictionary
        """
        try:
            # Remove markdown code blocks if present
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            cleaned = cleaned.strip()
            
            # Parse JSON
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            logger.error(f"Response was: {response[:200]}")
            raise ValueError(f"Invalid JSON response from OpenAI: {str(e)}")


# Singleton instance
openai_client = OpenAIClient()

