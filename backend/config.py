"""Configuration settings for Candy AI Clone"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (parent of backend folder)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path, override=True)


class Settings:
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://candy_user:candy_pass@localhost:5432/candy_db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Hugging Face
    HF_API_TOKEN: str = os.getenv("HF_API_TOKEN", "")
    HF_PROVIDER: str = os.getenv("HF_PROVIDER", "featherless-ai")
    HF_MODEL: str = os.getenv("HF_MODEL", "cognitivecomputations/dolphin-2.9.3-mistral-nemo-12b")

    # LLM Parameters
    MAX_NEW_TOKENS: int = int(os.getenv("MAX_NEW_TOKENS", "512"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.85"))
    CONTEXT_WINDOW: int = int(os.getenv("CONTEXT_WINDOW", "20"))

    # Image Models
    IMAGE_MODEL_REALISTIC: str = os.getenv("IMAGE_MODEL_REALISTIC", "UnfilteredAI/NSFW-gen-v2")
    IMAGE_MODEL_ANIME: str = os.getenv("IMAGE_MODEL_ANIME", "UnfilteredAI/NSFW-GEN-ANIME-v2")
    IMAGE_STEPS: int = int(os.getenv("IMAGE_STEPS", "30"))
    IMAGE_GUIDANCE: float = float(os.getenv("IMAGE_GUIDANCE", "7.5"))

    # Storage
    IMAGES_DIR: str = os.getenv("IMAGES_DIR", "./images")

    # Multi-Agent System
    USE_AGENTS: bool = os.getenv("USE_AGENTS", "false").lower() == "true"

    # Fallback LLM settings
    FALLBACK_PROVIDER: str = "together"
    FALLBACK_MODEL: str = "mistralai/Mistral-7B-Instruct-v0.3"


settings = Settings()
