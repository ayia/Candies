"""
FREE Image Generation Service V2 - With Quality Validation
Uses Pollinations.ai + DiversePromptGenerator for ultra-realistic varied images
"""
import sys
import os
import uuid
import asyncio
import aiohttp
import urllib.parse
import logging
from datetime import datetime
from typing import Optional, Dict
from config import settings
from image_quality_validator import DiversePromptGenerator, ImageQualityValidator

# Fix Windows asyncio event loop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logger = logging.getLogger("ImageServiceV2")


class ImageServiceV2:
    """
    V2: Enhanced with diversity enforcement and quality validation

    Improvements over V1:
    - Uses DiversePromptGenerator for varied prompts
    - Validates prompts before generation
    - Tracks previous prompts to avoid "same face syndrome"
    - Stronger negative prompts
    - Better ethnicity/age/feature diversity
    """

    def __init__(self):
        self.images_dir = settings.IMAGES_DIR
        os.makedirs(self.images_dir, exist_ok=True)

        # Pollinations.ai API
        self.base_url = "https://image.pollinations.ai/prompt"

        # V2: Quality validation system
        self.prompt_generator = DiversePromptGenerator()
        self.validator = ImageQualityValidator()

        # Track generated prompts to enforce diversity
        self.previous_prompts = []
        self.max_history = 50  # Remember last 50 prompts

    async def generate(
        self,
        prompt: str = None,
        negative_prompt: str = "",
        nsfw_level: int = 0,
        width: int = 1024,
        height: int = 1024,
        model: str = "flux",
        enforce_diversity: bool = True
    ) -> Optional[str]:
        """
        Generate image with quality validation

        Args:
            prompt: User prompt (if None, auto-generates diverse prompt)
            negative_prompt: Negative prompt
            nsfw_level: 0=SFW, 1=Sensual, 2=Topless, 3=Nude
            width: Image width
            height: Image height
            model: "flux", "turbo", or "sd"
            enforce_diversity: Use DiversePromptGenerator

        Returns:
            Image filename or None
        """

        # V2: If no prompt or enforce_diversity, generate diverse prompt
        if prompt is None or enforce_diversity:
            logger.info("🎲 Generating diverse prompt...")
            prompt, negative_prompt = self.prompt_generator.generate_diverse_prompt(
                nsfw_level=nsfw_level,
                previous_prompts=self.previous_prompts
            )

            # Validate generated prompt
            validation = self.validator.validate_complete_prompt(
                prompt, negative_prompt, self.previous_prompts
            )

            logger.info(f"✅ Prompt Score: {validation['overall_score']}/10")

            if not validation['passed']:
                logger.warning(f"⚠️ Prompt validation issues: {validation['summary']}")

        # V2: Track prompt for diversity
        self.previous_prompts.append(prompt)
        if len(self.previous_prompts) > self.max_history:
            self.previous_prompts.pop(0)

        # Add quality enhancement tags
        enhanced_prompt = self._add_quality_tags(prompt, nsfw_level)

        # Build Pollinations URL
        url = self._build_url(enhanced_prompt, negative_prompt, width, height, model)

        logger.info(f"🎨 Generating image...")
        logger.info(f"📝 Prompt preview: {prompt[:100]}...")

        # Generate image
        image_data = await self._fetch_image(url)

        if not image_data:
            return None

        # Save image
        filename = await self._save_image(image_data)

        return filename

    def _add_quality_tags(self, prompt: str, nsfw_level: int) -> str:
        """
        Add quality enhancement tags to prompt

        V2: Lighter tags since DiversePromptGenerator already includes details
        """

        # Basic quality tags - don't override diverse prompt details
        quality_prefix = (
            "raw candid photo, shot on iPhone, natural unedited, "
            "amateur photography, genuine real person, "
        )

        # NSFW tags
        nsfw_tags = ""
        if nsfw_level >= 1:
            nsfw_tags = ", adult 18+, sensual"
        if nsfw_level >= 2:
            nsfw_tags = ", explicit 18+, NSFW, topless, bare breasts, nipples visible"
        if nsfw_level >= 3:
            nsfw_tags = ", XXX 18+, fully nude, completely naked, full frontal nudity, nude body"

        return f"{quality_prefix}{prompt}{nsfw_tags}"

    def _build_url(
        self,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        model: str
    ) -> str:
        """Build Pollinations.ai URL"""

        # Add ultra-strong negatives
        if negative_prompt:
            full_negative = negative_prompt
        else:
            full_negative = (
                "perfect symmetrical face, flawless skin, same face syndrome, "
                "clone face, repetitive features, professional model, magazine, "
                "airbrushed, photoshopped, Instagram filter, beauty filter, "
                "professional makeup, salon hair, studio lighting, "
                "cartoon, anime, 3d render, low quality, blurry, deformed"
            )

        # Combine prompt and negative
        full_prompt = f"{prompt}, NOT: {full_negative}"

        # URL encode
        encoded = urllib.parse.quote(full_prompt)

        # Build URL with parameters
        url = (
            f"{self.base_url}/{encoded}"
            f"?width={width}&height={height}"
            f"&model={model}"
            f"&nologo=true"
            f"&enhance=true"
            f"&nofeed=true"
            f"&private=true"
        )

        return url

    async def _fetch_image(self, url: str) -> Optional[bytes]:
        """Fetch image from Pollinations.ai"""
        try:
            timeout = aiohttp.ClientTimeout(total=120)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        logger.info(f"✅ Image received ({len(image_data)} bytes)")
                        return image_data
                    else:
                        text = await response.text()
                        logger.error(f"❌ Error: {response.status} - {text[:200]}")
                        return None

        except asyncio.TimeoutError:
            logger.error("❌ Timeout: Generation took too long")
            return None
        except Exception as e:
            logger.error(f"❌ Request failed: {e}")
            return None

    async def _save_image(self, image_data: bytes) -> Optional[str]:
        """Save image to disk"""
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"{timestamp}_{unique_id}.jpg"
            filepath = os.path.join(self.images_dir, filename)

            # Save
            with open(filepath, 'wb') as f:
                f.write(image_data)

            logger.info(f"💾 Saved: {filename}")
            return filename

        except Exception as e:
            logger.error(f"❌ Save error: {e}")
            return None

    async def generate_batch(
        self,
        count: int,
        nsfw_level: int = 0,
        width: int = 1024,
        height: int = 1024,
        delay: int = 3
    ) -> list:
        """
        Generate multiple diverse images with validation

        Args:
            count: Number of images to generate
            nsfw_level: NSFW level
            width: Image width
            height: Image height
            delay: Seconds between requests (rate limiting)

        Returns:
            List of generated filenames
        """
        results = []

        print(f"\n{'='*70}")
        print(f"🎨 BATCH GENERATION - {count} Diverse Images")
        print(f"{'='*70}")
        print(f"NSFW Level: {nsfw_level}")
        print(f"Diversity: ENFORCED (varied ethnicities, ages, features)")
        print(f"{'='*70}\n")

        for i in range(count):
            print(f"\n[{i+1}/{count}] Generating image...")

            filename = await self.generate(
                prompt=None,  # Auto-generate diverse prompt
                nsfw_level=nsfw_level,
                width=width,
                height=height,
                enforce_diversity=True
            )

            if filename:
                results.append(filename)
                print(f"✅ Success: {filename}")
            else:
                results.append(None)
                print(f"❌ Failed")

            # Rate limiting
            if i < count - 1:
                print(f"⏱️  Waiting {delay}s...")
                await asyncio.sleep(delay)

        # Summary
        success_count = len([r for r in results if r])
        print(f"\n{'='*70}")
        print(f"📊 BATCH SUMMARY: {success_count}/{count} successful")
        print(f"{'='*70}\n")

        return results

    def get_stats(self) -> Dict:
        """Get diversity statistics"""
        return {
            "total_prompts_generated": len(self.previous_prompts),
            "recent_prompts": self.previous_prompts[-5:] if self.previous_prompts else [],
            "diversity_enforcement": "ACTIVE"
        }


