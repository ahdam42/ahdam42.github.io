"""Module for interacting with the LLM service using the Mistral model."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)
LLM_URL = "http://localhost:1234/v1/chat/completions"


class LLMService:
    """Service class for handling interactions with the Large Language Model (LLM)."""

    @staticmethod
    def get_llm_response(prompt: str, temperature: float = 0.8) -> str:
        """
        Retrieve a generated response from the LLM based on the provided prompt.

        Args:
            prompt: The input text prompt to generate a response for.
            temperature: Controls randomness in response generation (default: 0.8).

        Returns:
            Generated response content as a string, or empty string if an error occurs.

        """
        try:
            data: dict[str, Any] = {
                "model": "mistral-nemo-instruct-2407",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": 10000,
            }
            response = httpx.post(LLM_URL, json=data, timeout=30.0)
            response.raise_for_status()
            response_data = response.json()
        except Exception:
            logger.exception("LLM request failed")
            return ""
        else:
            if response_data.get("choices"):
                return response_data["choices"][0]["message"]["content"].strip()
            logger.error("Unexpected response structure: %s", response_data)
            return ""
