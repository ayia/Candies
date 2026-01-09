"""
Generate multiple NSFW examples with different levels
Tests ultra-realistic prompts with explicit content
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Fix Windows event loop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from image_service_free import free_image_service


async def generate_examples():
    """Generate multiple NSFW examples"""

    examples = [
        # Level 0 - SFW Portrait
        {
            "name": "SFW Portrait",
            "prompt": "stunning 25 year old woman with long brown hair, piercing blue eyes, natural beauty, elegant dress",
            "nsfw_level": 0,
            "description": "Beautiful portrait - Safe for Work"
        },

        # Level 1 - Sensual/Lingerie
        {
            "name": "Lingerie Bedroom",
            "prompt": "gorgeous 28 year old woman in luxurious bedroom, wearing black lace lingerie, lying on silk sheets, seductive pose, soft romantic lighting",
            "nsfw_level": 1,
            "description": "Sensual lingerie scene"
        },

        # Level 1 - Bikini Beach
        {
            "name": "Bikini Beach",
            "prompt": "beautiful woman on tropical beach at golden hour, wearing stylish bikini, sun-kissed skin, confident pose in shallow water",
            "nsfw_level": 1,
            "description": "Beach bikini photoshoot"
        },

        # Level 2 - Topless Portrait
        {
            "name": "Topless Portrait",
            "prompt": "stunning 26 year old woman topless from waist up, bare breasts visible, standing by window with city view, golden hour lighting",
            "nsfw_level": 2,
            "description": "Topless portrait with natural lighting"
        },

        # Level 2 - Topless Beach
        {
            "name": "Topless Beach",
            "prompt": "gorgeous woman topless on secluded beach, bare breasts, walking in ocean waves, wet skin glistening, sunset background",
            "nsfw_level": 2,
            "description": "Topless beach scene"
        },

        # Level 2 - Topless Bedroom
        {
            "name": "Topless Bedroom",
            "prompt": "beautiful naked woman from waist up, topless with bare breasts, sitting on edge of bed, intimate bedroom setting, soft lighting",
            "nsfw_level": 2,
            "description": "Intimate topless bedroom"
        },

        # Level 3 - Full Nude Bed
        {
            "name": "Full Nude Bed",
            "prompt": "stunning 24 year old woman completely naked, full frontal nudity, lying on white bed sheets, legs slightly apart, intimate erotic photography",
            "nsfw_level": 3,
            "description": "Full frontal nude on bed"
        },

        # Level 3 - Full Nude Standing
        {
            "name": "Full Nude Standing",
            "prompt": "gorgeous woman fully nude standing, complete naked body visible, full frontal nudity, confident pose in luxury apartment, natural lighting",
            "nsfw_level": 3,
            "description": "Standing full nude portrait"
        },

        # Level 3 - Full Nude Beach
        {
            "name": "Full Nude Beach",
            "prompt": "beautiful naked woman on private beach, completely nude full body, walking in shallow water, wet skin, full frontal nudity, sunset",
            "nsfw_level": 3,
            "description": "Full nude beach scene"
        },

        # Level 3 - Explicit Pose
        {
            "name": "Explicit Spread",
            "prompt": "stunning woman fully naked lying on bed, legs spread wide, explicit erotic pose, full frontal nudity, intimate photography, uncensored",
            "nsfw_level": 3,
            "description": "Explicit spread pose"
        },

        # Level 3 - Shower Scene
        {
            "name": "Shower Nude",
            "prompt": "gorgeous naked woman in luxury shower, water running over nude body, full frontal nudity, wet skin, steam, intimate moment",
            "nsfw_level": 3,
            "description": "Nude shower scene"
        },

        # Level 3 - Multiple Angles
        {
            "name": "Nude Back View",
            "prompt": "beautiful woman naked from behind, bare back and buttocks visible, looking over shoulder, full body nude, artistic photography",
            "nsfw_level": 3,
            "description": "Nude back view"
        }
    ]

    print("\n" + "="*70)
    print("🔥 GENERATING NSFW EXAMPLES - ALL LEVELS")
    print("="*70)
    print(f"Total examples: {len(examples)}")
    print("Levels: SFW (0), Sensual (1), Topless (2), Full Nude (3)")
    print("="*70)

    results = []

    for i, example in enumerate(examples, 1):
        print(f"\n[{i}/{len(examples)}] {example['name']} (Level {example['nsfw_level']})")
        print(f"Description: {example['description']}")
        print(f"Prompt: {example['prompt'][:80]}...")

        try:
            # Generate image
            image_path = await free_image_service.generate(
                prompt=example['prompt'],
                nsfw_level=example['nsfw_level'],
                width=1024,
                height=1024,
                model="flux"
            )

            if image_path:
                print(f"✅ SUCCESS: {image_path}")
                results.append({
                    "name": example['name'],
                    "level": example['nsfw_level'],
                    "path": image_path,
                    "success": True
                })
            else:
                print(f"❌ FAILED")
                results.append({
                    "name": example['name'],
                    "level": example['nsfw_level'],
                    "success": False
                })

            # Rate limit: wait 3 seconds between requests
            if i < len(examples):
                print("⏱️  Waiting 3s...")
                await asyncio.sleep(3)

        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append({
                "name": example['name'],
                "level": example['nsfw_level'],
                "success": False,
                "error": str(e)
            })
            await asyncio.sleep(3)

    # Summary
    print("\n" + "="*70)
    print("📊 GENERATION SUMMARY")
    print("="*70)

    by_level = {0: [], 1: [], 2: [], 3: []}
    for r in results:
        by_level[r['level']].append(r)

    for level in [0, 1, 2, 3]:
        level_name = ["SFW", "Sensual", "Topless", "Full Nude"][level]
        total = len(by_level[level])
        success = len([r for r in by_level[level] if r['success']])
        print(f"\nLevel {level} ({level_name}): {success}/{total} successful")
        for r in by_level[level]:
            status = "✅" if r['success'] else "❌"
            print(f"  {status} {r['name']}")
            if r['success'] and 'path' in r:
                print(f"      → {r['path']}")

    total_success = len([r for r in results if r['success']])
    print(f"\n{'='*70}")
    print(f"TOTAL: {total_success}/{len(results)} images generated successfully")
    print(f"{'='*70}")

    if total_success > 0:
        print(f"\n🎨 All images saved in: backend/images/")
        print(f"\n📸 Evaluation Criteria:")
        print(f"  1. Photoréalisme: Does it look like a real photo?")
        print(f"  2. Texture de peau: Visible pores? Natural imperfections?")
        print(f"  3. NSFW explicite: Is nudity shown as requested?")
        print(f"  4. Détails: Hair strands? Natural lighting?")
        print(f"  5. Look IA: Can you tell it's AI-generated?")

        print(f"\n💡 Expected Results:")
        print(f"  • Level 0: Professional portrait")
        print(f"  • Level 1: Lingerie/bikini visible")
        print(f"  • Level 2: Topless with bare breasts + nipples")
        print(f"  • Level 3: Full frontal nudity, completely naked")

    return results


if __name__ == "__main__":
    results = asyncio.run(generate_examples())
