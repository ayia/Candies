"""Image Generation Service v7.0 - Z-Image-Turbo with Multi-Agent Prompt System"""
import os
import uuid
import asyncio
import shutil
import requests
import urllib.parse
from datetime import datetime
from typing import Optional, Dict, Any
from huggingface_hub import InferenceClient
from gradio_client import Client as GradioClient
from config import settings


# Import multi-agent prompt system
try:
    from services.image_prompt_agents import generate_image_prompt, image_prompt_orchestrator
    AGENTS_AVAILABLE = True
    print("[ImageService] Multi-agent prompt system loaded")
except ImportError as e:
    AGENTS_AVAILABLE = False
    print(f"[ImageService] Multi-agent system not available: {e}")


class ImageService:
    """
    Image Service v7.0 - Hybrid Approach with Multi-Agent Prompt System

    Strategy:
    1. Multi-agent system generates optimized prompts based on:
       - User intention analysis
       - Character personality and physical traits
       - Relationship level and emotional context
       - NSFW modulation
    2. Z-Image-Turbo via fal-ai for SFW content (fast, high quality)
    3. NSFW Z-Image-Turbo Spaces for explicit content
    4. Pollinations as final fallback

    Z-Image-Turbo benefits:
    - #1 open-source model on Artificial Analysis leaderboard
    - Excellent photorealistic quality
    - Works with detailed prompts
    - 8 steps only (very fast)
    """

    def __init__(self):
        self.token = settings.HF_API_TOKEN
        self.images_dir = settings.IMAGES_DIR
        os.makedirs(self.images_dir, exist_ok=True)

        # Z-Image-Turbo via fal-ai (SFW only - they filter NSFW)
        self.fal_client = InferenceClient(
            provider="fal-ai",
            api_key=self.token
        )
        self.z_image_model = "Tongyi-MAI/Z-Image-Turbo"

        # NSFW Spaces using Z-Image-Turbo (try in order)
        self.nsfw_spaces = [
            {
                "name": "yingzhac/Z_image_NSFW",
                "api_name": "/generate_image",
                "max_size": 2048,
                "params": ["prompt", "negative", "height", "width", "steps", "guidance", "seed", "randomize"]
            },
            {
                "name": "ClickyGPT/NSFW_Z-Image-Turbo",
                "api_name": "/infer",
                "max_size": 1024,
                "params": ["prompt", "negative", "seed", "randomize", "width", "height", "guidance", "steps"]
            }
        ]

        # Quality settings
        self.default_steps = 8
        self.default_width = 1024
        self.default_height = 1024

        print(f"[ImageService] v6.0 Initialized - Z-Image-Turbo Hybrid")
        print(f"[ImageService] SFW: fal-ai provider")
        print(f"[ImageService] NSFW: {len(self.nsfw_spaces)} fallback spaces")

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
        """Generate an image with intelligent provider selection"""

        # Detect NSFW content
        nsfw_keywords = ["nude", "naked", "topless", "nsfw", "xxx", "porn", "sex",
                        "breast", "nipple", "pussy", "cock", "dick", "ass",
                        "blowjob", "fellation", "sucer", "levrette", "doggy",
                        "explicit", "uncensored", "bare"]
        prompt_lower = prompt.lower()
        is_nsfw = nsfw or nsfw_level >= 1 or any(kw in prompt_lower for kw in nsfw_keywords)

        # Enhance prompt
        enhanced_prompt = self._enhance_prompt(prompt, nsfw_level, style)

        # Clamp dimensions
        width = max(512, min(2048, width))
        height = max(512, min(2048, height))
        num_steps = steps or self.default_steps

        print(f"[ImageService] NSFW: {is_nsfw}, Level: {nsfw_level}")
        print(f"[ImageService] Prompt: {enhanced_prompt[:80]}...")

        errors = []

        if is_nsfw:
            # NSFW: Try Z-Image-Turbo NSFW Spaces first
            for space in self.nsfw_spaces:
                try:
                    print(f"[ImageService] Trying {space['name']}...")
                    result = await self._generate_nsfw_space(
                        space=space,
                        prompt=enhanced_prompt,
                        width=min(width, space["max_size"]),
                        height=min(height, space["max_size"]),
                        steps=num_steps,
                        seed=seed
                    )
                    print(f"[ImageService] Success with {space['name']}")
                    return result
                except Exception as e:
                    errors.append(f"{space['name']}: {e}")
                    print(f"[ImageService] {space['name']} failed: {e}")

            # Fallback to Pollinations for NSFW
            print("[ImageService] Trying Pollinations fallback...")
            try:
                return await self._generate_pollinations(enhanced_prompt, width, height, seed)
            except Exception as e:
                errors.append(f"Pollinations: {e}")

            raise Exception(f"All NSFW providers failed: {'; '.join(errors)}")

        else:
            # SFW: Use Z-Image-Turbo via fal-ai
            try:
                print("[ImageService] Using Z-Image-Turbo via fal-ai (SFW)...")
                return await self._generate_fal_ai(enhanced_prompt, width, height, num_steps, seed)
            except Exception as e:
                errors.append(f"fal-ai: {e}")
                print(f"[ImageService] fal-ai failed: {e}")

                # Fallback to Pollinations for SFW too
                try:
                    return await self._generate_pollinations(enhanced_prompt, width, height, seed)
                except Exception as e2:
                    errors.append(f"Pollinations: {e2}")

                raise Exception(f"All providers failed: {'; '.join(errors)}")

    async def _generate_fal_ai(
        self,
        prompt: str,
        width: int,
        height: int,
        steps: int,
        seed: Optional[int]
    ) -> str:
        """Generate with Z-Image-Turbo via fal-ai (SFW only)"""
        loop = asyncio.get_event_loop()

        def _generate():
            return self.fal_client.text_to_image(
                prompt=prompt,
                model=self.z_image_model,
                width=width,
                height=height,
                num_inference_steps=steps,
                seed=seed
            )

        image = await asyncio.wait_for(
            loop.run_in_executor(None, _generate),
            timeout=120
        )

        # Verify it's not a black/blocked image
        if hasattr(image, 'size'):
            # Check if image is mostly black (blocked)
            import io
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            if buffer.tell() < 10000:  # Less than 10KB = probably blocked
                raise Exception("Image blocked by content filter")

        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(self.images_dir, filename)
        image.save(filepath, "PNG")

        file_size = os.path.getsize(filepath)
        print(f"[ImageService] fal-ai success: {filename} ({file_size} bytes)")

        return filename

    async def _generate_nsfw_space(
        self,
        space: Dict,
        prompt: str,
        width: int,
        height: int,
        steps: int,
        seed: Optional[int]
    ) -> str:
        """Generate with NSFW Z-Image-Turbo Space"""
        loop = asyncio.get_event_loop()

        def _call_space():
            import sys
            import io
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            try:
                client = GradioClient(space["name"])
            finally:
                sys.stdout = old_stdout

            api_name = space["api_name"]
            params = space["params"]

            # Build arguments based on space parameter order
            if params[0] == "prompt":
                if space["name"] == "yingzhac/Z_image_NSFW":
                    # yingzhac: prompt, negative, height, width, steps, guidance, seed, randomize
                    return client.predict(
                        prompt,
                        "",  # negative prompt (not used by Z-Image)
                        height,
                        width,
                        steps,
                        0.0,  # guidance (0 for turbo)
                        seed if seed else 42,
                        seed is None,  # randomize
                        api_name=api_name
                    )
                else:
                    # ClickyGPT: prompt, negative, seed, randomize, width, height, guidance, steps
                    return client.predict(
                        prompt,
                        "",
                        seed if seed else 42,
                        seed is None,
                        width,
                        height,
                        0.0,
                        steps,
                        api_name=api_name
                    )

        result = await asyncio.wait_for(
            loop.run_in_executor(None, _call_space),
            timeout=180
        )

        # Parse result
        image_path = None
        if isinstance(result, tuple):
            gallery = result[0]
            if isinstance(gallery, list) and len(gallery) > 0:
                first = gallery[0]
                if isinstance(first, dict):
                    image_path = first.get('image') or first.get('path')
                elif isinstance(first, str):
                    image_path = first
            elif isinstance(result[0], str):
                image_path = result[0]
        elif isinstance(result, str):
            image_path = result

        if not image_path or not os.path.exists(image_path):
            raise Exception(f"No valid image in result: {type(result)}")

        # Copy to our images folder
        ext = os.path.splitext(image_path)[1] or ".png"
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
        filepath = os.path.join(self.images_dir, filename)
        shutil.copy(image_path, filepath)

        file_size = os.path.getsize(filepath)
        print(f"[ImageService] Space success: {filename} ({file_size} bytes)")

        return filename

    async def _generate_pollinations(
        self,
        prompt: str,
        width: int,
        height: int,
        seed: Optional[int]
    ) -> str:
        """Generate with Pollinations.ai (free, supports NSFW)"""
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        params = [f"width={width}", f"height={height}", "nologo=true", "model=flux"]
        if seed is not None:
            params.append(f"seed={seed}")
        url += "?" + "&".join(params)

        loop = asyncio.get_event_loop()

        def _fetch():
            response = requests.get(url, timeout=180)
            if response.status_code == 200:
                # Return both content and content-type
                content_type = response.headers.get('Content-Type', 'image/jpeg')
                return response.content, content_type
            raise Exception(f"HTTP {response.status_code}")

        image_data, content_type = await asyncio.wait_for(
            loop.run_in_executor(None, _fetch),
            timeout=180
        )

        # Determine correct extension from content-type
        if 'jpeg' in content_type or 'jpg' in content_type:
            ext = '.jpg'
        elif 'webp' in content_type:
            ext = '.webp'
        elif 'gif' in content_type:
            ext = '.gif'
        else:
            ext = '.png'

        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
        filepath = os.path.join(self.images_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(image_data)

        file_size = os.path.getsize(filepath)
        if file_size < 5000:
            os.remove(filepath)
            raise Exception(f"Image too small ({file_size} bytes)")

        print(f"[ImageService] Pollinations success: {filename} ({file_size} bytes)")
        return filename

    def _enhance_prompt(self, prompt: str, nsfw_level: int, style: str) -> str:
        """Enhance prompt for Z-Image-Turbo"""
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
        """Z-Image-Turbo doesn't use negative prompts"""
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
        """
        Generate an image using the multi-agent prompt system.

        This is the recommended method for generating character images as it:
        1. Analyzes user intention to understand what they want
        2. Builds character-specific context from their attributes
        3. Engineers an optimized prompt for the image model
        4. Moderates content based on relationship level
        5. Validates and refines the final prompt

        Args:
            user_message: The user's message requesting an image
            character_data: Dict with character info (name, physical_traits, personality, etc.)
            relationship_level: 0-10 relationship level
            current_mood: Character's current emotional state
            conversation_context: Recent conversation for context
            style: "realistic" or "anime"
            width: Image width (512-2048)
            height: Image height (512-2048)
            seed: Optional seed for reproducibility

        Returns:
            Dict with:
            - image_url: Generated image filename
            - prompt_used: The prompt that was generated
            - nsfw_level: Final NSFW level (0-5)
            - metadata: Additional info about the generation
        """
        if not AGENTS_AVAILABLE:
            # Fallback to basic prompt building
            print("[ImageService] Agents not available, using basic prompt")
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
                nsfw=False,
                nsfw_level=0
            )
            return {
                "image_url": filename,
                "prompt_used": basic_prompt,
                "nsfw_level": 0,
                "metadata": {"fallback": True}
            }

        try:
            # Use multi-agent system to generate optimized prompt
            print("[ImageService] Using multi-agent prompt system...")
            prompt_result = await generate_image_prompt(
                user_message=user_message,
                character_data=character_data,
                relationship_level=relationship_level,
                current_mood=current_mood,
                conversation_context=conversation_context,
                style=style
            )

            print(f"[ImageService] Agent-generated prompt: {prompt_result['prompt'][:100]}...")
            print(f"[ImageService] NSFW level: {prompt_result['nsfw_level']}")

            # Generate image with the optimized prompt
            filename = await self.generate(
                prompt=prompt_result["prompt"],
                style=style,
                negative_prompt=prompt_result.get("negative_prompt", ""),
                width=width,
                height=height,
                seed=seed,
                nsfw=prompt_result["is_nsfw"],
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
            print(f"[ImageService] Agent error, falling back to basic: {e}")
            # Fallback to basic prompt
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
                nsfw=False,
                nsfw_level=0
            )
            return {
                "image_url": filename,
                "prompt_used": basic_prompt,
                "nsfw_level": 0,
                "metadata": {"fallback": True, "error": str(e)}
            }


# Global instance
image_service = ImageService()
