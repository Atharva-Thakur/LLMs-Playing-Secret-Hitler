import os
import time
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv
from src.utils.logger import logger

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    logger.warning("GEMINI_API_KEY not found in environment variables. Please set it in .env file.")

genai.configure(api_key=API_KEY)

# Configuration for the model
GENERATION_CONFIG = {
    "temperature": 0.9,  # High temperature for creative/deceptive play
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

SAFETY_SETTINGS = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
]

class LLMClient:
    def __init__(self, model_name="gemini-2.5-flash"):
        self.model_name = model_name
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=GENERATION_CONFIG,
            safety_settings=SAFETY_SETTINGS
        )
        self.last_request_time = 0
        self.min_delay = 4.0  # Seconds between requests to avoid rate limits

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_response(self, prompt):
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_delay:
            time.sleep(self.min_delay - time_since_last)

        try:
            response = self.model.generate_content(prompt)
            self.last_request_time = time.time()
            
            if not response.candidates:
                raise ValueError("Gemini returned no candidates.")
            
            candidate = response.candidates[0]
            if not candidate.content.parts:
                finish_reason = getattr(candidate, 'finish_reason', 'Unknown')
                safety_ratings = getattr(candidate, 'safety_ratings', 'Unknown')
                prompt_feedback = getattr(response, 'prompt_feedback', 'Unknown')
                logger.warning(f"Gemini returned candidate with no parts. Finish reason: {finish_reason}, Safety: {safety_ratings}, Feedback: {prompt_feedback}")
                raise ValueError(f"Gemini returned candidate with no content parts. Finish reason: {finish_reason}")

            return response.text
        except Exception as e:
            logger.error(f"Error generating response from Gemini: {e}")
            raise e
