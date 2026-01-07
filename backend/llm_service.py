"""LLM Service using Hugging Face Inference Providers"""
import asyncio
from typing import List, Dict, Optional
from huggingface_hub import InferenceClient
from config import settings


# Fallback providers if main one fails
FALLBACK_PROVIDER = "hyperbolic"
FALLBACK_MODEL = "meta-llama/Llama-3.1-8B-Instruct"


class LLMService:
    def __init__(self):
        self.token = settings.HF_API_TOKEN
        self.provider = settings.HF_PROVIDER
        self.model = settings.HF_MODEL
        self.max_tokens = settings.MAX_NEW_TOKENS
        self.temperature = settings.TEMPERATURE

        print(f"LLM Service initialized: provider={self.provider}, model={self.model}")

        # Use HuggingFace Inference API with provider
        self.client = InferenceClient(
            provider=self.provider,
            api_key=self.token
        )

    async def chat(self, messages: List[Dict], system_prompt: Optional[str] = None) -> str:
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat_completion(
                    model=self.model,
                    messages=full_messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    top_p=0.95
                )
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"Error with {self.provider}: {e}")
            return await self._fallback_chat(full_messages)

    async def _fallback_chat(self, messages: List[Dict]) -> str:
        try:
            fallback_client = InferenceClient(
                provider=FALLBACK_PROVIDER,
                api_key=self.token
            )

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: fallback_client.chat_completion(
                    model=FALLBACK_MODEL,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"Fallback also failed: {e}")
            return "Je suis désolée, j'ai un problème technique. Réessaie dans un moment."

    def update_settings(self, provider: str = None, model: str = None,
                       temperature: float = None, max_tokens: int = None):
        if provider:
            self.provider = provider
            self.client = InferenceClient(provider=provider, api_key=self.token)
        if model:
            self.model = model
        if temperature is not None:
            self.temperature = temperature
        if max_tokens is not None:
            self.max_tokens = max_tokens


llm_service = LLMService()
