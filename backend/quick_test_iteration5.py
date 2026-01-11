"""Quick test of ITERATION 5 improvements - SIMPLIFIED prompt"""
import asyncio
import sys

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from services.image_prompt_agents import IntentionAnalyzer

async def test_iteration5():
    analyzer = IntentionAnalyzer()

    # Tests problématiques d'ITERATION 4
    tests = [
        # Over-inference test #7 - should NOT add table+chair
        ("Montre moi une photo avec un verre de vin", ["wine glass"], "holding", None, 0),

        # Missing inference test #37 - should infer desk+computer
        ("Photo professionnelle au bureau", ["desk", "computer"], "working", "office", 0),

        # Location normalization test #40
        ("Coffee shop photo with a latte", ["latte", "phone"], "sitting", "cafe", 0),

        # Action vague test #14
        ("Photo romantique avec du vin et des bougies", ["wine", "candles"], "sitting", None, 0),

        # Wearing vs holding test #9
        ("Une photo avec des écouteurs", ["headphones"], "wearing", None, 0),

        # Location action test #35
        ("Photo de toi dans la cuisine", [], "cooking", "kitchen", 0),

        # NSFW shower test #50
        ("Photo sous la douche", [], None, "bathroom", 2),

        # Location normalization test #33
        ("Selfie dans ta voiture", ["phone"], "taking selfie", "car", 0),

        # Key tests that should still pass
        ("Envoie moi une photo de toi en train de sucer une sucette", ["lollipop"], "sucking lollipop", None, 1),
        ("Photo sexy en lingerie", ["lingerie"], "posing seductively", None, 1),
    ]

    print("\n" + "="*80)
    print("ITERATION 5 - SIMPLIFIED Prompt Test")
    print("="*80 + "\n")

    passed = 0
    failed = 0

    for request, expected_objects, expected_action, expected_location, expected_nsfw in tests:
        result = await analyzer.analyze(request)

        test_passed = True
        issues = []

        # Check objects
        extracted_objects = result.objects if isinstance(result.objects, list) else [result.objects] if result.objects and result.objects != "NONE" else []

        # Check for over-inference (table, chair)
        forbidden = ["table", "chair", "saucer", "menu", "counter"]
        for obj in extracted_objects:
            if any(f in obj.lower() for f in forbidden):
                issues.append(f"Over-inference: {obj}")
                test_passed = False

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
            if any(vague in action_lower for vague in ["not specified", "unspecified", "possibly", "could be"]):
                issues.append(f"Vague action: {result.action}")
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
            print(f"✅ PASS: {request[:60]}")
            passed += 1
        else:
            print(f"❌ FAIL: {request[:60]}")
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
    print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(test_iteration5())
