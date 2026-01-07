"""Test NSFW Z-Image-Turbo Spaces"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gradio_client import Client


def test_space(space_name):
    """Test a HuggingFace Space and discover its API"""
    print(f"\n{'='*60}")
    print(f"Testing: {space_name}")
    print("=" * 60)

    try:
        # Suppress output
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        client = Client(space_name)
        sys.stdout = old_stdout

        print("Connected!")
        print("\nAPI Endpoints:")
        print("-" * 40)

        # Get API info
        api_info = client.view_api(print_info=False, return_format="dict")

        if api_info and "named_endpoints" in api_info:
            for name, info in api_info["named_endpoints"].items():
                print(f"\nEndpoint: {name}")
                if "parameters" in info:
                    print("  Parameters:")
                    for param in info["parameters"]:
                        label = param.get("label", "unknown")
                        ptype = param.get("type", "unknown")
                        print(f"    - {label}: {ptype}")

        if api_info and "unnamed_endpoints" in api_info:
            for idx, info in api_info["unnamed_endpoints"].items():
                print(f"\nfn_index={idx}")
                if "parameters" in info:
                    print("  Parameters:")
                    for param in info["parameters"]:
                        label = param.get("label", "unknown")
                        ptype = param.get("type", "unknown")
                        print(f"    - {label}: {ptype}")

        return client, api_info

    except Exception as e:
        print(f"Error: {e}")
        return None, None


# Test the NSFW spaces
spaces = [
    "yingzhac/Z_image_NSFW",
    "ClickyGPT/NSFW_Z-Image-Turbo",
]

for space in spaces:
    test_space(space)
