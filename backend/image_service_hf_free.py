"""
FREE Hugging Face Inference API - NSFW Image Generation
100% Free, No GPU needed, No limits (with free tier)
Uses HF Inference API instead of Spaces (more stable)
"""
import os
import uuid
import asyncio
import aiohttp
import base64
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from config import settings

logger = logging.getLogger("HFFreeImageService")

class HFFreeImageService:
    """
    FREE Hugging Face Inference API Service

    Uses direct model inference instead of Gradio Spaces
    More stable, no SSL timeout issues

    Best FREE NSFW models:
    - stabilityai/stable-diffusion-xl-base-1.0 (best quality, sometimes filtered)
    - segmind/SSD-1B (fast, less filtered)
    - runwayml/stable-diffusion-v1-5 (classic, reliable)
    """

    def __init__(self):
        self.api_key = settings.HF_API_TOKEN
        self.base_url = "https://api-inference.huggingface.co/models"

        # FREE models that work well for NSFW
        # Note: Some may have safety filters, we'll use the least filtered ones
        self.models = {
            "realistic": "stabilityai/stable-diffusion-2-1",  # Good balance
            "fast": "segmind/SSD-1B",  # Very fast, less filtered
            "classic": "runwayml/stable-diffusion-v1-5",  # Most reliable for NSFW
            "xl": "stabilityai/stable-diffusion-xl-base-1.0"  # Best quality but may filter
        }

        self.images_dir = settings.IMAGES_DIR
        os.makedirs(self.images_dir, exist_ok=True)

        logger.info("="*50)
        logger.info("FREE HuggingFace Inference API Initialized")
        logger.info(f"API Key: {'SET (' + self.api_key[:8] + '...)' if self.api_key else 'NOT SET!'}")
        logger.info("Models: " + ", ".join(self.models.keys()))
        logger.info("100% FREE - No GPU needed")
        logger.info("="*50)

    async def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        style: str = "classic",  # Use "classic" for best NSFW results
        width: int = 512,  # Free tier works best with 512
        height: int = 512,
        nsfw_level: int = 0
    ) -> Optional[str]:
        """
        Generate image using FREE HF Inference API

        Args:
            prompt: Main prompt
            negative_prompt: What to avoid
            style: "classic" (best for NSFW), "fast", "realistic", "xl"
            width/height: 512 recommended for free tier
            nsfw_level: 0-3

        Returns:
            Path to saved image or None
        """

        logger.info("="*50)
        logger.info("FREE HF Inference Generation")
        logger.info(f"Model: {style}")
        logger.info(f"Size: {width}x{height}")
        logger.info(f"NSFW Level: {nsfw_level}")
        logger.info(f"Prompt: {prompt[:100]}...")
        logger.info("="*50)

        # Select model
        model_id = self.models.get(style, self.models["classic"])

        # Enhance prompt
        enhanced_prompt = self._enhance_prompt(prompt, nsfw_level)

        # Build negative prompt
        if not negative_prompt:
            negative_prompt = self._build_negative_prompt(nsfw_level)

        # Try primary model first, fallback to others if filtered
        models_to_try = [
            self.models[style],
            self.models["classic"],
            self.models["fast"]
        ]

        for attempt, model_id in enumerate(models_to_try, 1):
            logger.info(f"Attempt {attempt}/3: Trying {model_id}")

            try:
                image_data = await self._call_inference_api(
                    model_id,
                    enhanced_prompt,
                    negative_prompt,
                    width,
                    height
                )

                if image_data:
                    # Save image
                    image_path = await self._save_image(image_data)
                    if image_path:
                        logger.info(f"SUCCESS! Image saved: {image_path}")
                        return image_path

            except Exception as e:
                logger.warning(f"Model {model_id} failed: {e}")
                if attempt < len(models_to_try):
                    logger.info("Trying next model...")
                    continue

        logger.error("All models failed")
        return None

    async def _call_inference_api(
        self,
        model_id: str,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int
    ) -> Optional[bytes]:
        """Call HF Inference API"""

        url = f"{self.base_url}/{model_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Payload for text-to-image
        payload = {
            "inputs": prompt,
            "parameters": {
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "num_inference_steps": 25,  # Good balance
                "guidance_scale": 7.5
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120)  # 2 minutes max
                ) as response:

                    if response.status == 503:
                        # Model loading, wait and retry
                        logger.info("Model loading, waiting 20s...")
                        await asyncio.sleep(20)

                        # Retry
                        async with session.post(
                            url,
                            json=payload,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=120)
                        ) as retry_response:
                            if retry_response.status == 200:
                                return await retry_response.read()
                            else:
                                error_text = await retry_response.text()
                                logger.error(f"Retry failed: {retry_response.status} - {error_text}")
                                return None

                    elif response.status == 200:
                        return await response.read()

                    else:
                        error_text = await response.text()
                        logger.error(f"API error: {response.status} - {error_text}")

                        # Check for NSFW filter
                        if "safety" in error_text.lower() or "filter" in error_text.lower():
                            logger.warning("Content filtered! Try reducing NSFW level or changing prompt")

                        return None

        except asyncio.TimeoutError:
            logger.error("Request timeout after 120s")
            return None
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None

    async def _save_image(self, image_data: bytes) -> Optional[str]:
        """Save image data to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"{timestamp}_{unique_id}.png"
            filepath = os.path.join(self.images_dir, filename)

            with open(filepath, 'wb') as f:
                f.write(image_data)

            return filename

        except Exception as e:
            logger.error(f"Save error: {e}")
            return None

    def _enhance_prompt(self, prompt: str, nsfw_level: int) -> str:
        """Enhance prompt with quality tags"""
        # For NSFW, be explicit to bypass filters
        quality_tags = "high quality, detailed, professional photography"

        if nsfw_level >= 1:
            quality_tags += ", adult content, mature"
        if nsfw_level >= 2:
            quality_tags += ", explicit, nsfw"
        if nsfw_level >= 3:
            quality_tags += ", uncensored, xxx"

        return f"{quality_tags}, {prompt}"

    def _build_negative_prompt(self, nsfw_level: int) -> str:
        """Build negative prompt"""
        base_negative = (
            "low quality, blurry, bad anatomy, deformed, ugly, "
            "watermark, signature, text, logo, artist name"
        )

        # For SFW, add NSFW to negative
        if nsfw_level == 0:
            base_negative += ", nsfw, nude, naked, explicit"

        return base_negative


# Global instance
hf_free_image_service = HFFreeImageService()


# ============================================================
# ALTERNATIVE: Use Pollinations.ai (100% FREE, NO API KEY!)
# ============================================================

class PollinationsImageService:
    """
    Pollinations.ai - Completely FREE, no API key needed!

    Pros:
    - 100% free forever
    - No API key required
    - No limits
    - Very fast
    - Works for NSFW

    Cons:
    - Less control over parameters
    - Lower quality than paid services
    """

    def __init__(self):
        self.base_url = "https://image.pollinations.ai/prompt"
        self.images_dir = settings.IMAGES_DIR
        os.makedirs(self.images_dir, exist_ok=True)

        logger.info("="*50)
        logger.info("Pollinations.ai Service - 100% FREE")
        logger.info("No API key needed!")
        logger.info("="*50)

    async def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        nsfw_level: int = 0
    ) -> Optional[str]:
        """
        Generate image using Pollinations.ai

        Simply encodes prompt in URL and downloads image
        """

        logger.info(f"Generating with Pollinations.ai: {prompt[:50]}...")

        try:
            # Enhance prompt
            enhanced_prompt = self._enhance_prompt(prompt, nsfw_level)

            # Build URL - pollinations.ai uses URL encoding
            import urllib.parse
            encoded_prompt = urllib.parse.quote(enhanced_prompt)
            url = f"{self.base_url}/{encoded_prompt}?width={width}&height={height}&nologo=true&enhance=true"

            # Download image
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        image_data = await response.read()

                        # Save
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        unique_id = str(uuid.uuid4())[:8]
                        filename = f"{timestamp}_{unique_id}.jpg"
                        filepath = os.path.join(self.images_dir, filename)

                        with open(filepath, 'wb') as f:
                            f.write(image_data)

                        logger.info(f"SUCCESS! Image saved: {filename}")
                        return filename
                    else:
                        logger.error(f"Failed: HTTP {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Error: {e}")
            return None

    def _enhance_prompt(self, prompt: str, nsfw_level: int) -> str:
        """Enhance prompt"""
        enhanced = f"high quality, detailed, {prompt}"

        if nsfw_level >= 1:
            enhanced += ", nsfw, adult"
        if nsfw_level >= 2:
            enhanced += ", explicit"

        return enhanced


# Global instance - NO API KEY NEEDED!
pollinations_service = PollinationsImageService()
