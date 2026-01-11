"""
Manual QA Validation - Interactive Testing
==========================================

Interactive QA system to manually validate and verify acceptance criteria
for intent extraction with real-time visual inspection.
"""

import asyncio
import sys
from typing import List, Dict
from services.image_prompt_agents import generate_image_prompt

# Add encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class QAValidator:
    """Interactive QA validation system"""

    def __init__(self):
        self.critical_tests = [
            {
                "id": "QA-001",
                "category": "CRITICAL - Lollipop",
                "request_fr": "Envoie moi une photo de toi en train de sucer une sucette",
                "request_en": "Send me a photo of you sucking a lollipop",
                "expected": {
                    "objects": ["lollipop", "candy"],
                    "action": "sucking",
                    "nsfw": 1,
                    "keywords": ["sucking", "lollipop", "tongue"]
                }
            },
            {
                "id": "QA-002",
                "category": "CRITICAL - Classroom Teacher",
                "request_fr": "Photo sexy de toi en prof dans ta classe",
                "request_en": "Sexy photo of you as a teacher in your classroom",
                "expected": {
                    "objects": ["glasses", "desk", "blackboard"],
                    "action": "standing",
                    "location": "classroom",
                    "nsfw": 1,
                    "keywords": ["classroom", "teacher", "blackboard"]
                }
            },
            {
                "id": "QA-003",
                "category": "Multiple Objects",
                "request_fr": "Photo de toi en train de lire un livre avec un café",
                "request_en": "Photo of you reading a book with coffee",
                "expected": {
                    "objects": ["book", "coffee"],
                    "action": "reading",
                    "nsfw": 0,
                    "keywords": ["book", "coffee", "reading"]
                }
            },
            {
                "id": "QA-004",
                "category": "Action Detection",
                "request_fr": "Montre moi une photo de toi en train de danser",
                "request_en": "Show me a photo of you dancing",
                "expected": {
                    "objects": [],
                    "action": "dancing",
                    "nsfw": 0,
                    "keywords": ["dancing"]
                }
            },
            {
                "id": "QA-005",
                "category": "NSFW Classification - Lingerie",
                "request_fr": "Photo sexy en lingerie",
                "request_en": "Sexy photo in lingerie",
                "expected": {
                    "objects": ["lingerie"],
                    "action": "posing",
                    "nsfw": 1,
                    "keywords": ["lingerie", "sexy"]
                }
            },
            {
                "id": "QA-006",
                "category": "Location - Beach",
                "request_fr": "Photo de toi à la plage",
                "request_en": "Photo of you at the beach",
                "expected": {
                    "objects": [],
                    "action": "standing",
                    "location": "beach",
                    "nsfw": 0,
                    "keywords": ["beach", "sand"]
                }
            },
            {
                "id": "QA-007",
                "category": "Complex - Multiple Elements",
                "request_fr": "Photo de toi dans ta chambre au lit avec un livre et un café",
                "request_en": "Photo of you in your bedroom in bed with a book and coffee",
                "expected": {
                    "objects": ["book", "coffee", "bed"],
                    "action": "lying",
                    "location": "bedroom",
                    "nsfw": 0,
                    "keywords": ["bedroom", "bed", "book", "coffee", "lying"]
                }
            },
            {
                "id": "QA-008",
                "category": "NSFW Level 2 - Topless",
                "request_fr": "Photo topless seins nus",
                "request_en": "Topless photo bare breasts",
                "expected": {
                    "objects": [],
                    "action": "posing",
                    "nsfw": 2,
                    "keywords": ["topless", "bare", "breasts"]
                }
            },
            {
                "id": "QA-009",
                "category": "Action - Biting Lip",
                "request_fr": "Photo en train de te mordre la lèvre",
                "request_en": "Photo biting your lip",
                "expected": {
                    "objects": [],
                    "action": "biting lip",
                    "nsfw": 1,
                    "keywords": ["biting", "lip"]
                }
            },
            {
                "id": "QA-010",
                "category": "Multiple Objects - Work Setup",
                "request_fr": "Photo au travail avec laptop, café et écouteurs",
                "request_en": "Work photo with laptop, coffee and headphones",
                "expected": {
                    "objects": ["laptop", "coffee", "headphones"],
                    "action": "working",
                    "nsfw": 0,
                    "keywords": ["laptop", "coffee", "headphones", "working"]
                }
            }
        ]

    async def validate_test(self, test: Dict, language: str = "fr") -> Dict:
        """Run a single QA test and return results"""

        request = test["request_fr"] if language == "fr" else test["request_en"]
        expected = test["expected"]

        print("\n" + "="*80)
        print(f"🧪 TEST {test['id']}: {test['category']}")
        print("="*80)
        print(f"\n📝 Request ({language.upper()}):")
        print(f"   \"{request}\"")
        print(f"\n🎯 Expected:")
        print(f"   Objects: {expected.get('objects', [])}")
        print(f"   Action: {expected.get('action', 'N/A')}")
        print(f"   Location: {expected.get('location', 'N/A')}")
        print(f"   NSFW: {expected.get('nsfw', 0)}")
        print(f"   Keywords: {expected.get('keywords', [])}")

        # Run extraction
        print(f"\n⏳ Running intent extraction...")

        character_data = {
            "name": "QA Test Character",
            "personality": "friendly, helpful",
            "age": "25",
            "ethnicity": "european"
        }

        try:
            result = await generate_image_prompt(
                user_message=request,
                character_data=character_data,
                relationship_level=0,
                current_mood="neutral",
                conversation_context="",
                style="realistic"
            )

            extracted_objects = result.get("objects", [])
            extracted_action = result.get("action", "")
            extracted_location = result.get("location", "")
            extracted_nsfw = result.get("nsfw_level", 0)
            final_prompt = result.get("prompt", "")

            print(f"\n✅ Extraction Complete!")
            print(f"\n📊 EXTRACTED RESULTS:")
            print(f"   Objects: {extracted_objects}")
            print(f"   Action: {extracted_action}")
            print(f"   Location: {extracted_location}")
            print(f"   NSFW: {extracted_nsfw}")

            print(f"\n📝 GENERATED PROMPT (first 300 chars):")
            print(f"   {final_prompt[:300]}...")

            # Validate each criterion
            print(f"\n🔍 VALIDATION:")

            validation_results = {
                "test_id": test["id"],
                "request": request,
                "passed_checks": [],
                "failed_checks": [],
                "warnings": []
            }

            # Check 1: Objects
            if expected.get("objects"):
                found_objects = sum(1 for exp_obj in expected["objects"]
                                  if any(exp_obj.lower() in ext_obj.lower()
                                        for ext_obj in extracted_objects))
                if found_objects >= len(expected["objects"]) * 0.5:  # 50% match
                    validation_results["passed_checks"].append(f"✅ Objects: {found_objects}/{len(expected['objects'])} found")
                    print(f"   ✅ Objects: {found_objects}/{len(expected['objects'])} found")
                else:
                    validation_results["failed_checks"].append(f"❌ Objects: Only {found_objects}/{len(expected['objects'])} found")
                    print(f"   ❌ Objects: Only {found_objects}/{len(expected['objects'])} found")
                    print(f"      Expected: {expected['objects']}")
                    print(f"      Got: {extracted_objects}")

            # Check 2: Action
            if expected.get("action"):
                action_match = (
                    expected["action"].lower() in extracted_action.lower() or
                    any(word in extracted_action.lower()
                        for word in expected["action"].lower().split())
                )
                if action_match:
                    validation_results["passed_checks"].append(f"✅ Action: '{expected['action']}' detected in '{extracted_action}'")
                    print(f"   ✅ Action: '{expected['action']}' detected in '{extracted_action}'")
                else:
                    validation_results["failed_checks"].append(f"❌ Action: Expected '{expected['action']}', got '{extracted_action}'")
                    print(f"   ❌ Action: Expected '{expected['action']}', got '{extracted_action}'")

            # Check 3: Location
            if expected.get("location"):
                location_match = (
                    expected["location"].lower() in extracted_location.lower() or
                    extracted_location.lower() in expected["location"].lower()
                )
                if location_match:
                    validation_results["passed_checks"].append(f"✅ Location: '{expected['location']}' detected")
                    print(f"   ✅ Location: '{expected['location']}' detected")
                else:
                    validation_results["failed_checks"].append(f"❌ Location: Expected '{expected['location']}', got '{extracted_location}'")
                    print(f"   ❌ Location: Expected '{expected['location']}', got '{extracted_location}'")

            # Check 4: NSFW Level (±1 tolerance)
            nsfw_diff = abs(extracted_nsfw - expected["nsfw"])
            if nsfw_diff == 0:
                validation_results["passed_checks"].append(f"✅ NSFW: Exact match (level {extracted_nsfw})")
                print(f"   ✅ NSFW: Exact match (level {extracted_nsfw})")
            elif nsfw_diff == 1:
                validation_results["warnings"].append(f"⚠️  NSFW: Close (expected {expected['nsfw']}, got {extracted_nsfw})")
                print(f"   ⚠️  NSFW: Close (expected {expected['nsfw']}, got {extracted_nsfw}) - ACCEPTABLE")
            else:
                validation_results["failed_checks"].append(f"❌ NSFW: Too far (expected {expected['nsfw']}, got {extracted_nsfw})")
                print(f"   ❌ NSFW: Too far (expected {expected['nsfw']}, got {extracted_nsfw})")

            # Check 5: Keywords in final prompt
            keywords_found = sum(1 for kw in expected.get("keywords", [])
                                if kw.lower() in final_prompt.lower())
            keywords_total = len(expected.get("keywords", []))

            if keywords_total > 0:
                keyword_ratio = keywords_found / keywords_total
                if keyword_ratio >= 0.7:
                    validation_results["passed_checks"].append(f"✅ Keywords: {keywords_found}/{keywords_total} in prompt ({keyword_ratio*100:.0f}%)")
                    print(f"   ✅ Keywords: {keywords_found}/{keywords_total} in prompt ({keyword_ratio*100:.0f}%)")
                else:
                    missing = [kw for kw in expected["keywords"] if kw.lower() not in final_prompt.lower()]
                    validation_results["failed_checks"].append(f"❌ Keywords: Only {keywords_found}/{keywords_total} in prompt")
                    print(f"   ❌ Keywords: Only {keywords_found}/{keywords_total} in prompt")
                    print(f"      Missing: {missing}")

            # Overall verdict
            total_checks = len(validation_results["passed_checks"]) + len(validation_results["failed_checks"])
            passed_checks = len(validation_results["passed_checks"])
            pass_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0

            validation_results["pass_rate"] = pass_rate
            validation_results["overall_passed"] = len(validation_results["failed_checks"]) == 0

            print(f"\n{'='*80}")
            if validation_results["overall_passed"]:
                print(f"✅ TEST PASSED - {passed_checks}/{total_checks} checks OK ({pass_rate:.0f}%)")
            else:
                print(f"❌ TEST FAILED - {len(validation_results['failed_checks'])} failures, {passed_checks} passed ({pass_rate:.0f}%)")
            print(f"{'='*80}")

            return validation_results

        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            return {
                "test_id": test["id"],
                "request": request,
                "passed_checks": [],
                "failed_checks": [f"Exception: {str(e)}"],
                "warnings": [],
                "pass_rate": 0.0,
                "overall_passed": False
            }

    async def run_qa_suite(self):
        """Run all QA tests"""

        print("\n" + "🔬"*40)
        print("MANUAL QA VALIDATION SUITE")
        print("🔬"*40)
        print(f"\nTotal Tests: {len(self.critical_tests)}")
        print(f"Testing both French and English for each test")
        print(f"Total Validations: {len(self.critical_tests) * 2}")
        print("\n" + "="*80 + "\n")

        all_results = []
        passed_count = 0
        failed_count = 0

        for i, test in enumerate(self.critical_tests, 1):
            print(f"\n{'#'*80}")
            print(f"QA VALIDATION {i}/{len(self.critical_tests)}")
            print(f"{'#'*80}")

            # Test French
            print(f"\n🇫🇷 TESTING FRENCH VERSION:")
            result_fr = await self.validate_test(test, language="fr")
            all_results.append(result_fr)
            if result_fr["overall_passed"]:
                passed_count += 1
            else:
                failed_count += 1

            # Wait a bit
            await asyncio.sleep(1)

            # Test English
            print(f"\n🇬🇧 TESTING ENGLISH VERSION:")
            result_en = await self.validate_test(test, language="en")
            all_results.append(result_en)
            if result_en["overall_passed"]:
                passed_count += 1
            else:
                failed_count += 1

            print(f"\n{'='*80}\n")

            # Wait between tests
            await asyncio.sleep(2)

        # Final report
        total_tests = len(all_results)
        pass_rate = (passed_count / total_tests * 100) if total_tests > 0 else 0

        print("\n" + "🏆"*40)
        print("FINAL QA VALIDATION REPORT")
        print("🏆"*40)
        print(f"\nTotal Validations: {total_tests}")
        print(f"✅ Passed: {passed_count} ({pass_rate:.1f}%)")
        print(f"❌ Failed: {failed_count} ({100-pass_rate:.1f}%)")

        # Acceptance criteria
        print(f"\n📊 ACCEPTANCE CRITERIA:")
        print(f"   Target Pass Rate: ≥ 85%")
        print(f"   Actual Pass Rate: {pass_rate:.1f}%")

        if pass_rate >= 85:
            print(f"\n✅ ✅ ✅ ACCEPTANCE CRITERIA MET! ✅ ✅ ✅")
        elif pass_rate >= 70:
            print(f"\n⚠️  Borderline - Improvements needed")
        else:
            print(f"\n❌ ACCEPTANCE CRITERIA NOT MET")

        # Failed tests detail
        if failed_count > 0:
            print(f"\n\n❌ FAILED TESTS DETAIL:")
            for result in all_results:
                if not result["overall_passed"]:
                    print(f"\n   Test: {result['test_id']}")
                    print(f"   Request: {result['request'][:60]}...")
                    for failure in result["failed_checks"]:
                        print(f"   └─ {failure}")

        print("\n" + "="*80 + "\n")

        return {
            "total": total_tests,
            "passed": passed_count,
            "failed": failed_count,
            "pass_rate": pass_rate,
            "acceptance_met": pass_rate >= 85
        }


async def main():
    """Main entry point"""
    validator = QAValidator()
    results = await validator.run_qa_suite()

    return 0 if results["acceptance_met"] else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