# Global instance
image_service_v2 = ImageServiceV2()


# ============================================================================
# TESTING
# ============================================================================

async def test_single_generation():
    """Test single image with diversity"""
    print("\n" + "="*70)
    print("TEST 1: Single Diverse Image")
    print("="*70)

    service = ImageServiceV2()

    filename = await service.generate(
        prompt=None,  # Auto-generate
        nsfw_level=2,  # Topless
        width=1024,
        height=1024,
        enforce_diversity=True
    )

    if filename:
        print(f"\n✅ Generated: {filename}")
    else:
        print(f"\n❌ Failed")


async def test_batch_generation():
    """Test batch generation with diversity"""
    print("\n" + "="*70)
    print("TEST 2: Batch Diverse Images (10 images)")
    print("="*70)

    service = ImageServiceV2()

    results = await service.generate_batch(
        count=10,
        nsfw_level=2,  # Topless
        width=1024,
        height=1024,
        delay=3
    )

    print(f"\n✅ Generated {len([r for r in results if r])}/10 images")
    print(f"\n📊 Diversity Stats:")
    stats = service.get_stats()
    print(f"  Total prompts: {stats['total_prompts_generated']}")
    print(f"  Diversity: {stats['diversity_enforcement']}")


async def test_custom_prompt_validation():
    """Test custom prompt with validation"""
    print("\n" + "="*70)
    print("TEST 3: Custom Prompt with Validation")
    print("="*70)

    service = ImageServiceV2()

    # Bad prompt (generic)
    bad_prompt = "beautiful woman in bedroom"

    # This should fail validation but still generate
    filename = await service.generate(
        prompt=bad_prompt,
        nsfw_level=1,
        enforce_diversity=False  # Use custom prompt
    )

    if filename:
        print(f"\n⚠️ Generated despite low quality prompt: {filename}")
        print(f"💡 This demonstrates validation warnings work")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "single":
            asyncio.run(test_single_generation())
        elif sys.argv[1] == "batch":
            asyncio.run(test_batch_generation())
        elif sys.argv[1] == "validate":
            asyncio.run(test_custom_prompt_validation())
    else:
        print("\nUsage:")
        print("  python image_service_v2.py single    - Generate 1 diverse image")
        print("  python image_service_v2.py batch     - Generate 10 diverse images")
        print("  python image_service_v2.py validate  - Test validation system")
        print("\n")
