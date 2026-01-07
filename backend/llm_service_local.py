"""Local LLM Service using Transformers with Dolphin uncensored model"""
import asyncio
import torch
from typing import List, Dict, Optional
from config import settings


class LocalLLMService:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = "cognitivecomputations/dolphin-2.8-mistral-7b-v02"
        self.max_tokens = settings.MAX_NEW_TOKENS
        self.temperature = settings.TEMPERATURE
        self._loaded = False

    def _load_model(self):
        """Lazy load the model on first use"""
        if self._loaded:
            return

        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        print(f"Loading local LLM: {self.model_name} on {self.device}...")

        if self.device == "cuda":
            # 4-bit quantization for GPU with limited VRAM
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
            )
        else:
            # CPU fallback (slower)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float32,
                device_map="cpu",
                trust_remote_code=True,
            )

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self._loaded = True
        print(f"Model loaded successfully on {self.device}")

    def _format_messages(self, messages: List[Dict], system_prompt: Optional[str] = None) -> str:
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
        """Generate a response using the local model"""
        loop = asyncio.get_event_loop()

        def _generate():
            self._load_model()

            prompt = self._format_messages(messages, system_prompt)

            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=4096
            ).to(self.model.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_tokens,
                    temperature=self.temperature,
                    top_p=0.95,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.convert_tokens_to_ids("<|im_end|>"),
                )

            # Decode only the new tokens
            response = self.tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[1]:],
                skip_special_tokens=False
            )

            # Clean up the response
            if "<|im_end|>" in response:
                response = response.split("<|im_end|>")[0]

            return response.strip()

        try:
            return await loop.run_in_executor(None, _generate)
        except Exception as e:
            print(f"Local LLM error: {e}")
            return "Je suis desolee, j'ai un probleme technique. Reessaie dans un moment."


# Global instance
local_llm_service = LocalLLMService()
