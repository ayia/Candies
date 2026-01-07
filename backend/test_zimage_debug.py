"""Debug Z-Image-Turbo generation - No size filter"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from huggingface_hub import InferenceClient
from config import settings
from datetime import datetime
import uuid


async def test_direct():
    """Test direct API call to Z-Image-Turbo"""

    print("=" * 60)
    print("Direct Z-Image-Turbo Test via fal-ai")
    print("=" * 60)

    token = settings.HF_API_TOKEN
    print(f"Token: {token[:10]}...{token[-5:]}")

    client = InferenceClient(
        provider="fal-ai",
        api_key=token
    )

    # Simple prompt first
    prompt = "A beautiful woman with long brown hair, photorealistic portrait, professional photography, 8k quality"

    print(f"\nPrompt: {prompt}")
    print("-" * 60)

    try:
        print("Calling text_to_image...")

        image = client.text_to_image(
            prompt=prompt,
            model="Tongyi-MAI/Z-Image-Turbo",
            width=1024,
            height=1024,
            num_inference_steps=8
        )

        print(f"Response type: {type(image)}")
        print(f"Image size: {image.size if hasattr(image, 'size') else 'N/A'}")
        print(f"Image mode: {image.mode if hasattr(image, 'mode') else 'N/A'}")

        # Save without checking size
        images_dir = os.path.join(os.path.dirname(__file__), "images")
        os.makedirs(images_dir, exist_ok=True)

        filename = f"test_debug_{datetime.now().strftime('%H%M%S')}.png"
        filepath = os.path.join(images_dir, filename)
        image.save(filepath, "PNG")

        file_size = os.path.getsize(filepath)
        print(f"\nSaved: {filename}")
        print(f"File size: {file_size} bytes ({file_size/1024:.1f} KB)")

        return True

    except Exception as e:
        print(f"\nError: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_direct())
    print("\n" + ("SUCCESS" if success else "FAILED"))
