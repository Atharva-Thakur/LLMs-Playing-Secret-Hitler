"""
Configuration loader and utilities
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""
    
    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    AZURE_OPENAI_DEPLOYMENT_GPT4 = os.getenv("AZURE_OPENAI_DEPLOYMENT_GPT4", "gpt-4")
    
    # Game settings
    NUM_PLAYERS = int(os.getenv("NUM_PLAYERS", "5"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "500"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    SAVE_GAME_LOGS = os.getenv("SAVE_GAME_LOGS", "true").lower() == "true"
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./game_logs")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        if not cls.AZURE_OPENAI_ENDPOINT or not cls.AZURE_OPENAI_API_KEY:
            raise ValueError(
                "Missing Azure OpenAI credentials. "
                "Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in .env file"
            )
        
        if cls.NUM_PLAYERS < 5 or cls.NUM_PLAYERS > 10:
            raise ValueError("NUM_PLAYERS must be between 5 and 10")
        
        return True
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "num_players": cls.NUM_PLAYERS,
            "temperature": cls.TEMPERATURE,
            "max_tokens": cls.MAX_TOKENS,
            "log_level": cls.LOG_LEVEL,
            "save_logs": cls.SAVE_GAME_LOGS,
            "output_dir": cls.OUTPUT_DIR
        }
