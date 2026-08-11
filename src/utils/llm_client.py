"""
LLM Client - Hugging Face Inference API Integration
Provides interface to Hugging Face hosted models for code generation.
"""

import os
import time
from typing import Optional, Dict, Any
from huggingface_hub import InferenceClient
from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger(__name__)


class LLMClient:
    """Client for LLM models via Hugging Face Inference API."""
    
    def __init__(self, api_token: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize LLM client.
        
        Args:
            api_token: Hugging Face API token (optional, reads from env)
            model: Model name (optional, reads from config)
        """
        self.api_token = api_token or os.getenv("HUGGINGFACE_API_TOKEN")
        if not self.api_token:
            raise ValueError(
                "Hugging Face API token required. Set HUGGINGFACE_API_TOKEN environment variable "
                "or get one from https://huggingface.co/settings/tokens"
            )
        
        config = get_config()
        self.model = model or config.agent.llm.model
        self.temperature = config.agent.llm.temperature
        self.max_tokens = config.agent.llm.max_tokens
        
        self.client = InferenceClient(token=self.api_token)
        logger.info(f"Initialized LLM client with model: {self.model}")
    
    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[list] = None
    ) -> str:
        """
        Generate text using the configured model.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature (optional)
            max_tokens: Maximum tokens to generate (optional)
            stop_sequences: Stop sequences (optional)
            
        Returns:
            Generated text
        """
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens
        
        try:
            logger.info(f"Generating with model: {self.model}")
            logger.debug(f"Parameters: temp={temp}, max_tokens={max_tok}, prompt_length={len(prompt)}")
            
            response = self.client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                max_tokens=max_tok,
                temperature=temp
            )
            
            try:
                result_text = response.choices[0].message.content
            except (AttributeError, IndexError):
                result_text = None

            if not result_text or len(result_text.strip()) == 0:
                raise ValueError(
                    "Model returned an empty response. "
                    "The model may still be loading (cold start) or the prompt "
                    "may be too long. Try again in a few seconds."
                )
            
            logger.info(f"Generation successful: {len(result_text)} characters")
            return result_text
            
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e).strip() if str(e).strip() else "(no error message from API)"
            
            logger.error(f"Generation error [{error_type}]: {error_msg}")
            logger.error(f"Model: {self.model}, Prompt length: {len(prompt)}")
            
            lower = error_msg.lower()
            if "rate limit" in lower:
                raise Exception(f"Rate limit exceeded. Please wait and try again. Detail: {error_msg}")
            elif "token" in lower or "authentication" in lower or "unauthorized" in lower:
                raise Exception(f"Authentication error. Check your HUGGINGFACE_API_TOKEN. Detail: {error_msg}")
            elif "model" in lower and ("not found" in lower or "unavailable" in lower):
                raise Exception(f"Model '{self.model}' not found or unavailable. Detail: {error_msg}")
            else:
                raise Exception(f"Generation failed [{error_type}]: {error_msg}")
    
    def generate_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        **kwargs
    ) -> str:
        """
        Generate with automatic retry on failure (exponential back-off).
        
        Args:
            prompt: Input prompt
            max_retries: Maximum retry attempts
            retry_delay: Base delay between retries (doubles each attempt)
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return self.generate(prompt, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait = retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Generation failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait:.1f}s: {e}"
                    )
                    time.sleep(wait)
                else:
                    logger.error(f"Generation failed after {max_retries} attempts. Last error: {e}")
        
        raise Exception(f"All {max_retries} generation attempts failed. Last error: {last_error}")
    
    def chat(
        self,
        messages: list[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Chat-style generation.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (optional)
            max_tokens: Maximum tokens to generate (optional)
            
        Returns:
            Generated response
        """
        prompt = self._format_chat_prompt(messages)
        return self.generate(prompt, temperature, max_tokens)
    
    def _format_chat_prompt(self, messages: list[Dict[str, str]]) -> str:
        """
        Format chat messages into a prompt string.
        
        Args:
            messages: List of message dicts
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}\n")
            elif role == "user":
                prompt_parts.append(f"User: {content}\n")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}\n")
        
        prompt_parts.append("Assistant:")
        return "\n".join(prompt_parts)

    # Keep backwards-compatible alias so existing imports don't break immediately
    GraniteClient = None  # Will be set below


# Backwards-compatible alias
GraniteClient = LLMClient
