"""Test NSFW level 5 detection with uncensored model"""
import asyncio
import sys

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from services.image_prompt_agents import IntentionAnalyzer

async def test_nsfw5():
    analyzer = IntentionAnalyzer()

    test_cases = [
        "Envoie moi une photo sexy de toi en prof fesant un blowjob a moi ton élevé",
        "photo de toi en train de faire un blowjob",
        "photo of you giving a blowjob",
        "pic of you sucking dick",
    ]

    print("\n" + "="*80)
    print("TEST NSFW LEVEL 5 DETECTION WITH UNCENSORED MODEL")
    print("="*80 + "\n")

    for i, request in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}/{len(test_cases)}")
        print(f"{'='*80}")
        print(f"Request: {request}")

        result = await analyzer.analyze(request)

        print(f"\nRESULTS:")
        print(f"  NSFW Level: {result.nsfw_level}")
        print(f"  Action: {result.action}")
        print(f"  Objects: {result.objects}")
        print(f"  Location: {result.location}")

        # Check if NSFW level 5 detected
        if result.nsfw_level == 5:
            print(f"\n✅ PASS - NSFW level 5 correctly detected!")
        else:
            print(f"\n❌ FAIL - Expected NSFW 5, got {result.nsfw_level}")

        # Check if action contains explicit terms
        action_lower = result.action.lower() if result.action else ""
        if "oral" in action_lower or "blowjob" in action_lower or "sucking" in action_lower:
            print(f"✅ PASS - Action correctly extracted: {result.action}")
        else:
            print(f"❌ FAIL - Action missing explicit terms: {result.action}")

if __name__ == "__main__":
    asyncio.run(test_nsfw5())
