import os
import requests
from typing import List, Dict, Any, Optional

from config import (
    RAKUTEN_AI_BASE_URL,
    RAKUTEN_AI_GATEWAY_KEY,
    RAKUTEN_AI_MODEL,
)


class RakutenAIClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_sec: float = 30.0,
    ) -> None:
        self.base_url = (base_url or os.getenv("RAKUTEN_AI_BASE_URL") or RAKUTEN_AI_BASE_URL).rstrip("/")
        self.api_key = os.getenv("RAKUTEN_AI_GATEWAY_KEY") or api_key or RAKUTEN_AI_GATEWAY_KEY
        self.model = os.getenv("RAKUTEN_AI_MODEL") or model or RAKUTEN_AI_MODEL
        self.timeout_sec = timeout_sec

        # Endpoint designed to be OpenAI-compatible
        self.chat_completions_url = f"{self.base_url}/chat/completions"

    def chat(self, messages: List[Dict[str, Any]], temperature: float = 0.2, max_tokens: int = 512) -> str:
        headers = {
            # Azure API Management often uses 'Ocp-Apim-Subscription-Key' or 'api-key'. We'll include both plus Authorization for compatibility.
            "api-key": self.api_key,
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        resp = requests.post(self.chat_completions_url, json=payload, headers=headers, timeout=self.timeout_sec)
        resp.raise_for_status()
        data = resp.json()

        # OpenAI-compatible response structure
        try:
            return data["choices"][0]["message"]["content"].strip()
        except Exception:
            # Fallback: return entire json string for debugging
            return str(data)


