"""Test script for image generation with new character fields"""
import sys
import io
import asyncio
from database import SessionLocal
from models import Character
from services.image_prompt_agents import CharacterDescriptionAgent, ImagePromptOrchestrator

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def test_basic_character_image_prompt():
    """Test 1: Image prompt from basic character fields"""
    print("\n" + "="*70)
    print("TEST 1: Basic Character Image Prompt")
    print("="*70)

    db = SessionLocal()
    try:
        # Get the basic character we created (ID 7)
        character = db.query(Character).filter(Character.id == 7).first()

        if not character:
            print("❌ Character ID 7 not found. Run test_character_creation.py first.")
            return False

        print(f"\n📋 Character: {character.name}")
        print(f"   - Ethnicity: {character.ethnicity}")
        print(f"   - Hair: {character.hair_length} {character.hair_color}")
        print(f"   - Eyes: {character.eye_color}")
        print(f"   - Body: {character.body_type}")

        # Build character description
        agent = CharacterDescriptionAgent()
        char_dict = {
            "name": character.name,
            "ethnicity": character.ethnicity,
            "age_range": character.age_range,
            "body_type": character.body_type,
            "breast_size": character.breast_size,
            "butt_size": character.butt_size,
            "hair_color": character.hair_color,
            "hair_length": character.hair_length,
            "eye_color": character.eye_color,
        }

        description = agent.build_description(char_dict)

        print(f"\n🎨 Generated Physical Prompt:")
        print(f"   {description.physical_prompt[:300]}...")

        print(f"\n✅ Test passed - Prompt generated from basic fields")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_detailed_character_image_prompt():
    """Test 2: Image prompt from detailed character fields"""
    print("\n" + "="*70)
    print("TEST 2: Detailed Character Image Prompt")
    print("="*70)

    db = SessionLocal()
    try:
        # Get the detailed character (ID 8)
        character = db.query(Character).filter(Character.id == 8).first()

        if not character:
            print("❌ Character ID 8 not found. Run test_character_creation.py first.")
            return False

        print(f"\n📋 Character: {character.name}")
        print(f"   - Hair style: {character.hair_style}")
        print(f"   - Face shape: {character.face_shape}")
        print(f"   - Lip style: {character.lip_style}")
        print(f"   - Skin tone: {character.skin_tone}")
        print(f"   - Waist: {character.waist_type}")
        print(f"   - Hips: {character.hip_type}")

        # Build character description
        agent = CharacterDescriptionAgent()
        char_dict = {
            "name": character.name,
            "ethnicity": character.ethnicity,
            "age_range": character.age_range,
            "body_type": character.body_type,
            "breast_size": character.breast_size,
            "butt_size": character.butt_size,
            "hair_color": character.hair_color,
            "hair_length": character.hair_length,
            "eye_color": character.eye_color,
            # NEW FIELDS
            "hair_style": character.hair_style,
            "face_shape": character.face_shape,
            "lip_style": character.lip_style,
            "nose_shape": character.nose_shape,
            "eyebrow_style": character.eyebrow_style,
            "skin_tone": character.skin_tone,
            "skin_details": character.skin_details,
            "waist_type": character.waist_type,
            "hip_type": character.hip_type,
            "leg_type": character.leg_type,
        }

        description = agent.build_description(char_dict)

        print(f"\n🎨 Generated Physical Prompt (with details):")
        print(f"   {description.physical_prompt[:400]}...")

        # Check if new fields are included
        prompt_lower = description.physical_prompt.lower()
        checks = [
            ("hair style" in prompt_lower or "waves" in prompt_lower, "Hair style"),
            ("oval" in prompt_lower, "Face shape"),
            ("lips" in prompt_lower or "lipstick" in prompt_lower, "Lip style"),
            ("olive" in prompt_lower or "tan" in prompt_lower, "Skin tone"),
            ("waist" in prompt_lower, "Waist type"),
            ("hips" in prompt_lower, "Hip type"),
        ]

        print(f"\n🔍 Field inclusion check:")
        all_passed = True
        for passed, field_name in checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {field_name}: {'Included' if passed else 'Missing'}")
            if not passed:
                all_passed = False

        if all_passed:
            print(f"\n✅ Test passed - All detailed fields included in prompt")
        else:
            print(f"\n⚠️  Some fields missing from prompt")

        return all_passed

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_custom_physical_description():
    """Test 3: Image prompt from custom physical_description (PRIORITY)"""
    print("\n" + "="*70)
    print("TEST 3: Custom Physical Description (CRITICAL PRIORITY)")
    print("="*70)

    db = SessionLocal()
    try:
        # Get the custom character (ID 9)
        character = db.query(Character).filter(Character.id == 9).first()

        if not character:
            print("❌ Character ID 9 not found. Run test_character_creation.py first.")
            return False

        print(f"\n📋 Character: {character.name}")
        print(f"\n🎯 Custom Physical Description (stored in DB):")
        print(f"   {character.physical_description[:200]}...")

        # Build character description
        agent = CharacterDescriptionAgent()
        char_dict = {
            "name": character.name,
            "ethnicity": character.ethnicity,
            "age_range": character.age_range,
            "body_type": character.body_type,
            "hair_color": character.hair_color,
            "eye_color": character.eye_color,
            # CRITICAL: Custom physical description
            "physical_description": character.physical_description,
        }

        description = agent.build_description(char_dict)

        print(f"\n🎨 Generated Physical Prompt:")
        print(f"   {description.physical_prompt}")

        # Check if custom description is used EXACTLY
        if description.physical_prompt.strip() == character.physical_description.strip():
            print(f"\n✅ PERFECT! Custom description used EXACTLY as provided")
            print(f"   This ensures 100% consistency with the intended appearance")
            return True
        else:
            print(f"\n⚠️  Warning: Prompt doesn't match custom description exactly")
            print(f"\n   Expected: {character.physical_description[:100]}...")
            print(f"   Got:      {description.physical_prompt[:100]}...")
            return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_full_image_prompt_builder():
    """Test 4: Complete image prompt with pose/location/outfit"""
    print("\n" + "="*70)
    print("TEST 4: Full Image Prompt Builder")
    print("="*70)

    db = SessionLocal()
    try:
        # Use the detailed character
        character = db.query(Character).filter(Character.id == 8).first()

        if not character:
            print("❌ Character ID 8 not found.")
            return False

        print(f"\n📋 Character: {character.name}")

        # Create prompt orchestrator
        orchestrator = ImagePromptOrchestrator()

        char_dict = {
            "name": character.name,
            "ethnicity": character.ethnicity,
            "age_range": character.age_range,
            "body_type": character.body_type,
            "breast_size": character.breast_size,
            "butt_size": character.butt_size,
            "hair_color": character.hair_color,
            "hair_length": character.hair_length,
            "hair_style": character.hair_style,
            "eye_color": character.eye_color,
            "face_shape": character.face_shape,
            "lip_style": character.lip_style,
            "skin_tone": character.skin_tone,
            "waist_type": character.waist_type,
            "hip_type": character.hip_type,
            "leg_type": character.leg_type,
        }

        # Build full prompt with context
        result = await orchestrator.generate_prompt(
            user_message="Generate an image of her standing confidently with hand on hip in a luxury penthouse wearing an elegant red evening dress",
            character_data=char_dict,
            style="realistic"
        )
        full_prompt = result["prompt"]

        print(f"\n🎨 Full Image Prompt:")
        print(f"   {full_prompt[:500]}...")

        # Check if all elements are present
        prompt_lower = full_prompt.lower()
        checks = [
            ("standing" in prompt_lower or "hand on hip" in prompt_lower, "Pose"),
            ("penthouse" in prompt_lower or "luxury" in prompt_lower, "Location"),
            ("dress" in prompt_lower or "red" in prompt_lower, "Outfit"),
            ("oval" in prompt_lower or "face" in prompt_lower, "Character details"),
        ]

        print(f"\n🔍 Prompt components check:")
        all_passed = True
        for passed, component in checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {component}: {'Included' if passed else 'Missing'}")
            if not passed:
                all_passed = False

        if all_passed:
            print(f"\n✅ Test passed - All components in final prompt")
        else:
            print(f"\n⚠️  Some components missing")

        return all_passed

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def main():
    print("\n" + "="*70)
    print("🧪 IMAGE GENERATION PROMPT TEST SUITE")
    print("="*70)

    # Run all tests
    test1 = test_basic_character_image_prompt()
    test2 = test_detailed_character_image_prompt()
    test3 = test_custom_physical_description()
    test4 = await test_full_image_prompt_builder()

    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"Test 1 (Basic):    {'✅ PASSED' if test1 else '❌ FAILED'}")
    print(f"Test 2 (Detailed): {'✅ PASSED' if test2 else '❌ FAILED'}")
    print(f"Test 3 (Custom):   {'✅ PASSED' if test3 else '❌ FAILED'}")
    print(f"Test 4 (Full):     {'✅ PASSED' if test4 else '❌ FAILED'}")

    if all([test1, test2, test3, test4]):
        print("\n🎉 All tests passed! Image generation system is working correctly.")
        print("\n💡 Key features:")
        print("   ✅ Basic fields automatically generate detailed prompts")
        print("   ✅ Detailed fields enhance prompts with specific features")
        print("   ✅ Custom physical_description provides EXACT control")
        print("   ✅ Full prompts integrate pose/location/outfit correctly")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")


if __name__ == "__main__":
    asyncio.run(main())
