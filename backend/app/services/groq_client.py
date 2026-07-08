import os
import time
import logging
from typing import Optional, List
from groq import Groq, APIError, APITimeoutError, RateLimitError
from app.services.exceptions import GroqAPIException

logger = logging.getLogger(__name__)

class GroqClientWrapper:
    """Manages communication, connection timeouts, rate limit rotation, and fallback key recovery for the Groq API."""

    def __init__(self):
        # 1. Fetch keys from environment variables
        primary_key = os.getenv("GROQ_API_KEY")
        fallback_key = os.getenv("GROQ_API_KEY_FALLBACK")
        
        self.clients: List[Groq] = []
        if primary_key:
            self.clients.append(Groq(api_key=primary_key))
        if fallback_key:
            self.clients.append(Groq(api_key=fallback_key))
            
        self.current_client_idx = 0
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.timeout = float(os.getenv("GROQ_TIMEOUT", "30.0"))
        self.max_retries = int(os.getenv("GROQ_MAX_RETRIES", "3"))

    def query_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Sends prompt to Groq, rotating keys on rate limits or API errors before fallback sleeping."""
        if not self.clients:
            raise GroqAPIException("No Groq API clients could be initialized. Please configure GROQ_API_KEY.")

        retry_count = 0
        backoff_sec = 2.0

        while retry_count <= self.max_retries:
            client = self.clients[self.current_client_idx]
            try:
                logger.info(
                    f"Dispatching LLM query (Model: {self.model}, "
                    f"Client Index: {self.current_client_idx}, Attempt: {retry_count + 1})"
                )
                completion = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    timeout=self.timeout
                )
                
                content = completion.choices[0].message.content
                if not content:
                    raise GroqAPIException("Received empty content response from Groq API.")
                return content

            except (RateLimitError, APIError) as e:
                # Rotate key if we have a fallback key available
                if len(self.clients) > 1:
                    next_idx = (self.current_client_idx + 1) % len(self.clients)
                    logger.warning(
                        f"Groq API error encountered: {str(e)}. "
                        f"Rotating from client key index {self.current_client_idx} to index {next_idx}."
                    )
                    self.current_client_idx = next_idx
                    retry_count += 1
                    # Small wait when rotating, but bypass standard backoff sleep
                    time.sleep(0.5)
                    continue
                else:
                    # Single client scenario
                    retry_count += 1
                    if retry_count > self.max_retries:
                        raise GroqAPIException(f"API execution failure: {str(e)}") from e
                    logger.warning(f"Groq API error: {str(e)}. Retrying in {backoff_sec}s...")
                    time.sleep(backoff_sec)
                    backoff_sec *= 2.0

            except APITimeoutError as e:
                # Handle timeout retry
                retry_count += 1
                if retry_count > self.max_retries:
                    raise GroqAPIException(f"Groq API connection timeout: {str(e)}") from e
                logger.warning(f"Groq request timed out. Retrying in {backoff_sec}s...")
                time.sleep(backoff_sec)
                backoff_sec *= 1.5

            except Exception as e:
                # Other generic errors
                logger.error(f"Unexpected error in Groq client wrapper: {str(e)}")
                raise GroqAPIException(f"Unexpected API failure: {str(e)}") from e
                
        raise GroqAPIException("Failed to query LLM: Max retries exceeded.")
