"""
Smart Image Service - Automatic Best Quality Selection
Tries services in order of quality, automatically falls back if one fails
"""
import sys
import os
import logging
from typing import Optional

# Fix Windows asyncio event loop
if sys.platform == 'win32':
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from config import settings

logger = logging.getLogger("SmartImageService")


class SmartImageService:
    """
    Smart Image Generation with Automatic Fallback

    Priority Order (best to worst):
    1. FLUX.1 Schnell (⭐⭐⭐⭐⭐) - Ultra photorealistic, if API key available
    2. Pollinations.ai (⭐⭐⭐⭐) - Free, unlimited, good quality
    3. HuggingFace Inference API (⭐⭐⭐⭐⭐) - Best quality but with quotas

    Automatically selects the best available service
    """

    def __init__(self):
        self.images_dir = settings.IMAGES_DIR
        os.makedirs(self.images_dir, exist_ok=True)

        # Check available services
        self.together_key = os.getenv("TOGETHER_API_KEY")
        self.hf_token = settings.HF_API_TOKEN

        # Initialize available services
        self.services = []

        # Try FLUX Schnell first (best quality)
        if self.together_key:
            try:
                from image_service_flux import flux_image_service
                self.services.append(("FLUX Schnell ⭐⭐⭐⭐⭐", flux_image_service))
                logger.info("✅ FLUX Schnell available (ULTRA PHOTOREALISTIC)")
            except Exception as e:
                logger.warning(f"⚠️  FLUX Schnell unavailable: {e}")

        # Always add Pollinations (free, unlimited)
        try:
            from image_service_free import free_image_service
            self.services.append(("Pollinations ⭐⭐⭐⭐", free_image_service))
            logger.info("✅ Pollinations.ai available (FREE, UNLIMITED)")
        except Exception as e:
            logger.warning(f"⚠️  Pollinations unavailable: {e}")

        # Add HF Inference as last resort
        if self.hf_token:
            try:
                from image_service_hf_free import hf_free_image_service
                self.services.append(("HuggingFace ⭐⭐⭐⭐⭐", hf_free_image_service))
                logger.info("✅ HuggingFace Inference available (BEST QUALITY, QUOTAS)")
            except Exception as e:
                logger.warning(f"⚠️  HuggingFace unavailable: {e}")

        if not self.services:
            logger.error("❌ NO IMAGE SERVICES AVAILABLE!")
        else:
            logger.info("="*60)
            logger.info(f"🎨 Smart Image Service - {len(self.services)} services available")
            for name, _ in self.services:
                logger.info(f"   • {name}")
            logger.info("="*60)

    async def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        style: str = "realistic",
        width: int = 1024,
        height: int = 1024,
        nsfw_level: int = 0
    ) -> Optional[str]:
        """
        Generate image using best available service

        Automatically tries services in order of quality
        Falls back to next service if one fails
        """

        if not self.services:
            logger.error("❌ No image services available!")
            return None

        logger.info("="*60)
        logger.info(f"🎨 Smart Image Generation")
        logger.info(f"Prompt: {prompt[:80]}...")
        logger.info(f"NSFW Level: {nsfw_level}")
        logger.info(f"Trying {len(self.services)} services in quality order...")
        logger.info("="*60)

        # Try each service in order
        for i, (service_name, service) in enumerate(self.services, 1):
            logger.info(f"\n🔄 Attempt {i}/{len(self.services)}: {service_name}")

            try:
                # Generate image
                image_path = await service.generate(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    style=style,
                    width=width,
                    height=height,
                    nsfw_level=nsfw_level
                )

                if image_path:
                    logger.info(f"✅ SUCCESS with {service_name}!")
                    logger.info(f"   Image: {image_path}")
                    return image_path
                else:
                    logger.warning(f"⚠️  {service_name} returned no image, trying next...")

            except Exception as e:
                logger.warning(f"❌ {service_name} failed: {e}")
                if i < len(self.services):
                    logger.info(f"   Trying next service...")
                continue

        logger.error("❌ All services failed!")
        return None

    def get_status(self) -> dict:
        """Get status of all available services"""
        return {
            "available_services": len(self.services),
            "services": [name for name, _ in self.services],
            "has_flux": bool(self.together_key),
            "has_hf": bool(self.hf_token)
        }


# Global instance
smart_image_service = SmartImageService()


# ============================================================
# USAGE EXAMPLE
# ============================================================

async def test_smart_service():
    """Test smart image service with automatic fallback"""
    print("\n" + "="*70)
    print("🧪 SMART IMAGE SERVICE TEST")
    print("="*70)

    service = SmartImageService()

    # Show status
    status = service.get_status()
    print(f"\n📊 Service Status:")
    print(f"   Available services: {status['available_services']}")
    for svc in status['services']:
        print(f"   • {svc}")

    if status['available_services'] == 0:
        print("\n❌ No services available!")
        print("   Solutions:")
        print("   1. Get Together.ai API key (best): https://api.together.xyz/signup")
        print("   2. Or just use Pollinations (working)")
        return

    # Test generation
    print("\n" + "="*70)
    print("Test 1: Portrait Photo")
    print("="*70)

    result = await service.generate(
        prompt="professional portrait of a beautiful woman, elegant, natural lighting",
        nsfw_level=0,
        width=1024,
        height=1024
    )

    if result:
        print(f"\n✅ SUCCESS: {result}")
        print(f"   Generated with: {status['services'][0] if status['services'] else 'Unknown'}")
    else:
        print("\n❌ FAILED")

    # Test NSFW
    print("\n" + "="*70)
    print("Test 2: NSFW Beach Photo")
    print("="*70)

    result2 = await service.generate(
        prompt="stunning woman on beach, bikini, summer photoshoot",
        nsfw_level=2,
        width=1024,
        height=1024
    )

    if result2:
        print(f"\n✅ SUCCESS: {result2}")
    else:
        print("\n❌ FAILED")

    # Summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    if result or result2:
        print("✅ Smart service working!")
        print(f"   Best service used: {status['services'][0]}")
        print("\n💡 Tips:")
        print("   • Add TOGETHER_API_KEY for ULTRA photorealistic quality")
        print("   • Current service works but FLUX is 10x better")
    else:
        print("❌ All services failed")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_smart_service())
