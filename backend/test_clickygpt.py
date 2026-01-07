"""Test ClickyGPT NSFW Z-Image-Turbo Space"""
import sys
import os
import shutil
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gradio_client import Client


def test_clickygpt():
    """Test NSFW with ClickyGPT/NSFW_Z-Image-Turbo"""

    print("=" * 60)
    print("Testing: ClickyGPT/NSFW_Z-Image-Turbo")
    print("=" * 60)

    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    client = Client("ClickyGPT/NSFW_Z-Image-Turbo")
    sys.stdout = old_stdout

    print("Connected!")

    prompt = """masterpiece, best quality, ultra realistic, photorealistic,
    beautiful caucasian woman, 25 years old, long brown hair,
    on white silk bed, bedroom, soft lighting, looking at camera,
    nude, bare breasts, seductive pose, detailed skin"""

    print(f"\nPrompt: {prompt[:60]}...")
    print("-" * 60)

    try:
        print("Generating with /infer endpoint...")

        result = client.predict(
            prompt,       # Prompt
            "",           # Negative prompt
            42,           # Seed
            False,        # Randomize seed
            1024,         # Width (max 1024)
            1024,         # Height (max 1024)
            0.0,          # Guidance scale (0 for turbo)
            8,            # Inference steps
            api_name="/infer"
        )

        print(f"\nResult type: {type(result)}")
        print(f"Result: {result}")

        # Parse result
        image_path = None
        if isinstance(result, tuple):
            # Usually (image_path, seed)
            image_path = result[0] if len(result) > 0 else None
        elif isinstance(result, str):
            image_path = result

        if image_path and os.path.exists(image_path):
            images_dir = os.path.join(os.path.dirname(__file__), "images")
            os.makedirs(images_dir, exist_ok=True)

            ext = os.path.splitext(image_path)[1] or ".png"
            filename = f"clickygpt_nsfw_{datetime.now().strftime('%H%M%S')}{ext}"
            dest = os.path.join(images_dir, filename)

            shutil.copy(image_path, dest)
            file_size = os.path.getsize(dest)

            print(f"\nSaved: {filename}")
            print(f"Size: {file_size} bytes ({file_size/1024:.1f} KB)")

            return dest

        print("No valid image in result")
        return None

    except Exception as e:
        print(f"\nError: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = test_clickygpt()
    print("\n" + ("SUCCESS" if result else "FAILED"))
