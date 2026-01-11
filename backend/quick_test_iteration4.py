"""Quick test of ITERATION 4 improvements - NO over-inference + SPECIFIC actions"""
import asyncio
import sys

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from services.image_prompt_agents import IntentionAnalyzer

async def test_iteration4():
    analyzer = IntentionAnalyzer()

    # Tests targeting ITERATION 4 fixes
    tests = [
        # Over-inference tests (should NOT add environmental objects)
        ("Coffee shop photo with a latte", ["latte", "phone"], "sitting", "cafe", 0),
        ("Photo professionnelle au bureau", ["desk", "computer"], None, "office", 0),

        # Action specificity tests (should be SPECIFIC, not generic "posing")
        ("photo de toi dans ta chambre au lit", ["bed"], "lying", "bedroom", 0),
        ("photo at the gym working out", [], "working out", "gym", 0),
        ("send me a photo blowing a kiss", [], "blowing kiss", None, 0),
        ("photo of you dancing", [], "dancing", None, 0),
        ("show me you lying down relaxed", [], "lying down", None, 0),

        # Clothing extraction (should still work)
        ("photo in a tight dress", ["dress"], None, None, 1),
        ("Photo sexy en lingerie", ["lingerie"], "posing seductively", None, 1),

        # Complex tests that were passing (should still pass)
        ("Envoie moi une photo de toi en train de sucer une sucette", ["lollipop"], "sucking lollipop", None, 1),
    ]

    print("\n" + "="*80)
    print("ITERATION 4 - NO Over-Inference + SPECIFIC Actions Test")
    print("="*80 + "\n")

    passed = 0
    failed = 0

    for request, expected_objects, expected_action, expected_location, expected_nsfw in tests:
        result = await analyzer.analyze(request)

        # Determine pass/fail
        test_passed = True
        issues = []

        # Check objects (should be minimal, no over-inference)
        extracted_objects = result.objects if isinstance(result.objects, list) else [result.objects] if result.objects and result.objects != "NONE" else []

        # Check for over-inference (environmental objects that shouldn't be there)
        forbidden_objects = ["saucer", "table", "chair", "menu", "counter", "barista", "apron",
                           "towel", "pillow", "beach ball", "wallet", "key"]
        extra_objects = []
        for obj in extracted_objects:
            obj_lower = obj.lower()
            if any(forbidden in obj_lower for forbidden in forbidden_objects):
                extra_objects.append(obj)
                test_passed = False

        if extra_objects:
            issues.append(f"Over-inference detected: {extra_objects}")

        # Check expected objects are present
        if expected_objects:
            for exp_obj in expected_objects:
                if not any(exp_obj.lower() in obj.lower() for obj in extracted_objects):
                    issues.append(f"Missing expected object: '{exp_obj}'")
                    test_passed = False

        # Check action specificity
        if expected_action:
            action_lower = result.action.lower() if result.action else ""
            if expected_action.lower() not in action_lower:
                issues.append(f"Action mismatch: expected '{expected_action}', got '{result.action}'")
                test_passed = False
            elif "posing" in action_lower and "posing" not in expected_action.lower():
                issues.append(f"Action too generic: got '{result.action}' instead of specific action")
                test_passed = False

        # Check location
        if expected_location:
            location_lower = result.location.lower() if result.location and result.location != "NONE" else ""
            if expected_location.lower() not in location_lower:
                issues.append(f"Location mismatch: expected '{expected_location}', got '{result.location}'")
                test_passed = False

        # Check NSFW level
        nsfw_match = abs(result.nsfw_level - expected_nsfw) <= 1

        if test_passed and nsfw_match:
            print(f"✅ PASS: {request}")
            passed += 1
        else:
            print(f"❌ FAIL: {request}")
            for issue in issues:
                print(f"   └─ {issue}")
            if not nsfw_match:
                print(f"   └─ NSFW mismatch: expected {expected_nsfw}, got {result.nsfw_level}")
            failed += 1

        print(f"   Objects: {result.objects}")
        print(f"   Action: {result.action}")
        print(f"   Location: {result.location}")
        print(f"   NSFW: {result.nsfw_level}")
        print()

    print("="*80)
    print(f"Results: {passed}/{len(tests)} passed ({passed/len(tests)*100:.1f}%)")
    print("="*80 + "\n")

    return passed, len(tests)

if __name__ == "__main__":
    asyncio.run(test_iteration4())
