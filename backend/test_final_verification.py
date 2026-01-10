"""
TEST FINAL DE VÉRIFICATION
Génère 5 exemples variés pour s'assurer que tout fonctionne correctement
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from image_service_free import free_image_service


async def run_final_tests():
    """Tests de vérification finale"""

    tests = [
        {
            "name": "Test 1: Portrait SFW",
            "prompt": "young woman with natural beauty, casual home photo",
            "nsfw_level": 0,
            "expected": "Portrait naturel avec imperfections"
        },
        {
            "name": "Test 2: Lingerie Bedroom",
            "prompt": "woman in black lingerie lying on bed, intimate amateur photo",
            "nsfw_level": 1,
            "expected": "Lingerie visible, style amateur"
        },
        {
            "name": "Test 3: Topless Mirror Selfie",
            "prompt": "woman topless taking mirror selfie, bare breasts visible, bedroom",
            "nsfw_level": 2,
            "expected": "Topless avec seins nus et mamelons visibles"
        },
        {
            "name": "Test 4: Full Nude Bedroom",
            "prompt": "woman completely naked on bed, full nude body, casual photo",
            "nsfw_level": 3,
            "expected": "Nudité complète, corps entier nu"
        },
        {
            "name": "Test 5: Beach Casual",
            "prompt": "woman on beach in bikini, casual vacation photo, natural sunlight",
            "nsfw_level": 1,
            "expected": "Bikini plage, style vacances amateur"
        }
    ]

    print("\n" + "="*70)
    print("🔥 TESTS DE VÉRIFICATION FINALE")
    print("="*70)
    print("Objectif: Vérifier cohérence et qualité sur 5 exemples variés")
    print("="*70)

    results = []

    for i, test in enumerate(tests, 1):
        print(f"\n[{i}/5] {test['name']}")
        print(f"Prompt: {test['prompt']}")
        print(f"NSFW Level: {test['nsfw_level']}")
        print(f"Attendu: {test['expected']}")
        print("-" * 70)

        try:
            image_path = await free_image_service.generate(
                prompt=test['prompt'],
                nsfw_level=test['nsfw_level'],
                width=512,
                height=512,
                model="flux"
            )

            if image_path:
                print(f"✅ SUCCESS: {image_path}")
                results.append({
                    "test": test['name'],
                    "status": "SUCCESS",
                    "path": image_path
                })
            else:
                print(f"❌ FAILED: No image generated")
                results.append({
                    "test": test['name'],
                    "status": "FAILED"
                })

            # Wait between requests
            if i < len(tests):
                print("⏱️  Waiting 5s...")
                await asyncio.sleep(5)

        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append({
                "test": test['name'],
                "status": "ERROR",
                "error": str(e)
            })
            await asyncio.sleep(5)

    # Summary
    print("\n" + "="*70)
    print("📊 RÉSUMÉ FINAL")
    print("="*70)

    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')

    for i, result in enumerate(results, 1):
        status_icon = "✅" if result['status'] == 'SUCCESS' else "❌"
        print(f"{status_icon} Test {i}: {result['test']} - {result['status']}")
        if result['status'] == 'SUCCESS':
            print(f"    → {result['path']}")

    print(f"\n{'='*70}")
    print(f"RÉSULTAT: {success_count}/5 tests réussis")
    print(f"{'='*70}")

    if success_count == 5:
        print("\n🎉 TOUS LES TESTS PASSÉS!")
        print("✅ Le service est PRÊT pour la production")
        print("\n📋 Points à vérifier visuellement dans les images:")
        print("  1. Photoréalisme (ressemble à vraie photo amateur?)")
        print("  2. Taches de rousseur / imperfections visibles?")
        print("  3. Cheveux naturels / désordonnés?")
        print("  4. NSFW correct (lingerie/topless/nude selon niveau)?")
        print("  5. Pas de look 'fantasy' ou 'mannequin parfait'?")
    elif success_count >= 3:
        print("\n⚠️  MAJORITÉ DES TESTS PASSÉS")
        print(f"   {success_count}/5 réussis - Vérifier les échecs")
    else:
        print("\n❌ TROP D'ÉCHECS")
        print("   Problème de connexion ou de service")

    print(f"\n📁 Toutes les images: backend/images/")

    return results


if __name__ == "__main__":
    asyncio.run(run_final_tests())
