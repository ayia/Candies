"""
Novita AI Image Generation Service - NSFW Uncensored
Fast, reliable, and affordable NSFW image generation
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

logger = logging.getLogger("NovitaImageService")

class NovitaImageService:
    """
    Novita AI Image Generation Service

    Best models for NSFW:
    - dreamshaper_8_93211.safetensors (balanced, realistic)
    - realvisxlV40_v40LightningBakedvae.safetensors (ultra-realistic)
    - crystalClearXL_ccxl.safetensors (crystal clear quality)
    """

    def __init__(self):
        self.api_key = os.getenv("NOVITA_API_KEY", settings.HF_API_TOKEN)
        self.api_url = "https://api.novita.ai/v3/async/txt2img"
        self.result_url = "https://api.novita.ai/v3/async/task-result"

        # Best NSFW models
        self.models = {
            "realistic": "realvisxlV40_v40LightningBakedvae.safetensors",  # Ultra-realistic NSFW
            "anime": "animeArtDiffusionXL_alpha3.safetensors",  # Anime style
            "balanced": "dreamshaper_8_93211.safetensors"  # Best overall
        }

        self.images_dir = settings.IMAGES_DIR
        os.makedirs(self.images_dir, exist_ok=True)

        logger.info("="*50)
        logger.info("Novita AI Image Service Initialized")
        logger.info(f"API Key: {'SET (' + self.api_key[:8] + '...)' if self.api_key else 'NOT SET!'}")
        logger.info(f"Models: {', '.join(self.models.keys())}")
        logger.info("="*50)

    async def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        style: str = "realistic",
        width: int = 1024,
        height: int = 1024,
        steps: int = 20,
        guidance_scale: float = 7.0,
        nsfw_level: int = 0
    ) -> Optional[str]:
        """
        Generate image using Novita AI

        Args:
            prompt: Main prompt
            negative_prompt: What to avoid
            style: "realistic", "anime", or "balanced"
            width/height: Image dimensions (512-2048)
            steps: Inference steps (15-50, higher=better quality)
            guidance_scale: CFG scale (7-12)
            nsfw_level: 0-3 (higher = more explicit)

        Returns:
            Path to saved image or None
        """

        logger.info("="*50)
        logger.info("Novita AI Generation Starting")
        logger.info(f"Style: {style}")
        logger.info(f"Size: {width}x{height}")
        logger.info(f"NSFW Level: {nsfw_level}")
        logger.info(f"Prompt: {prompt[:100]}...")
        logger.info("="*50)

        # Select model based on style
        model = self.models.get(style, self.models["realistic"])

        # Enhance prompt with quality tags
        enhanced_prompt = self._enhance_prompt(prompt, nsfw_level)

        # Build negative prompt
        if not negative_prompt:
            negative_prompt = self._build_negative_prompt(nsfw_level)

        # Payload for Novita AI
        payload = {
            "extra": {
                "response_image_type": "jpeg",  # or "webp"
                "enable_nsfw_detection": False  # IMPORTANT: Disable NSFW filter
            },
            "request": {
                "model_name": model,
                "prompt": enhanced_prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "image_num": 1,
                "steps": steps,
                "seed": -1,  # Random
                "guidance_scale": guidance_scale,
                "sampler_name": "DPM++ 2M Karras",  # Best sampler
                "sd_vae": "Automatic"
            }
        }

        try:
            # 1. Submit generation task
            task_id = await self._submit_task(payload)
            if not task_id:
                logger.error("Failed to submit task")
                return None

            logger.info(f"Task submitted: {task_id}")

            # 2. Poll for result (max 60 seconds)
            image_url = await self._wait_for_result(task_id, timeout=60)
            if not image_url:
                logger.error("Failed to get result")
                return None

            # 3. Download and save image
            image_path = await self._download_image(image_url)
            if not image_path:
                logger.error("Failed to download image")
                return None

            logger.info(f"SUCCESS! Image saved: {image_path}")
            return image_path

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _submit_task(self, payload: Dict) -> Optional[str]:
        """Submit generation task to Novita AI"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"Submit failed: HTTP {response.status} - {text}")
                    return None

                data = await response.json()
                return data.get("task_id")

    async def _wait_for_result(self, task_id: str, timeout: int = 60) -> Optional[str]:
        """Poll for task result"""
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        start_time = asyncio.get_event_loop().time()

        async with aiohttp.ClientSession() as session:
            while True:
                # Check timeout
                if asyncio.get_event_loop().time() - start_time > timeout:
                    logger.error("Timeout waiting for result")
                    return None

                async with session.get(
                    self.result_url,
                    params={"task_id": task_id},
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        await asyncio.sleep(2)
                        continue

                    data = await response.json()
                    task = data.get("task", {})
                    status = task.get("status")

                    if status == "TASK_STATUS_SUCCEED":
                        # Get image URL
                        images = task.get("images", [])
                        if images and images[0].get("image_url"):
                            return images[0]["image_url"]
                        return None

                    elif status == "TASK_STATUS_FAILED":
                        reason = task.get("reason", "Unknown")
                        logger.error(f"Task failed: {reason}")
                        return None

                    elif status in ["TASK_STATUS_PROCESSING", "TASK_STATUS_QUEUED"]:
                        # Still processing
                        await asyncio.sleep(2)
                        continue

                    else:
                        logger.warning(f"Unknown status: {status}")
                        await asyncio.sleep(2)

    async def _download_image(self, image_url: str) -> Optional[str]:
        """Download image from URL and save locally"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    image_url,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        logger.error(f"Download failed: HTTP {response.status}")
                        return None

                    image_data = await response.read()

                    # Save image
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    unique_id = str(uuid.uuid4())[:8]
                    filename = f"{timestamp}_{unique_id}.jpg"
                    filepath = os.path.join(self.images_dir, filename)

                    with open(filepath, 'wb') as f:
                        f.write(image_data)

                    return filename

        except Exception as e:
            logger.error(f"Download error: {e}")
            return None

    def _enhance_prompt(self, prompt: str, nsfw_level: int) -> str:
        """Enhance prompt with quality tags"""
        quality_tags = "masterpiece, best quality, ultra detailed, 8k uhd, high resolution"

        # Add NSFW tags if needed
        if nsfw_level >= 1:
            quality_tags += ", nsfw"
        if nsfw_level >= 2:
            quality_tags += ", explicit"
        if nsfw_level >= 3:
            quality_tags += ", uncensored"

        return f"{quality_tags}, {prompt}"

    def _build_negative_prompt(self, nsfw_level: int) -> str:
        """Build negative prompt"""
        base_negative = (
            "low quality, worst quality, normal quality, lowres, bad anatomy, "
            "bad hands, bad feet, error, missing fingers, extra digit, fewer digits, "
            "cropped, jpeg artifacts, signature, watermark, username, blurry, "
            "artist name, text, logo"
        )

        # Don't add censorship tags for NSFW
        if nsfw_level == 0:
            base_negative += ", nsfw, nude, naked"

        return base_negative


# Global instance
novita_image_service = NovitaImageService()
