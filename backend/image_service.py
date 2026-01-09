"""Image Generation Service v10.0 - Multi-Space with Retry & Fallback"""
import os
import uuid
import asyncio
import shutil
import sys
import io
import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from gradio_client import Client as GradioClient
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("ImageService")

# Import multi-agent prompt system
try:
    from services.image_prompt_agents import generate_image_prompt, image_prompt_orchestrator
    AGENTS_AVAILABLE = True
    logger.info("Multi-agent prompt system loaded")
except ImportError as e:
    AGENTS_AVAILABLE = False
    logger.warning(f"Multi-agent system not available: {e}")


# Available NSFW image generation spaces with their API configurations
# Each space has DIFFERENT API endpoints and parameters!
NSFW_SPACES = [
    {
        "name": "Heartsync/Adult",
        "endpoint": "/generate_image",
        "type": "adult",  # predict(prompt, height, width, steps, seed, randomize, num_images)
        "default_steps": 18,
        "priority": 1
    },
    {
        "name": "Heartsync/NSFW-Uncensored-photo",
        "endpoint": "/infer",
        "type": "infer",  # predict(prompt, negative_prompt, seed, dimensions, guidance_scale, inference_steps)
        "default_steps": 30,
        "priority": 2
    },
    {
        "name": "Heartsync/NSFW-image",
        "endpoint": "/generate",
        "type": "generate",  # predict(prompt, negative_prompt, steps, guidance, dimensions, num_samples)
        "default_steps": 30,
        "priority": 3
    }
]


