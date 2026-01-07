"""Test Z-Image-Turbo generation"""
import asyncio
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from image_service import image_service


async def test_generation():
    """Test image generation with Z-Image-Turbo"""

    print("=" * 60)
    print("Testing Z-Image-Turbo via fal-ai")
    print("=" * 60)

    # Test prompt - NSFW content similar to your screenshot
    test_prompt = """beautiful woman, long brown hair cascading down her back,
    on a white silk bed, looking directly at camera with seductive eyes,
    intimate bedroom scene, soft lighting, photorealistic"""

    print(f"\nPrompt: {test_prompt[:80]}...")
    print(f"NSFW Level: 3 (explicit)")
    print("-" * 60)

    try:
        filename = await image_service.generate(
            prompt=test_prompt,
            style="realistic",
            width=1024,
            height=1024,
            nsfw=True,
            nsfw_level=3,
            seed=42
        )

        filepath = image_service.get_image_path(filename)
        file_size = os.path.getsize(filepath)

        print("\n" + "=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print(f"Filename: {filename}")
        print(f"Path: {filepath}")
        print(f"Size: {file_size} bytes")
        print(f"Size: {file_size / 1024:.1f} KB")

        return True

    except Exception as e:
        print("\n" + "=" * 60)
        print("FAILED!")
        print("=" * 60)
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_generation())
    sys.exit(0 if success else 1)
