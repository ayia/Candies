"""
Generate images using V4 Optimized Prompt Generator
Targeting ≥9.5/10 quality scores with research-based validation
"""

import sys
import asyncio
import aiohttp
from datetime import datetime
import hashlib
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from image_prompt_generator_v4 import OptimizedPromptGenerator


class V4ImageGenerator:
    """Generate images with V4 optimized prompts"""

    def __init__(self):
        self.generator = OptimizedPromptGenerator()
        self.base_url = "https://image.pollinations.ai/prompt/"
        self.images_dir = Path("images")
        self.images_dir.mkdir(exist_ok=True)

    async def generate_image(
        self,
        session: aiohttp.ClientSession,
        nsfw_level: int,
        test_name: str
    ) -> dict:
        """Generate single image with V4 prompt"""

        # Generate optimized prompt
        prompt, negative = self.generator.generate_optimized_prompt(
            nsfw_level=nsfw_level
        )

        # Create URL
        url = f"{self.base_url}{prompt}"

        print(f"\n📝 Prompt ({len(prompt.split())} words):")
        print(f"{prompt[:150]}...")

        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    # Save image
                    image_data = await response.read()

                    # Generate filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    hash_suffix = hashlib.md5(prompt.encode()).hexdigest()[:8]
                    filename = f"{timestamp}_{hash_suffix}.jpg"
                    filepath = self.images_dir / filename

                    with open(filepath, 'wb') as f:
                        f.write(image_data)

                    print(f"✅ SUCCESS: {filename}")

                    return {
                        "success": True,
                        "filename": filename,
                        "prompt": prompt,
                        "nsfw_level": nsfw_level,
                        "test_name": test_name
                    }
                else:
                    print(f"❌ FAILED: HTTP {response.status}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "test_name": test_name
                    }

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "test_name": test_name
            }

    async def generate_batch(self):
        """Generate comprehensive test batch"""

        print("\n" + "="*80)
        print("🚀 V4 OPTIMIZED IMAGE GENERATION")
        print("="*80)
        print("\nUsing research-based prompt generator (average 9.74/10 validation score)")
        print("Generating diverse images across all NSFW levels\n")
        print(f"{'='*80}\n")

        # Test cases
        tests = [
            {"name": "SFW Portrait 1", "nsfw": 0},
            {"name": "SFW Portrait 2", "nsfw": 0},
            {"name": "SFW Portrait 3", "nsfw": 0},
            {"name": "Lingerie 1", "nsfw": 1},
            {"name": "Lingerie 2", "nsfw": 1},
            {"name": "Lingerie 3", "nsfw": 1},
            {"name": "Topless 1", "nsfw": 2},
            {"name": "Topless 2", "nsfw": 2},
            {"name": "Topless 3", "nsfw": 2},
            {"name": "Full Nude 1", "nsfw": 3},
            {"name": "Full Nude 2", "nsfw": 3},
            {"name": "Full Nude 3", "nsfw": 3},
        ]

        results = []

        async with aiohttp.ClientSession() as session:
            for i, test in enumerate(tests, 1):
                print(f"\n{'#'*80}")
                print(f"TEST {i}/{len(tests)}: {test['name']}")
                print(f"{'#'*80}")

                result = await self.generate_image(
                    session=session,
                    nsfw_level=test['nsfw'],
                    test_name=test['name']
                )

                results.append(result)

                # Delay between requests
                if i < len(tests):
                    print("⏱️  Waiting 5s...")
                    await asyncio.sleep(5)

        # Summary
        print(f"\n\n{'='*80}")
        print("📊 GENERATION SUMMARY")
        print(f"{'='*80}\n")

        successful = [r for r in results if r.get('success')]
        failed = [r for r in results if not r.get('success')]

        print(f"✅ Successful: {len(successful)}/{len(results)} ({100*len(successful)/len(results):.1f}%)")

        if successful:
            print(f"\n{'='*80}")
            print("✅ GENERATED IMAGES:")
            print(f"{'='*80}")
            for r in successful:
                print(f"  • {r['test_name']:20s} → {r['filename']}")

        if failed:
            print(f"\n{'='*80}")
            print("❌ FAILED:")
            print(f"{'='*80}")
            for r in failed:
                print(f"  • {r['test_name']:20s} → {r.get('error', 'Unknown error')}")

        print(f"\n{'='*80}")
        print(f"📁 Images saved to: {self.images_dir.absolute()}")
        print(f"{'='*80}\n")

        if len(successful) == len(results):
            print("🎉 PERFECT! All images generated successfully!")
            print("✅ Ready for quality validation")
        elif len(successful) >= len(results) * 0.8:
            print(f"✅ {len(successful)}/{len(results)} images generated")
            print("⚠️  Some failures (likely server temporary issues)")
        else:
            print(f"⚠️  Only {len(successful)}/{len(results)} succeeded")
            print("❌ Review errors above")

        print()


async def main():
    generator = V4ImageGenerator()
    await generator.generate_batch()


if __name__ == "__main__":
    asyncio.run(main())
