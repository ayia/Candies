"""Test Z-Image-Turbo NSFW Space"""
import sys
import os
import shutil
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gradio_client import Client


def test_nsfw_generation():
    """Test NSFW image generation with yingzhac/Z_image_NSFW"""

    print("=" * 60)
    print("Testing: yingzhac/Z_image_NSFW (Z-Image-Turbo)")
    print("=" * 60)

    # Connect to space
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    client = Client("yingzhac/Z_image_NSFW")
    sys.stdout = old_stdout

    print("Connected!")

    # NSFW prompt
    prompt = """masterpiece, best quality, ultra realistic, photorealistic, RAW photo, 8k uhd,
    beautiful caucasian woman, 25 years old, long brown hair cascading down back,
    on white silk bed sheets, bedroom setting, soft romantic lighting,
    looking directly at camera with seductive bedroom eyes,
    nude, bare breasts, nipples visible, naked body,
    seductive pose, lying on bed, detailed skin texture, sharp focus"""

    print(f"\nPrompt: {prompt[:80]}...")
    print("-" * 60)

    try:
        print("Generating with /generate_image endpoint...")

        result = client.predict(
            prompt,                  # Prompt
            "",                      # Negative Prompt (empty - Z-Image doesn't use it)
            1024,                    # Height
            1024,                    # Width
            8,                       # Inference Steps
            0.0,                     # CFG Guidance Scale (0 for turbo)
            42,                      # Seed
            False,                   # Randomize Seed
            api_name="/generate_image"
        )

        print(f"\nResult type: {type(result)}")
        print(f"Result: {result}")

        # Handle result - could be tuple (images, seed) or single image
        image_path = None
        if isinstance(result, tuple):
            # (gallery, seed) format
            gallery = result[0]
            if isinstance(gallery, list) and len(gallery) > 0:
                first = gallery[0]
                if isinstance(first, dict):
                    image_path = first.get('image') or first.get('path')
                elif isinstance(first, str):
                    image_path = first
        elif isinstance(result, str):
            image_path = result

        if image_path and os.path.exists(image_path):
            # Copy to our images folder
            images_dir = os.path.join(os.path.dirname(__file__), "images")
            os.makedirs(images_dir, exist_ok=True)

            ext = os.path.splitext(image_path)[1] or ".png"
            filename = f"zimage_nsfw_{datetime.now().strftime('%H%M%S')}{ext}"
            dest = os.path.join(images_dir, filename)

            shutil.copy(image_path, dest)
            file_size = os.path.getsize(dest)

            print(f"\nSaved: {filename}")
            print(f"Size: {file_size} bytes ({file_size/1024:.1f} KB)")
            print(f"Path: {dest}")

            return dest
        else:
            print(f"No valid image path found in result")
            return None

    except Exception as e:
        print(f"\nError: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = test_nsfw_generation()
    print("\n" + ("SUCCESS" if result else "FAILED"))
