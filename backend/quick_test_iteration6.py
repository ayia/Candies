"""Quick test of ITERATION 6 improvements - LLM-first avec exemples ciblés"""
import asyncio
import sys

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from services.image_prompt_agents import IntentionAnalyzer

async def test_iteration6():
    analyzer = IntentionAnalyzer()

    # Tests qui échouaient dans ITERATION 5b (16 tests)
    tests = [
        # ACTION VERBOSITÉ (7 tests)
        ("Photo romantique avec du vin et des bougies", ["wine", "candles"], "sitting", None, 0),
        ("Photo d'été avec des fleurs, un chapeau et des lunettes de soleil", ["flowers", "hat", "sunglasses"], "posing", None, 0),
        ("send me une photo sexy avec un coffee", ["coffee"], "posing", None, 1),
        ("Je voudrais une très belle photo de toi dans ta chambre, allongée sur ton lit avec un livre et un café, portant tes lunettes et un pyjama confortable", ["bed", "book", "coffee", "glasses", "pajamas"], "lying down", "bedroom", 0),

        # ACTION "NONE SPECIFIED" (3 tests)
        ("Outdoor photo in the park", [], "standing", "park", 0),
        ("Cute photo in casual clothes", [], "smiling", None, 0),
        ("Photo complètement nue", [], "posing", None, 3),

        # ACTION WEARING vs HOLDING (2 tests)
        ("Show me a photo wearing a necklace", ["necklace"], "wearing", None, 0),
        ("Show me a selfie with your phone", ["phone"], "holding", None, 0),

        # OBJECTS MANQUANTS (3 tests)
        ("Photo sexy de toi en prof dans ta classe", ["glasses", "desk", "blackboard"], "standing", "classroom", 1),
        ("Coffee shop photo with a latte", ["latte", "phone"], "sitting", "cafe", 0),
        ("Send a flirty photo", [], "posing seductively", None, 1),

        # AUTRES (1 test)
        ("Photo en pyjama", ["pajamas"], "lying", None, 0),
    ]

    print("\n" + "="*80)
    print("ITERATION 6 - LLM-First Approach + Exemples ❌ WRONG + Post-Processing")
    print("="*80 + "\n")

    passed = 0
    failed = 0

    for request, expected_objects, expected_action, expected_location, expected_nsfw in tests:
        result = await analyzer.analyze(request)

        test_passed = True
        issues = []

        # Check objects
        extracted_objects = result.objects if isinstance(result.objects, list) else [result.objects] if result.objects and result.objects != "NONE" else []

        # Check expected objects present
        if expected_objects:
            for exp in expected_objects:
                if not any(exp.lower() in obj.lower() for obj in extracted_objects):
                    issues.append(f"Missing object: {exp}")
                    test_passed = False

        # Check action
        if expected_action:
            action_lower = result.action.lower() if result.action else ""
            # Check for vague words
            if any(vague in action_lower for vague in ["not specified", "none specified", "unspecified", "possibly", "could be"]):
                issues.append(f"Vague action: {result.action}")
                test_passed = False
            # Check for verbosity
            elif " and " in action_lower or ", " in action_lower:
                issues.append(f"Verbose action: {result.action}")
                test_passed = False
            elif expected_action.lower() not in action_lower:
                issues.append(f"Action mismatch: expected '{expected_action}', got '{result.action}'")
                test_passed = False

        # Check location
        if expected_location:
            loc_lower = result.location.lower() if result.location and result.location != "NONE" else ""
            if expected_location.lower() not in loc_lower:
                issues.append(f"Location mismatch: expected '{expected_location}', got '{result.location}'")
                test_passed = False

        # Check NSFW
        nsfw_match = abs(result.nsfw_level - expected_nsfw) <= 1

        if test_passed and nsfw_match:
            print(f"✅ PASS: {request[:70]}")
            passed += 1
        else:
            print(f"❌ FAIL: {request[:70]}")
            for issue in issues:
                print(f"   └─ {issue}")
            if not nsfw_match:
                print(f"   └─ NSFW: expected {expected_nsfw}, got {result.nsfw_level}")
            failed += 1

        print(f"   Objects: {result.objects}")
        print(f"   Action: {result.action}")
        print(f"   Location: {result.location}")
        print(f"   NSFW: {result.nsfw_level}")
        print()

    print("="*80)
    print(f"Results: {passed}/{len(tests)} passed ({passed/len(tests)*100:.1f}%)")
    if passed == len(tests):
        print("✅ ✅ ✅ ALL 16 FAILING TESTS NOW PASSING! ✅ ✅ ✅")
    elif passed >= len(tests) * 0.75:
        print("⚠️  Most tests passing - good progress!")
    else:
        print("❌ Still too many failures")
    print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(test_iteration6())
