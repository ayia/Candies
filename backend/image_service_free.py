"""
FREE Image Generation Service - 100% Free NSFW-Friendly
Uses Pollinations.ai - No API key needed, truly unlimited and free
"""
import sys
import io
import os
import uuid
import asyncio
import aiohttp
import urllib.parse
import logging
from datetime import datetime
from typing import Optional
from config import settings

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Fix Windows asyncio event loop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logger = logging.getLogger("FreeImageService")


class FreeImageService:
    """
    100% FREE Image Generation using Pollinations.ai

    - No API key required
    - Unlimited generations
    - NSFW supported (disable safety filter)
    - Simple URL-based API
    - Models: Flux, Turbo, Stable Diffusion

    API: https://image.pollinations.ai/prompt/{prompt}?width=X&height=Y&model=flux&nologo=true&enhance=true
    """

    def __init__(self):
        self.images_dir = settings.IMAGES_DIR
        os.makedirs(self.images_dir, exist_ok=True)

        # Pollinations.ai API
        self.base_url = "https://image.pollinations.ai/prompt"

        # Available models (as of 2026)
        self.models = {
            "flux": "flux",           # Best quality (default)
            "turbo": "turbo",         # Fast generation
            "sd": "stable-diffusion"  # Classic SD
        }

        logger.info("="*60)
        logger.info("🎨 FREE Image Service - Pollinations.ai")
        logger.info("✅ No API key needed")
        logger.info("✅ Unlimited generations")
        logger.info("✅ NSFW supported")
        logger.info("Models: flux (best), turbo (fast), sd (classic)")
        logger.info("="*60)

    async def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        style: str = "realistic",
        width: int = 1024,
        height: int = 1024,
        nsfw_level: int = 0,
        model: str = "flux"  # "flux", "turbo", or "sd"
    ) -> Optional[str]:
        """
        Generate image using Pollinations.ai

        Args:
            prompt: Main prompt
            negative_prompt: What to avoid (included in prompt with "not:")
            style: "realistic" or "anime"
            width/height: Image dimensions (512-2048)
            nsfw_level: 0-3 (higher = more explicit)
            model: "flux" (best), "turbo" (fast), or "sd" (classic)

        Returns:
            Path to saved image or None
        """

        logger.info("="*60)
        logger.info("🎨 FREE Image Generation - Pollinations.ai")
        logger.info(f"Model: {model}")
        logger.info(f"Size: {width}x{height}")
        logger.info(f"NSFW Level: {nsfw_level}")
        logger.info(f"Prompt: {prompt[:100]}...")
        logger.info("="*60)

        # Enhance prompt
        enhanced_prompt = self._enhance_prompt(prompt, negative_prompt, nsfw_level)

        # Build URL
        model_name = self.models.get(model, "flux")

        try:
            # Generate image
            image_data = await self._generate_pollinations(
                enhanced_prompt,
                width,
                height,
                model_name,
                nsfw_level
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

    async def _generate_pollinations(
        self,
        prompt: str,
        width: int,
        height: int,
        model: str,
        nsfw_level: int
    ) -> Optional[bytes]:
        """
        Generate using Pollinations.ai API

        API: GET https://image.pollinations.ai/prompt/{prompt}
        Query params: width, height, model, seed, nologo, enhance, private
        """

        try:
            # URL encode the prompt
            encoded_prompt = urllib.parse.quote(prompt)

            # Build URL with parameters
            url = f"{self.base_url}/{encoded_prompt}"

            params = {
                "width": width,
                "height": height,
                "model": model,
                "nologo": "true",      # Remove Pollinations watermark
                "enhance": "true",     # Enhance prompt quality
                "seed": -1             # Random seed
            }

            # NSFW support: Don't set "safe" parameter (it filters NSFW)
            # By default, Pollinations allows NSFW when "safe" is not set

            logger.info(f"📡 Calling Pollinations API...")
            logger.info(f"   URL: {self.base_url}/[prompt]")
            logger.info(f"   Model: {model}")
            logger.info(f"   Size: {width}x{height}")

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=120)  # 2 minutes
                ) as response:

                    logger.info(f"   Status: {response.status}")

                    if response.status == 200:
                        image_data = await response.read()
                        logger.info(f"   ✅ Downloaded {len(image_data)} bytes")
                        return image_data
                    else:
                        error_text = await response.text()
                        logger.error(f"   ❌ Error: {error_text[:200]}")
                        return None

        except asyncio.TimeoutError:
            logger.error("❌ Timeout after 120s")
            return None
        except Exception as e:
            logger.error(f"❌ Request failed: {e}")
            return None

    async def _save_image(self, image_data: bytes) -> Optional[str]:
        """Save image data to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"{timestamp}_{unique_id}.jpg"
            filepath = os.path.join(self.images_dir, filename)

            with open(filepath, 'wb') as f:
                f.write(image_data)

            logger.info(f"💾 Saved: {filename} ({len(image_data)} bytes)")
            return filename

        except Exception as e:
            logger.error(f"❌ Save error: {e}")
            return None

    def _enhance_prompt(self, prompt: str, negative_prompt: str, nsfw_level: int) -> str:
        """
        ULTRA ENHANCED prompt for MAXIMUM photorealism with Pollinations

        Focus on photographic realism, camera specs, lighting details
        """

        # ULTRA REALISTIC - like real amateur photo NOT professional
        quality_tags = (
            "candid amateur photo, iPhone snapshot, casual selfie style, "
            "real unedited skin with visible pores, freckles, beauty marks, minor blemishes, "
            "natural imperfect skin texture NOT airbrushed, slightly uneven skin tone, "
            "messy natural hair with flyaway strands, not perfectly styled, "
            "natural home lighting or sunlight, slight shadows and highlights, "
            "realistic natural colors, not oversaturated, "
            "authentic real person NOT professional model, "
            "imperfect casual pose, genuine candid moment, "
            "shot on phone camera, amateur photography quality, "
            "looks like real girlfriend photo NOT magazine cover, "
            "photorealistic, real human being, genuine unretouched photo"
        )

        # NSFW/Nude tags - be VERY explicit for better results
        nsfw_tags = ""
        if nsfw_level >= 1:
            nsfw_tags = (
                ", adult content 18+, mature woman, sensual pose, "
                "provocative, seductive expression"
            )
        if nsfw_level >= 2:
            nsfw_tags = (
                ", explicit adult content 18+, NSFW, nude, naked body, "
                "topless, bare breasts, sensual curves, erotic photography, "
                "seductive pose, intimate moment"
            )
        if nsfw_level >= 3:
            nsfw_tags = (
                ", XXX explicit adult content 18+, fully nude, completely naked, "
                "full frontal nudity, bare breasts visible, nipples visible, "
                "explicit nude photography, uncensored, no clothing, "
                "erotic art photography, sexual pose, spread legs"
            )

        # Build full prompt
        full_prompt = f"{quality_tags}, {prompt}{nsfw_tags}"

        # Add negative prompt - focus on removing AI artifacts
        if negative_prompt:
            full_prompt += f", NOT: {negative_prompt}"
        else:
            # Default negatives - BLOCK fantasy/perfect/magazine look
            default_negative = (
                "professional model, magazine cover, fashion photoshoot, studio portrait, "
                "perfect flawless skin, airbrushed, photoshopped, retouched, "
                "professional makeup, salon hairstyle, perfectly styled, "
                "studio lighting, professional photographer, "
                "fantasy, idealized, too perfect, unrealistic beauty, "
                "cartoon, anime, illustration, 3d render, cgi, digital art, painting, "
                "artificial, fake, plastic skin, doll face, mannequin, "
                "oversaturated, oversmooth, glamour shot, "
                "low quality, blurry, bad anatomy, deformed, distorted, "
                "watermark, signature, text, logo"
            )
            if nsfw_level == 0:
                default_negative += ", nsfw, nude, naked, topless, explicit"
            full_prompt += f", NOT: {default_negative}"

        return full_prompt


# Global instance
free_image_service = FreeImageService()


# ============================================================
# USAGE EXAMPLES & TESTS
# ============================================================

async def test_sfw():
    """Test SFW image generation"""
    print("\n" + "="*60)
    print("Test 1: SFW Image (Safe for Work)")
    print("="*60)

    service = FreeImageService()

    result = await service.generate(
        prompt="beautiful woman in elegant evening dress, professional portrait photography",
        nsfw_level=0,
        width=512,
        height=512,
        model="flux"  # Best quality
    )

    if result:
        print(f"✅ SUCCESS: {result}")
    else:
        print("❌ FAILED")

    return result is not None


async def test_nsfw():
    """Test NSFW image generation"""
    print("\n" + "="*60)
    print("Test 2: NSFW Image")
    print("="*60)

    service = FreeImageService()

    result = await service.generate(
        prompt="stunning woman on beach, summer photoshoot, bikini, sun-kissed skin",
        nsfw_level=2,
        width=512,
        height=512,
        model="flux"
    )

    if result:
        print(f"✅ SUCCESS: {result}")
    else:
        print("❌ FAILED")

    return result is not None


async def test_all_models():
    """Test all available models"""
    print("\n" + "="*60)
    print("Test 3: All Models")
    print("="*60)

    service = FreeImageService()

    models = ["flux", "turbo", "sd"]
    results = {}

    for model in models:
        print(f"\n🧪 Testing model: {model}")
        result = await service.generate(
            prompt="portrait of a beautiful woman, professional photo",
            nsfw_level=0,
            width=512,
            height=512,
            model=model
        )
        results[model] = result is not None
        print(f"   {'✅' if result else '❌'} Model {model}")

    return results


async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("🧪 FREE IMAGE SERVICE TEST SUITE - Pollinations.ai")
    print("="*70)

    # Run tests
    test1 = await test_sfw()
    await asyncio.sleep(2)  # Rate limit

    test2 = await test_nsfw()
    await asyncio.sleep(2)

    test3 = await test_all_models()

    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"Test 1 (SFW):      {'✅ PASSED' if test1 else '❌ FAILED'}")
    print(f"Test 2 (NSFW):     {'✅ PASSED' if test2 else '❌ FAILED'}")
    print(f"Test 3 (Models):   {test3}")

    if test1 and test2:
        print("\n✅ All critical tests passed!")
        print("   ✅ 100% FREE service working")
        print("   ✅ NSFW content supported")
        print("   ✅ No API key required")
    else:
        print("\n⚠️  Some tests failed")


if __name__ == "__main__":
    asyncio.run(main())
