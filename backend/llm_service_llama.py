"""Local LLM Service using llama-cpp-python with Dolphin GGUF model"""
import asyncio
import os
from typing import List, Dict, Optional
from pathlib import Path
from config import settings


class LlamaLLMService:
    def __init__(self):
        self.model = None
        self.model_path = None
        self.max_tokens = settings.MAX_NEW_TOKENS
        self.temperature = settings.TEMPERATURE
        self._loaded = False

        # Model directory
        self.models_dir = Path(__file__).parent / "models"
        self.models_dir.mkdir(exist_ok=True)

        # Default GGUF model - small and fast for CPU
        self.model_repo = "TheBloke/dolphin-2.2.1-mistral-7B-GGUF"
        self.model_file = "dolphin-2.2.1-mistral-7b.Q4_K_M.gguf"

    def _download_model(self):
        """Download the GGUF model if not present"""
        model_path = self.models_dir / self.model_file

        if model_path.exists():
            print(f"Model already exists: {model_path}")
            return str(model_path)

        print(f"Downloading model {self.model_file}...")
        from huggingface_hub import hf_hub_download

        downloaded_path = hf_hub_download(
            repo_id=self.model_repo,
            filename=self.model_file,
            local_dir=str(self.models_dir),
            local_dir_use_symlinks=False
        )

        print(f"Model downloaded to: {downloaded_path}")
        return downloaded_path

    def _load_model(self):
        """Load the GGUF model"""
        if self._loaded:
            return

        from llama_cpp import Llama

        model_path = self._download_model()

        print(f"Loading llama.cpp model from {model_path}...")

        # Load with CPU-optimized settings
        self.model = Llama(
            model_path=model_path,
            n_ctx=4096,  # Context window
            n_threads=os.cpu_count() or 4,  # Use all CPU threads
            n_batch=512,
            verbose=False
        )

        self._loaded = True
        print("llama.cpp model loaded successfully!")

    def _format_prompt(self, messages: List[Dict], system_prompt: Optional[str] = None) -> str:
        """Format messages using ChatML template for Dolphin"""
        formatted = ""

        if system_prompt:
            formatted += f"<|im_start|>system\n{system_prompt}<|im_end|>\n"

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted += f"<|im_start|>{role}\n{content}<|im_end|>\n"

        # Add assistant start token
        formatted += "<|im_start|>assistant\n"
        return formatted

    async def chat(self, messages: List[Dict], system_prompt: Optional[str] = None) -> str:
        """Generate a response using llama.cpp"""
        loop = asyncio.get_event_loop()

        def _generate():
            self._load_model()

            prompt = self._format_prompt(messages, system_prompt)

            response = self.model(
                prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=0.95,
                stop=["<|im_end|>", "<|im_start|>"],
                echo=False
            )

            return response["choices"][0]["text"].strip()

        try:
            return await loop.run_in_executor(None, _generate)
        except Exception as e:
            print(f"llama.cpp error: {e}")
            return "Je suis désolée, j'ai un problème technique. Réessaie dans un moment."


# Global instance
llama_llm_service = LlamaLLMService()
