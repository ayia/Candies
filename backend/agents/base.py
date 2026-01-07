"""Base Agent class for all agents"""
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from huggingface_hub import InferenceClient


class BaseAgent(ABC):
    """Base class for all agents in the system"""

    def __init__(self, provider: str, model: str, api_key: str):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.client = InferenceClient(provider=provider, api_key=api_key)
        self.name = self.__class__.__name__

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent"""
        pass

    async def call(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 256
    ) -> str:
        """Call the LLM with the agent's system prompt"""
        system_prompt = self.get_system_prompt()
        if context:
            # Inject context into system prompt
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            system_prompt = f"{system_prompt}\n\nCONTEXT:\n{context_str}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]

        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat_completion(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[{self.name}] Error: {e}")
            return ""

    async def call_with_history(
        self,
        messages: list,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 512
    ) -> str:
        """Call the LLM with conversation history"""
        if system_prompt is None:
            system_prompt = self.get_system_prompt()

        full_messages = [{"role": "system", "content": system_prompt}]
        full_messages.extend(messages)

        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat_completion(
                    model=self.model,
                    messages=full_messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[{self.name}] Error with history: {e}")
            return ""
