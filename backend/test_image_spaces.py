"""Test script to diagnose Hugging Face Spaces connectivity"""
import sys
import io
import asyncio
import requests
from gradio_client import Client as GradioClient
from config import settings

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SPACES_TO_TEST = [
    "Heartsync/Adult",
    "Heartsync/NSFW-Uncensored-photo",
    "Heartsync/NSFW-image"
]

def test_space_availability(space_name):
    """Test if a space is available"""
    print(f"\n{'='*60}")
    print(f"Testing: {space_name}")
    print(f"{'='*60}")

    # 1. Check space status via API
    try:
        print("1. Checking space status via HF API...")
        response = requests.get(
            f"https://huggingface.co/api/spaces/{space_name}",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data.get('runtime', {}).get('stage', 'UNKNOWN')}")
            print(f"   SDK: {data.get('sdk', 'UNKNOWN')}")
            print(f"   Likes: {data.get('likes', 0)}")
        else:
            print(f"   ERROR: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

    # 2. Check runtime status
    try:
        print("2. Checking runtime status...")
        response = requests.get(
            f"https://huggingface.co/api/spaces/{space_name}/runtime",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   Stage: {data.get('stage', 'UNKNOWN')}")
            print(f"   Hardware: {data.get('hardware', {}).get('current', 'UNKNOWN')}")
        else:
            print(f"   ERROR: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ERROR: {e}")

    # 3. Test connection with Gradio Client
    try:
        print("3. Testing Gradio Client connection...")
        print("   (This may take 10-30 seconds...)")

        # Timeout after 30 seconds
        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError("Connection timeout")

        # Set alarm for 30 seconds (Unix only)
        # For Windows, we'll use a different approach
        try:
            client = GradioClient(space_name, hf_token=settings.HF_API_TOKEN)
            print(f"   SUCCESS! Connected to {space_name}")
            print(f"   API endpoints: {len(client.endpoints) if hasattr(client, 'endpoints') else 'Unknown'}")
            return True
        except Exception as e:
            print(f"   FAILED: {e}")
            return False

    except Exception as e:
        print(f"   ERROR: {e}")
        return False


def test_alternative_models():
    """Suggest alternative models that might work better"""
    print("\n" + "="*60)
    print("ALTERNATIVE MODELS TO CONSIDER")
    print("="*60)

    alternatives = [
        {
            "name": "Novita AI API",
            "url": "https://novita.ai",
            "pros": "Stable, fast, no quotas",
            "cons": "Requires paid API key"
        },
        {
            "name": "Stability AI (Stable Diffusion API)",
            "url": "https://platform.stability.ai",
            "pros": "Official, high quality",
            "cons": "Paid service"
        },
        {
            "name": "Local Stable Diffusion",
            "url": "https://github.com/AUTOMATIC1111/stable-diffusion-webui",
            "pros": "Full control, no limits, private",
            "cons": "Requires GPU (NVIDIA recommended)"
        }
    ]

    for i, alt in enumerate(alternatives, 1):
        print(f"\n{i}. {alt['name']}")
        print(f"   URL: {alt['url']}")
        print(f"   Pros: {alt['pros']}")
        print(f"   Cons: {alt['cons']}")


def main():
    print("="*60)
    print("HUGGING FACE SPACES DIAGNOSTIC TEST")
    print("="*60)
    print(f"\nHF Token: {'SET' if settings.HF_API_TOKEN else 'NOT SET'}")

    results = {}
    for space in SPACES_TO_TEST:
        results[space] = test_space_availability(space)

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for space, success in results.items():
        status = "OK" if success else "FAILED"
        emoji = "✓" if success else "✗"
        print(f"{space}: {status}")

    if not any(results.values()):
        print("\nALL SPACES FAILED!")
        print("\nPossible causes:")
        print("1. HuggingFace spaces are sleeping (not used recently)")
        print("2. Network/firewall blocking connections")
        print("3. Quota exceeded (free tier limits)")
        print("4. Spaces moved or renamed")

        print("\nRecommended solutions:")
        print("1. Visit each space URL directly to wake it up:")
        for space in SPACES_TO_TEST:
            print(f"   https://huggingface.co/spaces/{space}")
        print("\n2. Wait 2-3 minutes and try again")
        print("3. Consider using alternative services (see below)")

        test_alternative_models()
    else:
        print(f"\n{sum(results.values())}/{len(results)} spaces are working!")


if __name__ == "__main__":
    main()
