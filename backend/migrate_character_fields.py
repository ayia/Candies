"""Migration script to add new character appearance fields"""
import sys
import io
from sqlalchemy import text
from database import engine

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def migrate_up():
    """Add new appearance columns to characters table"""

    migrations = [
        # Detailed Face fields
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS hair_style VARCHAR(50);",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS face_shape VARCHAR(30);",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS lip_style VARCHAR(50);",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS nose_shape VARCHAR(30);",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS eyebrow_style VARCHAR(50);",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS skin_tone VARCHAR(50);",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS skin_details VARCHAR(100);",

        # Detailed Body fields
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS waist_type VARCHAR(30);",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS hip_type VARCHAR(30);",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS leg_type VARCHAR(30);",

        # CRITICAL: Custom physical description
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS physical_description TEXT;",
    ]

    print("🔄 Running migration: Adding new character appearance fields...")

    with engine.connect() as conn:
        for i, sql in enumerate(migrations, 1):
            try:
                conn.execute(text(sql))
                conn.commit()
                field_name = sql.split("ADD COLUMN IF NOT EXISTS ")[1].split(" ")[0]
                print(f"  ✅ [{i}/{len(migrations)}] Added column: {field_name}")
            except Exception as e:
                print(f"  ⚠️  [{i}/{len(migrations)}] Error (may already exist): {e}")

    print("\n✅ Migration completed successfully!")
    print("\n📋 New fields added:")
    print("   - hair_style, face_shape, lip_style, nose_shape, eyebrow_style")
    print("   - skin_tone, skin_details")
    print("   - waist_type, hip_type, leg_type")
    print("   - physical_description (CRITICAL for SD prompts)")


def migrate_down():
    """Remove the new appearance columns (rollback)"""

    columns_to_drop = [
        "hair_style", "face_shape", "lip_style", "nose_shape", "eyebrow_style",
        "skin_tone", "skin_details", "waist_type", "hip_type", "leg_type",
        "physical_description"
    ]

    print("⚠️  Rolling back migration: Removing new character appearance fields...")

    with engine.connect() as conn:
        for column in columns_to_drop:
            try:
                sql = f"ALTER TABLE characters DROP COLUMN IF EXISTS {column};"
                conn.execute(text(sql))
                conn.commit()
                print(f"  ✅ Removed column: {column}")
            except Exception as e:
                print(f"  ⚠️  Error removing {column}: {e}")

    print("\n✅ Rollback completed!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        migrate_down()
    else:
        migrate_up()
