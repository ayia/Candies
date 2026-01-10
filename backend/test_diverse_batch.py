"""
Test Diverse Batch Generation - 15 varied images across all NSFW levels
Validates diversity and quality improvements
"""
import asyncio
import sys

# Fix Windows event loop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from image_service_v2 import image_service_v2


async def test_complete_diversity():
    """
    Generate 15 diverse images:
    - 5 SFW (level 0)
    - 5 Sensual/Lingerie (level 1)
    - 3 Topless (level 2)
    - 2 Full Nude (level 3)

    Each batch should show different:
    - Ethnicities (European, Asian, African, Latino, etc.)
    - Ages (20s, 30s)
    - Face shapes and features
    - Contexts (bedroom, car, bathroom, etc.)
    """

    print("\n" + "="*70)
    print("🎨 COMPREHENSIVE DIVERSITY TEST - V2 Service")
    print("="*70)
    print("\nObjectif: Générer 15 images TOUTES DIFFÉRENTES")
    print("Critères:")
    print("  ✓ Ethnicités variées (pas toutes caucasiennes)")
    print("  ✓ Âges variés (20s-30s)")
    print("  ✓ Traits faciaux distincts")
    print("  ✓ Contextes variés")
    print("  ✓ PAS de 'same face syndrome'")
    print("="*70)

    all_results = []

    # Batch 1: SFW (5 images)
    print("\n" + "="*70)
    print("BATCH 1: 5 SFW Images (Safe for Work)")
    print("="*70)
    results_sfw = await image_service_v2.generate_batch(
        count=5,
        nsfw_level=0,
        width=1024,
        height=1024,
        delay=3
    )
    all_results.extend(results_sfw)

    # Batch 2: Sensual/Lingerie (5 images)
    print("\n" + "="*70)
    print("BATCH 2: 5 Sensual/Lingerie Images (NSFW 1)")
    print("="*70)
    results_sensual = await image_service_v2.generate_batch(
        count=5,
        nsfw_level=1,
        width=1024,
        height=1024,
        delay=3
    )
    all_results.extend(results_sensual)

    # Batch 3: Topless (3 images)
    print("\n" + "="*70)
    print("BATCH 3: 3 Topless Images (NSFW 2)")
    print("="*70)
    results_topless = await image_service_v2.generate_batch(
        count=3,
        nsfw_level=2,
        width=1024,
        height=1024,
        delay=3
    )
    all_results.extend(results_topless)

    # Batch 4: Full Nude (2 images)
    print("\n" + "="*70)
    print("BATCH 4: 2 Full Nude Images (NSFW 3)")
    print("="*70)
    results_nude = await image_service_v2.generate_batch(
        count=2,
        nsfw_level=3,
        width=1024,
        height=1024,
        delay=3
    )
    all_results.extend(results_nude)

    # Final Summary
    print("\n" + "="*70)
    print("📊 FINAL SUMMARY - DIVERSITY TEST")
    print("="*70)

    success_count = len([r for r in all_results if r])
    print(f"\n✅ Generated: {success_count}/15 images")

    print("\nBreakdown by NSFW Level:")
    print(f"  Level 0 (SFW):     {len([r for r in results_sfw if r])}/5")
    print(f"  Level 1 (Sensual): {len([r for r in results_sensual if r])}/5")
    print(f"  Level 2 (Topless): {len([r for r in results_topless if r])}/3")
    print(f"  Level 3 (Nude):    {len([r for r in results_nude if r])}/2")

    # Diversity stats
    stats = image_service_v2.get_stats()
    print(f"\n📈 Diversity Statistics:")
    print(f"  Total prompts generated: {stats['total_prompts_generated']}")
    print(f"  Diversity enforcement: {stats['diversity_enforcement']}")

    print("\n" + "="*70)
    print("🔍 VALIDATION MANUELLE REQUISE")
    print("="*70)
    print("\nVérifier visuellement chaque image pour:")
    print("  1. Visages TOUS DIFFÉRENTS (ethnicité, traits, âge)")
    print("  2. Imperfections naturelles visibles")
    print("  3. Contextes variés (voiture, lit, miroir, etc.)")
    print("  4. NSFW correct selon le niveau")
    print("  5. Pas de look 'mannequin parfait Instagram'")

    print("\n📁 Toutes les images dans: backend/images/")
    print("\n💡 Compare avec les anciennes images pour voir l'amélioration!")
    print("="*70)

    return all_results


if __name__ == "__main__":
    print("\n🚀 Starting Comprehensive Diversity Test...")
    print("⏱️  Estimated time: ~60 seconds (15 images × 3s delay)")

    results = asyncio.run(test_complete_diversity())

    print("\n✅ Test completed!")
    print(f"📊 Results: {len([r for r in results if r])}/15 successful")
