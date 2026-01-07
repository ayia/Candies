"""Image Generation Service v9.0 - Heartsync/Adult EXCLUSIVE"""
import os
import uuid
import asyncio
import shutil
import sys
import io
import logging
from datetime import datetime
from typing import Optional, Dict, Any
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


class ImageService:
    """
    Image Service v9.0 - Heartsync/Adult EXCLUSIVE

    Uses ONLY Heartsync/Adult Space on HuggingFace.
    No fallback - Heartsync/Adult or nothing.

    Heartsync/Adult API:
    - Endpoint: /generate_image
    - Parameters: prompt, height, width, num_inference_steps, seed, randomize_seed, num_images
    - Returns: Gallery of images + seed used
    """

    def __init__(self):
        self.token = settings.HF_API_TOKEN
        self.images_dir = settings.IMAGES_DIR
        os.makedirs(self.images_dir, exist_ok=True)

        # Heartsync/Adult Space - EXCLUSIVE
        self.space_name = "Heartsync/Adult"
        self.api_endpoint = "/generate_image"

        # Quality settings
        self.default_steps = 18  # Heartsync default
        self.default_width = 1024
        self.default_height = 1024

        logger.info("=" * 50)
        logger.info("v9.0 - Heartsync/Adult EXCLUSIVE")
        logger.info(f"Space: {self.space_name}")
        logger.info(f"Endpoint: {self.api_endpoint}")
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
        """Generate an image using Heartsync/Adult EXCLUSIVELY"""

        # Enhance prompt
        enhanced_prompt = self._enhance_prompt(prompt, nsfw_level, style)

        # Clamp dimensions (Heartsync supports 512-2048)
        width = max(512, min(2048, width))
        height = max(512, min(2048, height))
        num_steps = steps or self.default_steps

        logger.info("=" * 50)
        logger.info("Heartsync/Adult - Generation Starting")
        logger.info(f"NSFW Level: {nsfw_level}")
        logger.info(f"Size: {width}x{height}, Steps: {num_steps}")
        logger.info(f"Prompt: {enhanced_prompt[:100]}...")
        logger.info("=" * 50)

        try:
            result = await self._generate_heartsync(
                prompt=enhanced_prompt,
                width=width,
                height=height,
                steps=num_steps,
                seed=seed
            )
            logger.info(f">>> SUCCESS with Heartsync/Adult")
            return result
        except Exception as e:
            error_msg = str(e)
            logger.error(f">>> Heartsync/Adult failed: {error_msg}")
            raise Exception(f"Heartsync/Adult generation failed: {error_msg}")

    async def _generate_heartsync(
        self,
        prompt: str,
        width: int,
        height: int,
        steps: int,
        seed: Optional[int]
    ) -> str:
        """Generate with Heartsync/Adult Space"""
        loop = asyncio.get_event_loop()

        def _call_space():
            # Suppress Gradio output
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()
            try:
                client = GradioClient(self.space_name)
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

            # Heartsync/Adult API:
            # predict(prompt, height, width, num_inference_steps, seed, randomize_seed, num_images, api_name="/generate_image")
            # Returns: (_generated_images, seed_used)
            return client.predict(
                prompt,                      # prompt (str, required)
                height,                      # height (float, default: 1024)
                width,                       # width (float, default: 1024)
                steps,                       # num_inference_steps (float, default: 18)
                seed if seed else 42,        # seed (float, default: 42)
                seed is None,                # randomize_seed (bool, default: True)
                1,                           # num_images (float, default: 2) - we only need 1
                api_name=self.api_endpoint
            )

        result = await asyncio.wait_for(
            loop.run_in_executor(None, _call_space),
            timeout=180
        )

        # Parse result: (_generated_images, seed_used)
        # _generated_images is a Gallery: list of dicts with 'image' key
        image_path = None

        if isinstance(result, tuple) and len(result) >= 1:
            gallery = result[0]
            seed_used = result[1] if len(result) > 1 else None
            logger.info(f">>> Seed used: {seed_used}")

            if isinstance(gallery, list) and len(gallery) > 0:
                first = gallery[0]
                if isinstance(first, dict):
                    # Gallery format: {'image': {'path': '...', 'url': '...', ...}, 'caption': None}
                    image_data = first.get('image', {})
                    if isinstance(image_data, dict):
                        image_path = image_data.get('path')
                    elif isinstance(image_data, str):
                        image_path = image_data
                elif isinstance(first, str):
                    image_path = first

        if not image_path:
            logger.error(f"Failed to extract image path from result: {type(result)}")
            raise Exception(f"No valid image in result: {type(result)}")

        if not os.path.exists(image_path):
            logger.error(f"Image file does not exist: {image_path}")
            raise Exception(f"Image file not found: {image_path}")

        # Copy to our images folder
        ext = os.path.splitext(image_path)[1] or ".png"
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
        filepath = os.path.join(self.images_dir, filename)
        shutil.copy(image_path, filepath)

        file_size = os.path.getsize(filepath)
        logger.info(f">>> Heartsync/Adult SUCCESS: {filename} ({file_size} bytes)")

        return filename

    def _enhance_prompt(self, prompt: str, nsfw_level: int, style: str) -> str:
        """Enhance prompt for better image generation"""
        prompt_lower = prompt.lower()

        # Quality prefix
        if style == "anime":
            quality = "masterpiece, best quality, anime style, detailed illustration"
        else:
            quality = "masterpiece, best quality, ultra realistic, photorealistic, RAW photo, 8k uhd"

        # Sexual acts enhancement
        sexual_acts = {
            "blowjob": "woman performing oral sex, blowjob, fellatio, sucking cock, penis in mouth",
            "sucer": "woman performing oral sex, blowjob, fellatio, sucking cock",
            "fellation": "woman giving oral sex, blowjob, fellatio, deepthroat",
            "sex": "couple having sex, sexual intercourse, penetration",
            "doggy": "doggy style position, rear entry, woman on all fours, from behind",
            "levrette": "doggy style, rear entry sex, bent over",
            "cowgirl": "cowgirl position, woman on top, riding",
            "anal": "anal sex, anal penetration",
            "masturbation": "woman masturbating, touching herself, fingering",
            "cunnilingus": "cunnilingus, oral sex on woman, licking"
        }

        for keyword, enhancement in sexual_acts.items():
            if keyword in prompt_lower:
                prompt = f"{enhancement}, {prompt}"
                nsfw_level = max(nsfw_level, 3)
                break

        # NSFW tags
        if nsfw_level >= 3:
            nsfw_tags = "nsfw, explicit, nude, naked, uncensored, fully nude, bare skin"
            if "nude" not in prompt_lower:
                prompt = f"{prompt}, completely nude, naked body, bare breasts, nipples visible"
        elif nsfw_level >= 2:
            nsfw_tags = "nsfw, nude, topless, bare breasts, uncensored"
            if "nude" not in prompt_lower:
                prompt = f"{prompt}, nude, topless"
        elif nsfw_level >= 1:
            nsfw_tags = "nsfw, sexy, seductive, sensual"
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
