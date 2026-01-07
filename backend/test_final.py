"""Test final - Image Service v6.0"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from image_service import image_service


async def test_sfw():
    """Test SFW generation with Z-Image-Turbo via fal-ai"""
    print("\n" + "=" * 60)
    print("TEST 1: SFW Content (Z-Image-Turbo via fal-ai)")
    print("=" * 60)

    prompt = "beautiful woman with long brown hair, professional portrait, elegant dress, studio lighting"

    try:
        filename = await image_service.generate(
            prompt=prompt,
            width=1024,
            height=1024,
            nsfw=False,
            nsfw_level=0
        )
        filepath = image_service.get_image_path(filename)
        size = os.path.getsize(filepath)
        print(f"\nSUCCESS: {filename} ({size/1024:.1f} KB)")
        return filename
    except Exception as e:
        print(f"\nFAILED: {e}")
        return None


async def test_nsfw():
    """Test NSFW generation"""
    print("\n" + "=" * 60)
    print("TEST 2: NSFW Content (Spaces or Pollinations fallback)")
    print("=" * 60)

    prompt = "beautiful woman, bedroom, seductive pose, looking at camera"

    try:
        filename = await image_service.generate(
            prompt=prompt,
            width=1024,
            height=1024,
            nsfw=True,
            nsfw_level=3
        )
        filepath = image_service.get_image_path(filename)
        size = os.path.getsize(filepath)
        print(f"\nSUCCESS: {filename} ({size/1024:.1f} KB)")
        return filename
    except Exception as e:
        print(f"\nFAILED: {e}")
        return None


async def main():
    print("=" * 60)
    print("IMAGE SERVICE v6.0 - FINAL TEST")
    print("=" * 60)

    # Test SFW
    sfw_result = await test_sfw()

    # Test NSFW
    nsfw_result = await test_nsfw()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"SFW Test:  {'PASS' if sfw_result else 'FAIL'}")
    print(f"NSFW Test: {'PASS' if nsfw_result else 'FAIL'}")

    return sfw_result is not None


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
