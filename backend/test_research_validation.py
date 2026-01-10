"""
Test existing image prompts against research-based validation criteria.
Tests all NSFW levels and ethnicities to ensure quality.
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from image_quality_validator_v3 import FluxRawPromptGenerator
from research_based_validator import ResearchBasedValidator, print_validation_report


def main():
    print("\n" + "="*80)
    print("🔬 RESEARCH-BASED VALIDATION TEST")
    print("="*80)
    print("\nTesting our prompt generator against research-based acceptance criteria")
    print("Target: ≥ 9.0/10 composite score")
    print(f"{'='*80}\n")

    generator = FluxRawPromptGenerator()
    validator = ResearchBasedValidator()

    # Test cases: different NSFW levels and ethnicities
    test_cases = [
        {"name": "SFW - East Asian", "nsfw": 0, "ethnicity": "East Asian", "age": "mid 20s"},
        {"name": "SFW - African", "nsfw": 0, "ethnicity": "African", "age": "early 30s"},
        {"name": "Lingerie - Latino", "nsfw": 1, "ethnicity": "Latino", "age": "late 20s"},
        {"name": "Topless - European", "nsfw": 2, "ethnicity": "European", "age": "mid 20s"},
        {"name": "Full Nude - Middle-Eastern", "nsfw": 3, "ethnicity": "Middle-Eastern", "age": "early 30s"},
        {"name": "Full Nude - Mixed race", "nsfw": 3, "ethnicity": "Mixed race", "age": "late 20s"},
    ]

    results = []
    passed_count = 0
    total_count = len(test_cases)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'#'*80}")
        print(f"TEST {i}/{total_count}: {test_case['name']}")
        print(f"{'#'*80}\n")

        # Generate prompt
        prompt, negative = generator.generate_flux_raw_prompt(
            nsfw_level=test_case["nsfw"],
            previous_prompts=[],
            include_hands=True
        )

        print(f"📝 Generated Prompt:\n{prompt}\n")

        # Validate with research-based criteria
        validation_results = validator.validate_comprehensive(prompt)

        # Print detailed report
        print_validation_report(prompt, validation_results)

        # Store results
        results.append({
            "test_name": test_case['name'],
            "score": validation_results['composite_score'],
            "passed": validation_results['passed'],
            "recommendation": validation_results['recommendation']
        })

        if validation_results['passed']:
            passed_count += 1

        print(f"\n{'='*80}\n")

    # Summary
    print("\n" + "="*80)
    print("📊 FINAL SUMMARY")
    print("="*80)
    print(f"\n✅ Passed: {passed_count}/{total_count} ({100*passed_count/total_count:.1f}%)")
    print(f"\nTarget: ≥ 9.0/10 for all test cases\n")

    print(f"{'='*80}")
    print("Individual Results:")
    print(f"{'='*80}")
    for result in results:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"{status} | {result['test_name']:30s} | Score: {result['score']:.2f}/10")

    # Calculate average
    avg_score = sum(r['score'] for r in results) / len(results)
    print(f"\n{'='*80}")
    print(f"📈 Average Score: {avg_score:.2f}/10")
    print(f"{'='*80}")

    if passed_count == total_count and avg_score >= 9.5:
        print("\n🎉 EXCELLENT! All tests passed with high scores!")
        print("✅ Ready for production deployment.")
    elif passed_count == total_count:
        print("\n✅ All tests passed acceptance threshold (≥9.0)")
        print(f"⚠️  Average {avg_score:.2f} < 9.5 target. Consider minor improvements.")
    elif passed_count >= total_count * 0.8:
        print(f"\n⚠️  {passed_count}/{total_count} tests passed. Improvements needed.")
    else:
        print(f"\n❌ Only {passed_count}/{total_count} tests passed. Significant improvements required.")

    # Identify weakest areas
    print(f"\n{'='*80}")
    print("🔍 IMPROVEMENT RECOMMENDATIONS:")
    print(f"{'='*80}")

    failed_tests = [r for r in results if not r['passed']]
    if failed_tests:
        print("\nFailed test cases:")
        for test in failed_tests:
            print(f"  • {test['test_name']}: {test['score']:.2f}/10")
    else:
        print("\n✅ All tests passed! Focus on reaching 9.5/10 average:")

        # Find lowest scoring tests
        sorted_results = sorted(results, key=lambda x: x['score'])
        print("\nLowest scoring (opportunities for improvement):")
        for result in sorted_results[:3]:
            print(f"  • {result['test_name']}: {result['score']:.2f}/10")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
