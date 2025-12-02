"""
Azure OpenAI client wrapper
"""
import os
from typing import List, Dict, Optional
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()


class AzureOpenAIClient:
    """Wrapper for Azure OpenAI API"""
    
    def __init__(
        self,
        deployment_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        """Initialize Azure OpenAI client"""
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        
        if not self.endpoint or not self.api_key:
            raise ValueError(
                "Azure OpenAI credentials not found. "
                "Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in .env file"
            )
        
        self.deployment_name = deployment_name or os.getenv("AZURE_OPENAI_DEPLOYMENT_GPT4")
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version
        )
    
    def get_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Get completion from Azure OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens
            )
            
            content = response.choices[0].message.content
            if content is None:
                print(f"Warning: Azure OpenAI returned None content. Finish reason: {response.choices[0].finish_reason}")
                return ""
            return content
        
        except Exception as e:
            print(f"Error calling Azure OpenAI: {e}")
            raise
    
    def get_completion_with_metadata(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict:
        """Get completion with usage metadata"""
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens
            )
            
            content = response.choices[0].message.content
            if content is None:
                print(f"Warning: Azure OpenAI returned None content. Finish reason: {response.choices[0].finish_reason}")
                content = ""
            
            return {
                "content": content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason
            }
        
        except Exception as e:
            print(f"Error calling Azure OpenAI: {e}")
            raise
