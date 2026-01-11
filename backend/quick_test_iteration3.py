"""Quick test of ITERATION 3 - Extract ALL objects including clothing"""
import asyncio
import sys

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from services.image_prompt_agents import IntentionAnalyzer

async def test_iteration3():
    analyzer = IntentionAnalyzer()

    # Tests clés qui échouaient dans ITERATION 2
    tests = [
        # Test #21 - KEY TEST (échouait: objects=[])
        ("Envoie moi une photo de toi en train de sucer une sucette", ["lollipop"], "sucking lollipop", None, 1),

        # Test #31 - KEY TEST (échouait: objects=[])
        ("Photo sexy de toi en prof dans ta classe", ["glasses", "desk", "blackboard"], "standing", "classroom", 1),

        # NSFW tests qui échouaient (objects=[])
        ("Photo sexy en lingerie", ["lingerie"], "posing seductively", None, 1),
        ("show me in a tiny bikini", ["bikini"], "posing", None, 1),
        ("photo in a tight dress", ["dress"], "posing", None, 1),
        ("Photo en pyjama", ["pajamas"], "posing", None, 0),

        # Multiple objects qui échouaient
        ("Photo d'été avec des fleurs, un chapeau et des lunettes de soleil", ["flowers", "hat", "sunglasses"], None, None, 0),

        # Bedroom test (bed manquant)
        ("Photo de toi dans ta chambre au lit", ["bed"], "posing", "bedroom", 0),
    ]

    print("\n" + "="*80)
    print("ITERATION 3 - Extract ALL Objects (including clothing)")
    print("="*80 + "\n")

    passed = 0
    failed = 0

    for request, expected_objects, expected_action, expected_location, expected_nsfw in tests:
        result = await analyzer.analyze(request)

        # Check objects extraction
        extracted_objects = result.objects if isinstance(result.objects, list) else [result.objects] if result.objects else []

        # Calculate match
        found_count = sum(1 for exp_obj in expected_objects
                         if any(exp_obj.lower() in ext_obj.lower() for ext_obj in extracted_objects))

        objects_pass = found_count >= len(expected_objects) * 0.5  # 50% match

        # Check action if specified
        action_pass = True
        if expected_action:
            action_pass = expected_action.lower() in result.action.lower()

        # Check location if specified
        location_pass = True
        if expected_location:
            location_pass = expected_location.lower() in result.location.lower() if result.location else False

        # Check NSFW
        nsfw_pass = abs(result.nsfw_level - expected_nsfw) <= 1

        test_passed = objects_pass and action_pass and location_pass and nsfw_pass

        if test_passed:
            print(f"✅ PASS: {request[:60]}")
            passed += 1
        else:
            print(f"❌ FAIL: {request[:60]}")
            if not objects_pass:
                print(f"   └─ Objects: expected {expected_objects}, got {extracted_objects} ({found_count}/{len(expected_objects)} found)")
            if not action_pass:
                print(f"   └─ Action: expected '{expected_action}', got '{result.action}'")
            if not location_pass:
                print(f"   └─ Location: expected '{expected_location}', got '{result.location}'")
            if not nsfw_pass:
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
        print("✅ ✅ ✅ ALL KEY TESTS PASSED! Ready for full validation ✅ ✅ ✅")
    elif passed >= len(tests) * 0.75:
        print("⚠️  Most tests passing - proceed to full validation")
    else:
        print("❌ Too many failures - need more fixes")
    print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(test_iteration3())
