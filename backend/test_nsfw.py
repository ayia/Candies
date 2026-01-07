"""Test Z-Image-Turbo NSFW generation"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from huggingface_hub import InferenceClient
from config import settings
from datetime import datetime


async def test_nsfw():
    """Test NSFW content generation"""

    print("=" * 60)
    print("Z-Image-Turbo NSFW Test")
    print("=" * 60)

    client = InferenceClient(
        provider="fal-ai",
        api_key=settings.HF_API_TOKEN
    )

    # NSFW prompt similar to the screenshot request
    prompt = """masterpiece, best quality, ultra realistic, photorealistic, RAW photo, 8k uhd,
    nsfw, explicit, nude, naked, uncensored,
    beautiful caucasian woman, 25 years old, long brown hair cascading down back,
    on white silk bed sheets, bedroom setting, soft romantic lighting,
    looking directly at camera with seductive bedroom eyes,
    completely nude, bare breasts, nipples visible,
    seductive pose, lying on bed, detailed skin texture, sharp focus"""

    print(f"\nPrompt (truncated): {prompt[:100]}...")
    print("-" * 60)

    try:
        print("Generating...")

        image = client.text_to_image(
            prompt=prompt,
            model="Tongyi-MAI/Z-Image-Turbo",
            width=1024,
            height=1024,
            num_inference_steps=8
        )

        print(f"Image size: {image.size}")

        # Save
        images_dir = os.path.join(os.path.dirname(__file__), "images")
        filename = f"test_nsfw_{datetime.now().strftime('%H%M%S')}.png"
        filepath = os.path.join(images_dir, filename)
        image.save(filepath, "PNG")

        file_size = os.path.getsize(filepath)
        print(f"\nSaved: {filename}")
        print(f"File size: {file_size} bytes ({file_size/1024:.1f} KB)")
        print(f"Path: {filepath}")

        return filepath

    except Exception as e:
        print(f"\nError: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = asyncio.run(test_nsfw())
    print("\n" + ("SUCCESS" if result else "FAILED"))
