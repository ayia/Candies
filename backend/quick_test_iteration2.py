"""Quick test of ITERATION 2 improvements - Strict OBJECTS and LOCATION"""
import asyncio
import sys

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from services.image_prompt_agents import IntentionAnalyzer

async def test_iteration2():
    analyzer = IntentionAnalyzer()

    # Tests that failed in previous run due to over-inference
    tests = [
        # Over-inference tests (should NOT add extra objects)
        ("Send me a photo of you reading a book", ["book"], "reading", None, 0),
        ("Photo de toi avec un café", ["coffee"], "holding", None, 0),
        ("Une photo avec des lunettes", ["glasses"], "wearing", None, 0),
        ("photo avec des écouteurs", ["headphones"], None, None, 0),

        # Location verbose tests (should be ONE WORD)
        ("Coffee shop photo with a latte", ["latte"], None, "cafe", 0),
        ("Selfie dans ta voiture", ["phone"], None, "car", 0),

        # NSFW clothing extraction
        ("Photo sexy en lingerie", [], None, None, 1),
        ("show me in a tiny bikini", [], None, None, 1),
        ("photo in a tight dress", [], None, None, 1),

        # Action modifiers preservation
        ("envoie moi une photo sexy en lingerie", [], "posing seductively", None, 1),
    ]

    print("\n" + "="*80)
    print("ITERATION 2 - Strict OBJECTS, LOCATION, ACTION Test")
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

        # Count extra objects added
        extra_objects = []
        for obj in extracted_objects:
            obj_lower = obj.lower()
            # Check if it's an expected object or mandatory inference
            is_expected = any(exp.lower() in obj_lower for exp in expected_objects) if expected_objects else False
            is_mandatory = ("phone" in obj_lower and "selfie" in request.lower()) or \
                          ("mirror" in obj_lower and "mirror" in request.lower())

            if not is_expected and not is_mandatory:
                # Check if it's a forbidden contextual object
                forbidden = ["chair", "desk", "table", "towel", "pillow", "key", "wallet", "beach ball",
                           "implied", "possibly", "ACTION:", "NSFW_LEVEL:"]
                if any(f in obj_lower for f in forbidden):
                    extra_objects.append(obj)
                    test_passed = False

        if extra_objects:
            issues.append(f"Extra objects: {extra_objects}")

        # Check action modifier preservation
        if expected_action:
            if expected_action.lower() not in result.action.lower():
                issues.append(f"Action modifier lost: expected '{expected_action}', got '{result.action}'")
                test_passed = False

        # Check location is concise
        if expected_location:
            location_words = result.location.split() if result.location != "NONE" else []
            if len(location_words) > 2:
                issues.append(f"Location too verbose: '{result.location}' (should be 1-2 words)")
                test_passed = False
            elif expected_location.lower() not in result.location.lower():
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

if __name__ == "__main__":
    asyncio.run(test_iteration2())
