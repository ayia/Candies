"""Test script for creating a character with new detailed fields"""
import sys
import io
from database import SessionLocal
from models import Character
from prompt_builder import build_system_prompt

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def test_basic_character():
    """Test 1: Create character with basic fields only"""
    print("\n" + "="*60)
    print("TEST 1: Basic Character Creation")
    print("="*60)

    db = SessionLocal()
    try:
        character_data = {
            "name": "Sophie Basic",
            "style": "realistic",
            "ethnicity": "european",
            "age_range": "25-30",
            "body_type": "slim",
            "breast_size": "medium",
            "butt_size": "round",
            "hair_color": "blonde",
            "hair_length": "long",
            "eye_color": "blue",
        }

        # Create character directly
        character = Character(**character_data)
        character.system_prompt = build_system_prompt(character_data)

        db.add(character)
        db.commit()
        db.refresh(character)

        print(f"\n✅ Character created: {character.name} (ID: {character.id})")
        print(f"   System prompt length: {len(character.system_prompt or '')} chars")
        print(f"\n📝 First 200 chars of system prompt:")
        print(f"   {(character.system_prompt or '')[:200]}...")

        return character.id

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()


def test_detailed_character():
    """Test 2: Create character with ALL detailed fields"""
    print("\n" + "="*60)
    print("TEST 2: Detailed Character Creation")
    print("="*60)

    db = SessionLocal()
    try:
        character_data = {
            "name": "Isabella Detailed",
            "style": "realistic",

            # Basic
            "ethnicity": "latina",
            "age_range": "28-32",
            "body_type": "curvy",
            "breast_size": "large",
            "butt_size": "round",
            "hair_color": "dark brown",
            "hair_length": "long",
            "eye_color": "brown",

            # Detailed Face
            "hair_style": "loose waves with side part",
            "face_shape": "oval",
            "lip_style": "full plump lips with red lipstick",
            "nose_shape": "small straight",
            "eyebrow_style": "arched dark brows",
            "skin_tone": "tan olive",
            "skin_details": "smooth flawless skin with natural glow",

            # Detailed Body
            "waist_type": "narrow waist",
            "hip_type": "wide hips",
            "leg_type": "long toned legs",
        }

        # Create character directly
        character = Character(**character_data)
        character.system_prompt = build_system_prompt(character_data)

        db.add(character)
        db.commit()
        db.refresh(character)

        print(f"\n✅ Character created: {character.name} (ID: {character.id})")
        print(f"\n📋 Detailed fields saved:")
        print(f"   - Hair style: {character.hair_style}")
        print(f"   - Face shape: {character.face_shape}")
        print(f"   - Lip style: {character.lip_style}")
        print(f"   - Skin tone: {character.skin_tone}")
        print(f"   - Waist: {character.waist_type}")
        print(f"   - Hips: {character.hip_type}")
        print(f"   - Legs: {character.leg_type}")

        print(f"\n📝 System prompt length: {len(character.system_prompt or '')} chars")
        print(f"\n📝 First 300 chars of system prompt:")
        print(f"   {(character.system_prompt or '')[:300]}...")

        return character.id

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()


def test_custom_physical_description():
    """Test 3: Create character with custom physical_description (PRIORITY)"""
    print("\n" + "="*60)
    print("TEST 3: Custom Physical Description (PRIORITY)")
    print("="*60)

    db = SessionLocal()
    try:
        # Custom SD prompt for exact control
        custom_prompt = """stunning 28 year old woman, exotic middle eastern beauty, piercing green eyes with long lashes,
        high cheekbones, full pouty lips with nude gloss, straight black hair cascading past shoulders,
        sun-kissed bronze skin with subtle freckles across nose, hourglass figure with narrow waist and wide hips,
        long graceful neck, elegant posture, confident expression, natural beauty, photorealistic"""

        character_data = {
            "name": "Layla Custom",
            "style": "realistic",
            "ethnicity": "middle-eastern",
            "age_range": "28-32",

            # CRITICAL: Custom physical description overrides all other fields
            "physical_description": custom_prompt,

            # These are still stored for metadata but won't affect image generation
            "body_type": "curvy",
            "hair_color": "black",
            "eye_color": "green",
        }

        # Create character directly
        character = Character(**character_data)
        character.system_prompt = build_system_prompt(character_data)

        db.add(character)
        db.commit()
        db.refresh(character)

        print(f"\n✅ Character created: {character.name} (ID: {character.id})")
        print(f"\n🎯 CUSTOM PHYSICAL DESCRIPTION:")
        print(f"   {character.physical_description}")

        print(f"\n📝 System prompt will use the custom description for images")

        return character.id

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()


def main():
    print("\n" + "="*60)
    print("🧪 CHARACTER CREATION TEST SUITE")
    print("="*60)

    # Test all three scenarios
    char1_id = test_basic_character()
    char2_id = test_detailed_character()
    char3_id = test_custom_physical_description()

    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"Test 1 (Basic):   {'✅ PASSED' if char1_id else '❌ FAILED'}")
    print(f"Test 2 (Detailed): {'✅ PASSED' if char2_id else '❌ FAILED'}")
    print(f"Test 3 (Custom):   {'✅ PASSED' if char3_id else '❌ FAILED'}")

    if all([char1_id, char2_id, char3_id]):
        print("\n🎉 All tests passed! Character IDs:", [char1_id, char2_id, char3_id])
    else:
        print("\n⚠️  Some tests failed. Check errors above.")


if __name__ == "__main__":
    main()
