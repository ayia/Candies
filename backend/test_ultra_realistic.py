"""
Test ULTRA REALISTIC image generation with optimized prompts
"""
import sys
import io
import asyncio

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Fix Windows event loop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from image_service_free import free_image_service


async def test_ultra_realistic_portrait():
    """Test 1: Ultra realistic portrait"""
    print("\n" + "="*70)
    print("TEST 1: Ultra Realistic Portrait")
    print("="*70)

    result = await free_image_service.generate(
        prompt=(
            "stunning 25 year old woman with long flowing hair, "
            "piercing green eyes, natural beauty, flawless complexion, "
            "soft natural makeup, gentle smile"
        ),
        nsfw_level=0,
        width=1024,
        height=1024,
        model="flux"
    )

    if result:
        print(f"✅ Portrait: {result}")
    else:
        print("❌ Failed")

    return result


async def test_nsfw_level_1():
    """Test 2: NSFW Level 1 - Sensual"""
    print("\n" + "="*70)
    print("TEST 2: NSFW Level 1 - Sensual")
    print("="*70)

    await asyncio.sleep(3)  # Rate limit

    result = await free_image_service.generate(
        prompt=(
            "beautiful 28 year old woman in luxurious bedroom, "
            "wearing elegant lingerie, sensual pose on silk sheets, "
            "soft romantic lighting, confident seductive gaze"
        ),
        nsfw_level=1,
        width=1024,
        height=1024,
        model="flux"
    )

    if result:
        print(f"✅ Sensual: {result}")
    else:
        print("❌ Failed")

    return result


async def test_nsfw_level_2():
    """Test 3: NSFW Level 2 - Explicit Topless"""
    print("\n" + "="*70)
    print("TEST 3: NSFW Level 2 - Explicit Topless")
    print("="*70)

    await asyncio.sleep(3)

    result = await free_image_service.generate(
        prompt=(
            "gorgeous 26 year old woman with perfect body, "
            "topless nude from waist up, bare breasts visible, "
            "standing in luxury penthouse with city view, "
            "golden hour sunlight through windows, confident pose"
        ),
        nsfw_level=2,
        width=1024,
        height=1024,
        model="flux"
    )

    if result:
        print(f"✅ Topless: {result}")
    else:
        print("❌ Failed")

    return result


async def test_nsfw_level_3():
    """Test 4: NSFW Level 3 - Full Nude"""
    print("\n" + "="*70)
    print("TEST 4: NSFW Level 3 - Full Frontal Nude")
    print("="*70)

    await asyncio.sleep(3)

    result = await free_image_service.generate(
        prompt=(
            "stunning 24 year old woman completely naked, "
            "full frontal nudity, full body nude photo, "
            "lying on bed with white sheets, legs slightly spread, "
            "intimate erotic photography, soft lighting, artistic nude"
        ),
        nsfw_level=3,
        width=1024,
        height=1024,
        model="flux"
    )

    if result:
        print(f"✅ Full Nude: {result}")
    else:
        print("❌ Failed")

    return result


async def test_beach_nude():
    """Test 5: Beach Nude Scene"""
    print("\n" + "="*70)
    print("TEST 5: Beach Nude Scene")
    print("="*70)

    await asyncio.sleep(3)

    result = await free_image_service.generate(
        prompt=(
            "beautiful naked woman on private beach at sunset, "
            "completely nude walking in shallow water, "
            "wet skin glistening, ocean waves, golden hour, "
            "full body nude, artistic beach photography"
        ),
        nsfw_level=3,
        width=1024,
        height=1024,
        model="flux"
    )

    if result:
        print(f"✅ Beach Nude: {result}")
    else:
        print("❌ Failed")

    return result


async def main():
    print("\n" + "="*70)
    print("🔥 ULTRA REALISTIC + NSFW IMAGE GENERATION TEST")
    print("="*70)
    print("\nTesting with OPTIMIZED prompts for maximum photorealism")
    print("and explicit NSFW/nude content...")

    results = []

    # Test 1: Portrait (SFW)
    r1 = await test_ultra_realistic_portrait()
    results.append(("Portrait SFW", r1))

    # Test 2: Sensual (NSFW 1)
    r2 = await test_nsfw_level_1()
    results.append(("Sensual NSFW 1", r2))

    # Test 3: Topless (NSFW 2)
    r3 = await test_nsfw_level_2()
    results.append(("Topless NSFW 2", r3))

    # Test 4: Full Nude (NSFW 3)
    r4 = await test_nsfw_level_3()
    results.append(("Full Nude NSFW 3", r4))

    # Test 5: Beach Nude
    r5 = await test_beach_nude()
    results.append(("Beach Nude", r5))

    # Summary
    print("\n" + "="*70)
    print("📊 FINAL RESULTS")
    print("="*70)

    success_count = 0
    for name, result in results:
        status = "✅ SUCCESS" if result else "❌ FAILED"
        print(f"{name:20s} : {status}")
        if result:
            success_count += 1

    print(f"\n✅ {success_count}/{len(results)} tests passed")

    if success_count > 0:
        print("\n🎨 Generated images saved in: backend/images/")
        print("📸 Check the images to verify photorealism and NSFW quality")
        print("\n💡 Images should now:")
        print("   • Look more like real photographs")
        print("   • Have natural skin texture (pores, imperfections)")
        print("   • Show explicit NSFW/nude content as requested")
        print("   • Have individual hair strands visible")
        print("   • Natural lighting without AI artifacts")
    else:
        print("\n❌ All tests failed - checking connection...")


if __name__ == "__main__":
    asyncio.run(main())
