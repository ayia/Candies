"""Quick test of ITERATION 1 improvements"""
import asyncio
import sys

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from services.image_prompt_agents import IntentionAnalyzer

async def test_improvements():
    analyzer = IntentionAnalyzer()

    tests = [
        ("photo sexy en lingerie", ["lingerie"], "posing seductively", None, 1),
        ("show me in a tiny bikini", ["bikini"], "posing", None, 1),
        ("photo in a tight dress", ["tight dress"], "posing", None, 1),
        ("bathroom mirror selfie", ["phone", "mirror"], "taking selfie", "bathroom", 0),
        ("photo de toi dans ta chambre au lit", ["bed"], "posing or lying", "bedroom", 0),
        ("photo avec des lunettes", ["glasses"], "wearing glasses", None, 0),
    ]

    print("\n" + "="*80)
    print("ITERATION 1 - Quick Test Results")
    print("="*80 + "\n")

    passed = 0
    failed = 0

    for request, expected_objects, expected_action, expected_location, expected_nsfw in tests:
        result = await analyzer.analyze(request)

        # Check objects
        objects_match = any(exp_obj.lower() in str(result.objects).lower() for exp_obj in expected_objects) if expected_objects else True

        # Check action
        action_match = expected_action.lower() in result.action.lower() if expected_action else True

        # Check location
        location_match = (expected_location is None and result.location == "NONE") or \
                        (expected_location and expected_location.lower() in result.location.lower())

        # Check NSFW
        nsfw_match = abs(result.nsfw_level - expected_nsfw) <= 1

        test_passed = objects_match and action_match and location_match and nsfw_match

        if test_passed:
            print(f"✅ PASS: {request}")
            passed += 1
        else:
            print(f"❌ FAIL: {request}")
            failed += 1

        print(f"   Expected: objects={expected_objects}, action={expected_action}, location={expected_location}, nsfw={expected_nsfw}")
        print(f"   Got:      objects={result.objects}, action={result.action}, location={result.location}, nsfw={result.nsfw_level}")
        print()

    print("="*80)
    print(f"Results: {passed}/{len(tests)} passed ({passed/len(tests)*100:.1f}%)")
    print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(test_improvements())