class ImageService:
    """
    Image Service v10.0 - Multi-Space with Retry & Fallback

    Primary: Heartsync/Adult
    Fallbacks: Heartsync/NSFW-Uncensored-photo, Heartsync/NSFW-image

    Features:
    - Automatic retry on quota exceeded
    - Fallback to alternative Heartsync spaces
    - Wait and retry option
    """

    def __init__(self):
        self.token = settings.HF_API_TOKEN
        self.images_dir = settings.IMAGES_DIR
        os.makedirs(self.images_dir, exist_ok=True)

        # Available spaces sorted by priority
        self.spaces = sorted(NSFW_SPACES, key=lambda x: x["priority"])
        self.current_space_index = 0

        # Retry settings
        self.max_retries = 3
        self.retry_delay = 5  # seconds between retries
        self.quota_wait_time = 30  # seconds to wait if quota exceeded

        # Quality settings
        self.default_steps = 18
        self.default_width = 1024
        self.default_height = 1024

        logger.info("=" * 50)
        logger.info("v10.1 - Multi-Space with HF Authentication")
        logger.info(f"Primary: {self.spaces[0]['name']}")
        logger.info(f"Fallbacks: {', '.join([s['name'] for s in self.spaces[1:]])}")
        logger.info(f"HF Token: {'SET (' + self.token[:8] + '...)' if self.token else 'NOT SET!'}")
        logger.info(f"Max retries: {self.max_retries}, Retry delay: {self.retry_delay}s")
        logger.info("=" * 50)

    async def generate(
        self,
        prompt: str,
        style: str = "realistic",
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        steps: Optional[int] = None,
        guidance: Optional[float] = None,
        seed: Optional[int] = None,
        nsfw: bool = False,
        nsfw_level: int = 0
    ) -> str:
        """Generate an image with retry and fallback to alternative spaces"""

        # Enhance prompt
        enhanced_prompt = self._enhance_prompt(prompt, nsfw_level, style)

        # Clamp dimensions
        width = max(512, min(2048, width))
        height = max(512, min(2048, height))

        logger.info("=" * 50)
        logger.info("Image Generation Starting (with retry & fallback)")
        logger.info(f"NSFW Level: {nsfw_level}")
        logger.info(f"Size: {width}x{height}")
        logger.info(f"Prompt: {enhanced_prompt[:100]}...")
        logger.info("=" * 50)

        errors = []

        # Try each space in priority order
        for space_config in self.spaces:
            space_name = space_config["name"]
            num_steps = steps or space_config["default_steps"]

            # Try with retries for each space
            for attempt in range(self.max_retries):
                try:
                    logger.info(f"[Attempt {attempt + 1}/{self.max_retries}] Trying {space_name}...")

                    result = await self._generate_with_space(
                        space_config=space_config,
                        prompt=enhanced_prompt,
                        _negative_prompt=negative_prompt or "",
                        width=width,
                        height=height,
                        steps=num_steps,
                        seed=seed,
                        _guidance=guidance or 7.0
                    )

                    logger.info(f">>> SUCCESS with {space_name}")
                    return result

                except Exception as e:
                    error_msg = str(e)
                    errors.append(f"{space_name} (attempt {attempt + 1}): {error_msg}")
                    logger.warning(f">>> {space_name} failed: {error_msg}")

                    # Check if quota exceeded - wait before retry
                    if "quota" in error_msg.lower() or "exceeded" in error_msg.lower():
                        if attempt < self.max_retries - 1:
                            logger.info(f"Quota exceeded, waiting {self.retry_delay}s before retry...")
                            await asyncio.sleep(self.retry_delay)
                        else:
                            logger.info(f"Quota exceeded on {space_name}, trying next space...")
                            break  # Move to next space
                    elif attempt < self.max_retries - 1:
                        logger.info(f"Retrying in {self.retry_delay}s...")
                        await asyncio.sleep(self.retry_delay)

        # All spaces failed
        error_summary = "\n".join(errors)
        logger.error(f"All spaces failed:\n{error_summary}")
        raise Exception(f"All image generation spaces failed. Errors:\n{error_summary}")

    async def _generate_with_space(
        self,
        space_config: Dict[str, Any],
        prompt: str,
        _negative_prompt: str,
        width: int,
        height: int,
        steps: int,
        seed: Optional[int],
        _guidance: float
    ) -> str:
        """Generate image with a specific space - routes to the correct handler"""
        space_name = space_config["name"]
        space_type = space_config.get("type", "adult")

        logger.info(f"Connecting to {space_name} (type: {space_type})...")

        # Route to the correct handler based on space type
        if space_type == "adult":
            # Heartsync/Adult - /generate_image endpoint
            return await self._generate_heartsync_adult(space_name, prompt, width, height, steps, seed)
        elif space_type == "infer":
            # Heartsync/NSFW-Uncensored-photo - /infer endpoint
            return await self._generate_heartsync_infer(space_name, prompt, _negative_prompt, width, height, steps, seed, _guidance)
        elif space_type == "generate":
            # Heartsync/NSFW-image - /generate endpoint
            return await self._generate_heartsync_generate(space_name, prompt, _negative_prompt, width, height, steps, seed, _guidance)
        else:
            raise Exception(f"Unknown space type: {space_type} for {space_name}")

    async def _generate_heartsync_adult(
        self,
        space_name: str,
        prompt: str,
        width: int,
        height: int,
        steps: int,
        seed: Optional[int]
    ) -> str:
        """Generate with Heartsync/Adult - /generate_image endpoint"""
        loop = asyncio.get_event_loop()
        hf_token = self.token  # Use HF token for authentication

        def _call_space():
            old_stdout, old_stderr = sys.stdout, sys.stderr
            sys.stdout, sys.stderr = io.StringIO(), io.StringIO()
            try:
                # Pass HF token for authentication - this gives us quota as authenticated user
                client = GradioClient(space_name, hf_token=hf_token)
                logger.info(f"[{space_name}] Connected with HF authentication")
            finally:
                sys.stdout, sys.stderr = old_stdout, old_stderr

            # API: predict(prompt, height, width, num_inference_steps, seed, randomize_seed, num_images)
            return client.predict(
                prompt,
                height,
                width,
                steps,
                seed if seed else 42,
                seed is None,
                1,
                api_name="/generate_image"
            )

        result = await asyncio.wait_for(
            loop.run_in_executor(None, _call_space),
            timeout=180
        )
        return self._process_gradio_result(result, space_name)

    async def _generate_heartsync_infer(
        self,
        space_name: str,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        steps: int,
        seed: Optional[int],
        guidance: float
    ) -> str:
        """Generate with Heartsync/NSFW-Uncensored-photo - /infer endpoint"""
        loop = asyncio.get_event_loop()
        hf_token = self.token  # Use HF token for authentication

        def _call_space():
            old_stdout, old_stderr = sys.stdout, sys.stderr
            sys.stdout, sys.stderr = io.StringIO(), io.StringIO()
            try:
                # Pass HF token for authentication
                client = GradioClient(space_name, hf_token=hf_token)
                logger.info(f"[{space_name}] Connected with HF authentication")
            finally:
                sys.stdout, sys.stderr = old_stdout, old_stderr

            # API: predict(prompt, negative_prompt, seed, dimensions, guidance_scale, inference_steps)
            # dimensions format: "WxH" string
            dimensions = f"{width}x{height}"
            return client.predict(
                prompt,
                negative_prompt or "",
                seed if seed else 42,
                dimensions,
                guidance or 7.0,
                steps,
                api_name="/infer"
            )

        result = await asyncio.wait_for(
            loop.run_in_executor(None, _call_space),
            timeout=180
        )
        return self._process_gradio_result(result, space_name)

    async def _generate_heartsync_generate(
        self,
        space_name: str,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        steps: int,
        seed: Optional[int],
        guidance: float
    ) -> str:
        """Generate with Heartsync/NSFW-image - /generate endpoint"""
        loop = asyncio.get_event_loop()
        hf_token = self.token  # Use HF token for authentication

        def _call_space():
            old_stdout, old_stderr = sys.stdout, sys.stderr
            sys.stdout, sys.stderr = io.StringIO(), io.StringIO()
            try:
                # Pass HF token for authentication
                client = GradioClient(space_name, hf_token=hf_token)
                logger.info(f"[{space_name}] Connected with HF authentication")
            finally:
                sys.stdout, sys.stderr = old_stdout, old_stderr

            # API: predict(prompt, negative_prompt, inference_steps, guidance_scale, dimensions, num_samples)
            dimensions = f"{width}x{height}"
            return client.predict(
                prompt,
                negative_prompt or "",
                steps,
                guidance or 7.0,
                dimensions,
                1,  # num_samples
                api_name="/generate"
            )

        result = await asyncio.wait_for(
            loop.run_in_executor(None, _call_space),
            timeout=180
        )
        return self._process_gradio_result(result, space_name)

    def _process_gradio_result(self, result: Any, space_name: str) -> str:
        """Process Gradio result and save image to disk"""
        image_path = None

        # Handle different result formats
        if isinstance(result, tuple):
            # Format: (image_path, seed) or (gallery, seed)
            if len(result) >= 1:
                first_item = result[0]
                seed_used = result[1] if len(result) > 1 else None
                logger.info(f">>> {space_name} seed used: {seed_used}")

                if isinstance(first_item, list) and len(first_item) > 0:
                    # Gallery format
                    gallery_item = first_item[0]
                    if isinstance(gallery_item, dict):
                        image_data = gallery_item.get('image', {})
                        if isinstance(image_data, dict):
                            image_path = image_data.get('path')
                        elif isinstance(image_data, str):
                            image_path = image_data
                    elif isinstance(gallery_item, str):
                        image_path = gallery_item
                elif isinstance(first_item, str):
                    # Direct path
                    image_path = first_item
                elif isinstance(first_item, dict):
                    # Dict with path
                    image_path = first_item.get('path') or first_item.get('image')
        elif isinstance(result, str):
            # Direct path string
            image_path = result
        elif isinstance(result, dict):
            # Dict result
            image_path = result.get('path') or result.get('image')

        if not image_path:
            logger.error(f"[{space_name}] Failed to extract image path from result: {type(result)}")
            raise Exception(f"No valid image in result from {space_name}: {type(result)}")

        if not os.path.exists(image_path):
            logger.error(f"[{space_name}] Image file does not exist: {image_path}")
            raise Exception(f"Image file not found from {space_name}: {image_path}")

        # Copy to our images folder
        ext = os.path.splitext(image_path)[1] or ".png"
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
        filepath = os.path.join(self.images_dir, filename)
        shutil.copy(image_path, filepath)

        file_size = os.path.getsize(filepath)
        logger.info(f">>> {space_name} SUCCESS: {filename} ({file_size} bytes)")

        return filename

    def _enhance_prompt(self, prompt: str, nsfw_level: int, style: str) -> str:
        """
        Enhance prompt for better image generation.

        NO HARDCODED KEYWORD DETECTION - the NSFW level is determined by the
        multi-agent LLM system which understands context in any language.
        """
        prompt_lower = prompt.lower()

        # Quality prefix based on style
        if style == "anime":
            quality = "masterpiece, best quality, anime style, detailed illustration"
        else:
            quality = "masterpiece, best quality, ultra realistic, photorealistic, RAW photo, 8k uhd"

        # NSFW tags based on level (determined by multi-agent system, not hardcoded keywords)
        if nsfw_level >= 4:
            nsfw_tags = "nsfw, explicit, nude, naked, uncensored, fully nude, bare skin, exposed body"
            # Ensure nudity is explicit in prompt
            if "nude" not in prompt_lower and "naked" not in prompt_lower:
                prompt = f"completely nude, naked body, bare breasts, nipples visible, {prompt}"
        elif nsfw_level >= 3:
            nsfw_tags = "nsfw, nude, topless, bare breasts, uncensored"
            if "nude" not in prompt_lower and "topless" not in prompt_lower:
                prompt = f"topless, bare breasts, {prompt}"
        elif nsfw_level >= 2:
            nsfw_tags = "nsfw, revealing, sexy, sensual"
        elif nsfw_level >= 1:
            nsfw_tags = "sexy, seductive, sensual"
        else:
            nsfw_tags = ""

        parts = [quality]
        if nsfw_tags:
            parts.append(nsfw_tags)
        parts.append(prompt)
        parts.append("detailed skin texture, professional lighting, sharp focus")

        return ", ".join(parts)

    def build_prompt(
        self,
        character: Dict[str, Any],
        pose: Optional[str] = None,
        location: Optional[str] = None,
        outfit: Optional[str] = None,
        custom: Optional[str] = None,
        nsfw_level: int = 0
    ) -> str:
        """Build optimized prompt from character attributes"""
        parts = ["1girl, solo, single woman"]

        # Ethnicity
        ethnicity = (character.get("ethnicity") or "").lower()
        ethnicity_map = {
            "caucasian": "caucasian european woman, white skin",
            "asian": "asian woman, asian features",
            "latina": "latina hispanic woman, tan skin",
            "african": "african black woman, dark skin",
            "indian": "indian south asian woman, brown skin",
            "arab": "arab middle eastern woman, olive skin",
            "mixed": "mixed race woman, exotic features"
        }
        if ethnicity in ethnicity_map:
            parts.append(ethnicity_map[ethnicity])

        # Age
        age = character.get("age_range", "25-30")
        if age:
            parts.append(f"{age} years old")

        # Body
        body_type = (character.get("body_type") or "").lower()
        body_map = {
            "curvy": "curvy voluptuous body, wide hips, hourglass figure",
            "slim": "slim slender body, thin waist",
            "athletic": "athletic toned body, fit physique",
            "petite": "petite small frame, delicate body",
            "thick": "thick body, wide hips, curvy figure"
        }
        if body_type in body_map:
            parts.append(body_map[body_type])

        # Breasts
        breast_size = (character.get("breast_size") or "").lower()
        breast_map = {
            "small": "small perky breasts, A cup",
            "medium": "medium breasts, B cup, natural",
            "large": "large breasts, D cup, big natural",
            "very large": "huge breasts, massive bust, F cup"
        }
        if breast_size in breast_map:
            parts.append(breast_map[breast_size])

        # Butt
        butt_size = (character.get("butt_size") or "").lower()
        butt_map = {
            "small": "small tight butt",
            "medium": "round butt, shapely",
            "round": "round plump butt, bubble butt",
            "large": "big round ass, wide hips"
        }
        if butt_size in butt_map:
            parts.append(butt_map[butt_size])

        # Hair & Eyes
        hair_color = character.get("hair_color", "brown")
        hair_length = character.get("hair_length", "long")
        eye_color = character.get("eye_color", "brown")
        parts.append(f"{hair_length} {hair_color} hair")
        parts.append(f"beautiful {eye_color} eyes")
        parts.append("beautiful face, detailed features")

        # Outfit
        if outfit:
            parts.append(outfit)
        elif nsfw_level >= 3:
            parts.append("completely nude, naked, bare breasts, nipples visible")
        elif nsfw_level >= 2:
            parts.append("nude, topless, bare breasts")
        elif nsfw_level >= 1:
            parts.append("sexy lingerie, lace bra, panties")
        else:
            parts.append("attractive clothing")

        # Pose
        if pose:
            parts.append(pose)
        elif nsfw_level >= 2:
            parts.append("seductive pose, bedroom eyes, looking at viewer")
        else:
            parts.append("natural pose, looking at viewer")

        # Location
        if location:
            parts.append(f"{location}")
        else:
            parts.append("soft lighting")

        if custom:
            parts.append(custom)

        return ", ".join(parts)

    def build_negative_prompt(self, style: str = "realistic", nsfw_level: int = 0) -> str:
        """Negative prompt (not used by Heartsync but kept for compatibility)"""
        return ""

    def get_character_seed(self, character_id: int) -> int:
        return (character_id * 12345) % 2147483647

    def get_image_path(self, filename: str) -> str:
        return os.path.join(self.images_dir, filename)

    def delete_image(self, filename: str) -> bool:
        filepath = os.path.join(self.images_dir, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False

    def list_images(self) -> list:
        if not os.path.exists(self.images_dir):
            return []
        return [f for f in os.listdir(self.images_dir)
                if f.endswith(('.png', '.jpg', '.jpeg', '.webp'))]

    async def generate_multiple(
        self,
        prompt: str,
        count: int = 1,
        style: str = "realistic",
        seed: Optional[int] = None,
        **kwargs
    ) -> list:
        tasks = []
        for i in range(min(count, 4)):
            img_seed = (seed + i * 1000) if seed is not None else None
            tasks.append(self.generate(prompt, style=style, seed=img_seed, **kwargs))
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def generate_with_agents(
        self,
        user_message: str,
        character_data: Dict[str, Any],
        relationship_level: int = 0,
        current_mood: str = "neutral",
        conversation_context: str = "",
        style: str = "realistic",
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate an image using the multi-agent prompt system + Heartsync/Adult"""

        if not AGENTS_AVAILABLE:
            logger.info("Agents not available, using basic prompt")
            basic_prompt = self.build_prompt(
                character=character_data,
                custom=user_message,
                nsfw_level=0
            )
            filename = await self.generate(
                prompt=basic_prompt,
                style=style,
                width=width,
                height=height,
                seed=seed,
                nsfw_level=0
            )
            return {
                "image_url": filename,
                "prompt_used": basic_prompt,
                "nsfw_level": 0,
                "metadata": {"fallback": True}
            }

        try:
            logger.info("Using multi-agent prompt system...")
            prompt_result = await generate_image_prompt(
                user_message=user_message,
                character_data=character_data,
                relationship_level=relationship_level,
                current_mood=current_mood,
                conversation_context=conversation_context,
                style=style
            )

            logger.info(f"Agent prompt: {prompt_result['prompt'][:100]}...")
            logger.info(f"NSFW level: {prompt_result['nsfw_level']}")

            filename = await self.generate(
                prompt=prompt_result["prompt"],
                style=style,
                width=width,
                height=height,
                seed=seed,
                nsfw_level=prompt_result["nsfw_level"]
            )

            return {
                "image_url": filename,
                "prompt_used": prompt_result["prompt"],
                "nsfw_level": prompt_result["nsfw_level"],
                "is_nsfw": prompt_result["is_nsfw"],
                "metadata": prompt_result.get("metadata", {})
            }

        except Exception as e:
            logger.error(f"Agent error: {e}")
            raise


# Global instance
image_service = ImageService()
