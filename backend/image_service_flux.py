"""
FLUX Schnell - Ultra Photorealistic Image Generation
Best free photorealistic model from Black Forest Labs via Together.ai

Quality: ⭐⭐⭐⭐⭐ (Midjourney level)
Free Tier: 3 months, 6 images/minute
NSFW: Supported (no safety checker by default)
"""
import sys
import io
import os
import uuid
import asyncio
import aiohttp
import base64
import logging
from datetime import datetime
from typing import Optional
from config import settings

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Fix Windows asyncio event loop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logger = logging.getLogger("FluxImageService")


class FluxImageService:
    """
    FLUX.1 [schnell] - Ultra Photorealistic Image Generation

    Advantages:
    - ⭐⭐⭐⭐⭐ Midjourney-level quality
    - 100% photorealistic (indistinguishable from real photos)
    - Free for 3 months via Together.ai
    - 6 images/minute rate limit
    - NSFW supported
    - By Black Forest Labs (ex-Stability AI team)

    API: https://api.together.xyz/v1/images/generations
    Model: black-forest-labs/FLUX.1-schnell-Free
    """

    def __init__(self):
        # Together.ai API key (free tier: 3 months)
        self.api_key = os.getenv("TOGETHER_API_KEY", settings.HF_API_TOKEN)

        self.api_url = "https://api.together.xyz/v1/images/generations"

        # FLUX Schnell Free model
        self.model = "black-forest-labs/FLUX.1-schnell-Free"

        self.images_dir = settings.IMAGES_DIR
        os.makedirs(self.images_dir, exist_ok=True)

        logger.info("="*60)
        logger.info("🎨 FLUX.1 [schnell] - Ultra Photorealistic")
        logger.info("By Black Forest Labs (ex-Stability AI)")
        logger.info(f"API Key: {'SET (' + self.api_key[:8] + '...)' if self.api_key else 'NOT SET!'}")
        logger.info("Free Tier: 3 months, 6 img/min")
        logger.info("Quality: ⭐⭐⭐⭐⭐ Midjourney-level")
        logger.info("="*60)

    async def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        style: str = "realistic",
        width: int = 1024,
        height: int = 1024,
        nsfw_level: int = 0,
        steps: int = 4  # Schnell = fast, 4 steps is optimal
    ) -> Optional[str]:
        """
        Generate ultra-photorealistic image using FLUX.1 [schnell]

        Args:
            prompt: Main prompt (detailed descriptions work best)
            negative_prompt: What to avoid
            style: "realistic" or "anime"
            width/height: Image dimensions (512-2048, must be multiple of 32)
            nsfw_level: 0-3 (NSFW supported)
            steps: Inference steps (4 recommended for schnell)

        Returns:
            Path to saved image or None
        """

        logger.info("="*60)
        logger.info("🎨 FLUX Schnell Generation")
        logger.info(f"Model: {self.model}")
        logger.info(f"Size: {width}x{height}")
        logger.info(f"Steps: {steps}")
        logger.info(f"NSFW Level: {nsfw_level}")
        logger.info(f"Prompt: {prompt[:100]}...")
        logger.info("="*60)

        # Enhance prompt for maximum photorealism
        enhanced_prompt = self._enhance_prompt_photorealistic(prompt, nsfw_level, style)

        # Build negative prompt
        if not negative_prompt:
            negative_prompt = self._build_negative_prompt(nsfw_level)

        try:
            # Generate image
            image_data = await self._generate_flux(
                enhanced_prompt,
                negative_prompt,
                width,
                height,
                steps
            )

            if image_data:
                # Save image
                image_path = await self._save_image(image_data)
                if image_path:
                    logger.info(f"✅ SUCCESS! Image: {image_path}")
                    return image_path

            logger.error("❌ Generation failed")
            return None

        except Exception as e:
            logger.error(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _generate_flux(
        self,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        steps: int
    ) -> Optional[bytes]:
        """
        Call Together.ai FLUX API

        Docs: https://docs.together.ai/docs/image-models
        """

        if not self.api_key:
            logger.error("❌ No API key set! Set TOGETHER_API_KEY in .env")
            return None

        # Validate dimensions (must be multiple of 32)
        width = (width // 32) * 32
        height = (height // 32) * 32

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "prompt": prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "n": 1,  # Number of images
            "response_format": "b64_json"  # Get base64 instead of URL
        }

        # Add negative prompt if provided
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        try:
            logger.info(f"📡 Calling Together.ai API...")
            logger.info(f"   Endpoint: {self.api_url}")
            logger.info(f"   Model: {self.model}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:

                    logger.info(f"   Status: {response.status}")

                    if response.status == 200:
                        data = await response.json()

                        # Extract base64 image
                        if data.get("data") and len(data["data"]) > 0:
                            b64_image = data["data"][0].get("b64_json")
                            if b64_image:
                                image_data = base64.b64decode(b64_image)
                                logger.info(f"   ✅ Downloaded {len(image_data)} bytes")
                                return image_data

                        logger.error("   ❌ No image in response")
                        return None

                    elif response.status == 401:
                        logger.error("   ❌ Invalid API key!")
                        return None

                    elif response.status == 429:
                        logger.error("   ❌ Rate limit exceeded (6 img/min)")
                        return None

                    else:
                        error_text = await response.text()
                        logger.error(f"   ❌ Error: {error_text[:200]}")
                        return None

        except asyncio.TimeoutError:
            logger.error("❌ Timeout after 60s")
            return None
        except Exception as e:
            logger.error(f"❌ Request failed: {e}")
            return None

    async def _save_image(self, image_data: bytes) -> Optional[str]:
        """Save image data to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"flux_{timestamp}_{unique_id}.png"
            filepath = os.path.join(self.images_dir, filename)

            with open(filepath, 'wb') as f:
                f.write(image_data)

            logger.info(f"💾 Saved: {filename} ({len(image_data)} bytes)")
            return filename

        except Exception as e:
            logger.error(f"❌ Save error: {e}")
            return None

    def _enhance_prompt_photorealistic(self, prompt: str, nsfw_level: int, style: str) -> str:
        """
        Enhance prompt for MAXIMUM photorealism

        FLUX works best with natural language descriptions
        like you're describing a real photograph
        """

        # Photorealistic quality tags
        if style == "realistic":
            quality = (
                "professional photograph, shot on Canon EOS R5, 85mm f/1.4 lens, "
                "natural lighting, 8k uhd, high resolution, photorealistic, "
                "hyperrealistic, ultra detailed, sharp focus, beautiful bokeh, "
                "film grain, cinematic, lifelike"
            )
        else:  # anime
            quality = (
                "high quality anime art, detailed illustration, "
                "vibrant colors, masterpiece, best quality"
            )

        # NSFW tags (for FLUX, be explicit to get better results)
        nsfw_tags = ""
        if nsfw_level >= 1:
            nsfw_tags = ", adult content, mature, sensual"
        if nsfw_level >= 2:
            nsfw_tags = ", adult content, mature, sensual, explicit, nsfw"
        if nsfw_level >= 3:
            nsfw_tags = ", adult content, mature, sensual, explicit, nsfw, uncensored"

        # Combine
        full_prompt = f"{quality}, {prompt}{nsfw_tags}"

        return full_prompt

    def _build_negative_prompt(self, nsfw_level: int) -> str:
        """Build negative prompt for photorealism"""

        base_negative = (
            "cartoon, anime, illustration, 3d render, cgi, painting, drawing, "
            "artificial, fake, plastic, doll, mannequin, "
            "low quality, blurry, bad anatomy, deformed, ugly, distorted, "
            "bad hands, bad fingers, extra fingers, missing fingers, "
            "watermark, signature, text, logo, artist name, username, "
            "oversaturated, overexposed, underexposed, noise"
        )

        # For SFW, add NSFW to negative
        if nsfw_level == 0:
            base_negative += ", nsfw, nude, naked, explicit, sexual"

        return base_negative


# Global instance
flux_image_service = FluxImageService()


# ============================================================
# USAGE EXAMPLES & TESTS
# ============================================================

async def test_photorealistic_portrait():
    """Test ultra-photorealistic portrait"""
    print("\n" + "="*60)
    print("Test 1: Ultra-Photorealistic Portrait")
    print("="*60)

    service = FluxImageService()

    result = await service.generate(
        prompt=(
            "professional headshot of a beautiful 28 year old woman with long brown hair, "
            "green eyes, natural makeup, gentle smile, wearing elegant black blazer, "
            "soft studio lighting, gray background, shallow depth of field"
        ),
        nsfw_level=0,
        width=1024,
        height=1024,
        steps=4
    )

    if result:
        print(f"✅ SUCCESS: {result}")
        print("   Check the image - it should look 100% real!")
    else:
        print("❌ FAILED")

    return result is not None


async def test_nsfw_photorealistic():
    """Test NSFW photorealistic image"""
    print("\n" + "="*60)
    print("Test 2: NSFW Photorealistic")
    print("="*60)

    service = FluxImageService()

    result = await service.generate(
        prompt=(
            "stunning 25 year old woman on tropical beach at sunset, "
            "wearing stylish bikini, sun-kissed tan skin, wind in hair, "
            "confident pose, golden hour lighting, ocean in background, "
            "professional fashion photography"
        ),
        nsfw_level=2,
        width=1024,
        height=1024,
        steps=4
    )

    if result:
        print(f"✅ SUCCESS: {result}")
    else:
        print("❌ FAILED")

    return result is not None


async def test_comparison():
    """Compare with simple prompt"""
    print("\n" + "="*60)
    print("Test 3: Detailed vs Simple Prompt")
    print("="*60)

    service = FluxImageService()

    # Simple prompt
    print("\n📝 Simple prompt: 'beautiful woman'")
    result1 = await service.generate(
        prompt="beautiful woman",
        nsfw_level=0,
        width=512,
        height=512,
        steps=4
    )

    await asyncio.sleep(10)  # Rate limit: 6/min

    # Detailed prompt
    print("\n📝 Detailed prompt with photo description")
    result2 = await service.generate(
        prompt=(
            "professional portrait photograph of a beautiful woman with flowing hair, "
            "expressive eyes, natural beauty, elegant features, soft lighting"
        ),
        nsfw_level=0,
        width=512,
        height=512,
        steps=4
    )

    print(f"\nSimple: {'✅' if result1 else '❌'}")
    print(f"Detailed: {'✅' if result2 else '❌'}")
    print("\n💡 Tip: Detailed prompts produce better photorealism!")

    return result1 and result2


async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("🧪 FLUX.1 [schnell] TEST SUITE - Ultra Photorealistic")
    print("="*70)

    # Check API key
    service = FluxImageService()
    if not service.api_key:
        print("\n❌ ERROR: No API key set!")
        print("   1. Get free API key: https://api.together.xyz/signup")
        print("   2. Add to .env: TOGETHER_API_KEY=your_key_here")
        return

    # Run tests
    test1 = await test_photorealistic_portrait()

    print("\n⏱️  Waiting 10s (rate limit: 6/min)...")
    await asyncio.sleep(10)

    test2 = await test_nsfw_photorealistic()

    await asyncio.sleep(10)

    test3 = await test_comparison()

    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"Test 1 (Portrait):  {'✅ PASSED' if test1 else '❌ FAILED'}")
    print(f"Test 2 (NSFW):      {'✅ PASSED' if test2 else '❌ FAILED'}")
    print(f"Test 3 (Compare):   {'✅ PASSED' if test3 else '❌ FAILED'}")

    if test1 or test2:
        print("\n✅ FLUX Schnell working!")
        print("   🎨 Check the images - they should look 100% REAL")
        print("   💡 Use detailed prompts for best results")
        print("   ⚡ Rate limit: 6 images/minute")
    else:
        print("\n⚠️  Tests failed - check API key")


if __name__ == "__main__":
    asyncio.run(main())
