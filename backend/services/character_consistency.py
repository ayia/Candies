"""
Character Consistency Service
Inspired by DreamBooth and LoRA techniques for maintaining visual consistency

This service provides:
1. Character visual signatures for consistent image generation
2. Dynamic prompt building with consistency tokens
3. Seed management for reproducible results
4. Face/feature anchoring techniques
"""

import hashlib
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


@dataclass
class CharacterSignature:
    """Visual signature for a character"""
    character_id: int
    base_seed: int
    face_tokens: str          # Tokens describing unique facial features
    body_tokens: str          # Tokens describing body type
    style_tokens: str         # Tokens describing art style
    negative_tokens: str      # What to avoid for this character
    reference_prompts: List[str]  # Anchor prompts that produced good results

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "CharacterSignature":
        return cls(**data)


class CharacterConsistencyService:
    """
    Service to maintain visual consistency across generated images

    Techniques used:
    1. Consistent seed derivation from character attributes
    2. Face/body anchor tokens that describe unique features
    3. Negative prompt augmentation to avoid inconsistency
    4. Reference prompt tracking for successful generations
    """

    # Ethnicity to detailed face tokens mapping
    ETHNICITY_FACE_TOKENS = {
        "caucasian": "caucasian european woman, fair skin, western facial features, defined cheekbones",
        "asian": "asian woman, east asian features, almond eyes, smooth skin, delicate features",
        "latina": "latina hispanic woman, warm tan skin, full lips, expressive eyes",
        "african": "black african woman, dark brown skin, full lips, beautiful dark features",
        "indian": "indian south asian woman, brown skin, dark expressive eyes, elegant features",
        "arab": "middle eastern arab woman, olive skin, dark eyes, elegant nose",
        "mixed": "mixed race woman, exotic unique features, beautiful blend of features"
    }

    # Body type to detailed tokens
    BODY_TYPE_TOKENS = {
        "slim": "slim slender body, thin waist, lean figure, graceful proportions",
        "curvy": "curvy voluptuous body, wide hips, hourglass figure, feminine curves",
        "athletic": "athletic fit body, toned muscles, defined abs, strong physique",
        "petite": "petite small frame, delicate body, compact proportions",
        "thick": "thick curvy body, wide hips, full thighs, generous proportions",
        "average": "average natural body, balanced proportions, normal build"
    }

    # Breast size tokens
    BREAST_TOKENS = {
        "small": "small perky breasts, A-B cup, petite chest",
        "medium": "medium natural breasts, C cup, balanced proportions",
        "large": "large full breasts, D-DD cup, heavy chest",
        "very large": "huge massive breasts, F+ cup, enormous bust"
    }

    # Style tokens for art style consistency
    STYLE_TOKENS = {
        "realistic": "photorealistic, RAW photo, 8k uhd, dslr quality, realistic skin texture, natural lighting",
        "anime": "anime style, 2d illustration, cel shaded, anime aesthetic, vibrant colors",
        "semi-realistic": "semi-realistic, digital art, detailed illustration, soft rendering"
    }

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None

        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                print("[CharacterConsistency] Redis connected")
            except Exception as e:
                print(f"[CharacterConsistency] Redis error: {e}")

        # In-memory cache
        self.signature_cache: Dict[int, CharacterSignature] = {}
        print("[CharacterConsistency] Service initialized")

    def _generate_base_seed(self, character: Dict) -> int:
        """Generate a consistent base seed from character attributes"""
        # Create a stable hash from key attributes
        seed_string = "|".join([
            str(character.get("id", 0)),
            str(character.get("name", "")),
            str(character.get("ethnicity", "")),
            str(character.get("hair_color", "")),
            str(character.get("eye_color", ""))
        ])

        # Generate seed from hash
        hash_value = int(hashlib.md5(seed_string.encode()).hexdigest()[:8], 16)
        return hash_value % 2147483647

    def _build_face_tokens(self, character: Dict) -> str:
        """Build detailed face description tokens"""
        parts = []

        # Ethnicity base
        ethnicity = (character.get("ethnicity") or "caucasian").lower()
        parts.append(self.ETHNICITY_FACE_TOKENS.get(ethnicity, self.ETHNICITY_FACE_TOKENS["caucasian"]))

        # Age
        age = character.get("age_range", "25")
        if age:
            parts.append(f"{age} years old")

        # Eyes
        eye_color = (character.get("eye_color") or "brown").lower()
        parts.append(f"beautiful {eye_color} eyes, detailed eyes, expressive gaze")

        # Hair
        hair_color = (character.get("hair_color") or "brown").lower()
        hair_length = (character.get("hair_length") or "long").lower()
        parts.append(f"{hair_length} {hair_color} hair, detailed hair strands")

        # Face quality
        parts.append("detailed face, perfect symmetry, clear skin, natural beauty")

        return ", ".join(parts)

    def _build_body_tokens(self, character: Dict) -> str:
        """Build detailed body description tokens"""
        parts = []

        # Body type
        body_type = (character.get("body_type") or "average").lower()
        parts.append(self.BODY_TYPE_TOKENS.get(body_type, self.BODY_TYPE_TOKENS["average"]))

        # Breast size
        breast_size = (character.get("breast_size") or "medium").lower()
        parts.append(self.BREAST_TOKENS.get(breast_size, self.BREAST_TOKENS["medium"]))

        # Butt size
        butt_size = (character.get("butt_size") or "medium").lower()
        butt_map = {
            "small": "small tight butt",
            "medium": "round shapely butt",
            "round": "round plump butt, bubble butt",
            "large": "big round ass, wide hips"
        }
        parts.append(butt_map.get(butt_size, "shapely posterior"))

        return ", ".join(parts)

    def _build_negative_tokens(self, character: Dict) -> str:
        """Build negative prompt tokens to avoid inconsistency"""
        base_negative = [
            "ugly", "deformed", "blurry", "bad anatomy", "watermark", "text",
            "extra fingers", "mutated hands", "poorly drawn face", "mutation",
            "bad proportions", "extra limbs", "disfigured", "gross proportions",
            "malformed limbs", "missing arms", "missing legs", "extra arms",
            "fused fingers", "too many fingers", "long neck", "cross-eyed"
        ]

        # Add style-specific negatives
        style = (character.get("style") or "realistic").lower()
        if style == "realistic":
            base_negative.extend(["cartoon", "anime", "3d render", "illustration", "painting", "drawing"])
        elif style == "anime":
            base_negative.extend(["realistic", "photo", "3d", "uncanny valley"])

        # Add ethnicity-based negatives to prevent confusion
        ethnicity = (character.get("ethnicity") or "").lower()
        ethnicity_negatives = {
            "caucasian": ["asian features", "dark skin", "african features"],
            "asian": ["western features", "european features", "dark skin"],
            "african": ["pale skin", "asian features", "caucasian features"],
            "latina": ["pale skin", "asian features"],
            "indian": ["pale skin", "asian features", "african features"]
        }
        base_negative.extend(ethnicity_negatives.get(ethnicity, []))

        return ", ".join(base_negative)

    def create_signature(self, character: Dict) -> CharacterSignature:
        """Create a visual signature for a character"""
        char_id = character.get("id", 0)

        signature = CharacterSignature(
            character_id=char_id,
            base_seed=self._generate_base_seed(character),
            face_tokens=self._build_face_tokens(character),
            body_tokens=self._build_body_tokens(character),
            style_tokens=self.STYLE_TOKENS.get(
                (character.get("style") or "realistic").lower(),
                self.STYLE_TOKENS["realistic"]
            ),
            negative_tokens=self._build_negative_tokens(character),
            reference_prompts=[]
        )

        # Cache it
        self.signature_cache[char_id] = signature

        # Store in Redis
        if self.redis_client:
            try:
                key = f"casdy:signature:{char_id}"
                self.redis_client.set(key, json.dumps(signature.to_dict()), ex=86400 * 30)
            except Exception as e:
                print(f"[CharacterConsistency] Redis save error: {e}")

        return signature

    def get_signature(self, character: Dict) -> CharacterSignature:
        """Get or create signature for a character"""
        char_id = character.get("id", 0)

        # Check cache
        if char_id in self.signature_cache:
            return self.signature_cache[char_id]

        # Check Redis
        if self.redis_client:
            try:
                key = f"casdy:signature:{char_id}"
                data = self.redis_client.get(key)
                if data:
                    signature = CharacterSignature.from_dict(json.loads(data))
                    self.signature_cache[char_id] = signature
                    return signature
            except Exception:
                pass

        # Create new
        return self.create_signature(character)

    def build_consistent_prompt(
        self,
        character: Dict,
        base_prompt: str,
        nsfw_level: int = 0,
        include_body: bool = True
    ) -> str:
        """
        Build a prompt with consistency tokens

        Args:
            character: Character dictionary
            base_prompt: The base prompt describing the scene/pose
            nsfw_level: 0-3 NSFW level
            include_body: Whether to include body description

        Returns:
            Enhanced prompt with consistency tokens
        """
        signature = self.get_signature(character)

        parts = []

        # 1. Quality and style tokens first
        parts.append(signature.style_tokens)

        # 2. Subject definition
        parts.append("1girl, solo, single woman")

        # 3. Face tokens (always)
        parts.append(signature.face_tokens)

        # 4. Body tokens (if needed)
        if include_body:
            parts.append(signature.body_tokens)

        # 5. NSFW enhancement
        if nsfw_level >= 3:
            parts.append("nsfw, nude, naked, explicit, uncensored")
        elif nsfw_level >= 2:
            parts.append("nsfw, nude, topless, bare breasts")
        elif nsfw_level >= 1:
            parts.append("sexy, seductive, revealing")

        # 6. Base prompt (scene/pose)
        parts.append(base_prompt)

        # 7. Consistency reinforcement
        parts.append("same person, consistent appearance, recognizable face")

        return ", ".join(parts)

    def build_consistent_negative(
        self,
        character: Dict,
        nsfw_level: int = 0
    ) -> str:
        """Build negative prompt with consistency tokens"""
        signature = self.get_signature(character)

        negative_parts = [signature.negative_tokens]

        # Add NSFW-specific negatives
        if nsfw_level >= 2:
            negative_parts.append("censored, mosaic, pixelated, censor bar, clothed")
        if nsfw_level >= 3:
            negative_parts.append("underwear, bra, panties, covered")

        return ", ".join(negative_parts)

    def get_generation_seed(
        self,
        character: Dict,
        variation: int = 0
    ) -> int:
        """
        Get a seed for generation with optional variation

        Args:
            character: Character dictionary
            variation: Variation offset (0 = base, 1+ = variations)

        Returns:
            Seed value for image generation
        """
        signature = self.get_signature(character)
        return (signature.base_seed + variation * 1000) % 2147483647

    def register_successful_prompt(
        self,
        character_id: int,
        prompt: str,
        max_references: int = 5
    ):
        """Register a prompt that produced good results"""
        if character_id not in self.signature_cache:
            return

        signature = self.signature_cache[character_id]

        # Add to reference prompts
        if prompt not in signature.reference_prompts:
            signature.reference_prompts.append(prompt)
            # Keep only recent references
            signature.reference_prompts = signature.reference_prompts[-max_references:]

        # Update Redis
        if self.redis_client:
            try:
                key = f"casdy:signature:{character_id}"
                self.redis_client.set(key, json.dumps(signature.to_dict()), ex=86400 * 30)
            except Exception:
                pass

    def get_reference_style(self, character_id: int) -> Optional[str]:
        """Get a reference prompt style hint for consistency"""
        if character_id not in self.signature_cache:
            return None

        signature = self.signature_cache[character_id]
        if signature.reference_prompts:
            # Return the most recent successful prompt as style guide
            return signature.reference_prompts[-1]

        return None

    def build_image_prompt_v2(
        self,
        character: Dict,
        pose: Optional[str] = None,
        location: Optional[str] = None,
        outfit: Optional[str] = None,
        custom: Optional[str] = None,
        nsfw_level: int = 0
    ) -> Dict[str, str]:
        """
        Build complete prompt and negative prompt for image generation

        Returns:
            Dict with 'prompt' and 'negative_prompt' keys
        """
        signature = self.get_signature(character)

        # Build base scene description
        scene_parts = []

        if custom:
            scene_parts.append(custom)

        if outfit:
            scene_parts.append(outfit)
        elif nsfw_level >= 3:
            scene_parts.append("completely nude, fully naked, no clothes, bare body")
        elif nsfw_level >= 2:
            scene_parts.append("topless, nude, bare breasts exposed")
        elif nsfw_level >= 1:
            scene_parts.append("wearing sexy lingerie, revealing outfit")
        else:
            scene_parts.append("wearing attractive casual clothing")

        if pose:
            scene_parts.append(pose)
        elif nsfw_level >= 2:
            scene_parts.append("seductive pose, bedroom eyes, inviting expression")
        else:
            scene_parts.append("natural pose, looking at viewer, gentle smile")

        if location:
            scene_parts.append(f"in {location}, {location} background")
        else:
            scene_parts.append("soft lighting, clean background")

        base_prompt = ", ".join(scene_parts)

        # Build full prompt with consistency
        full_prompt = self.build_consistent_prompt(
            character=character,
            base_prompt=base_prompt,
            nsfw_level=nsfw_level,
            include_body=True
        )

        # Build negative prompt
        negative = self.build_consistent_negative(character, nsfw_level)

        return {
            "prompt": full_prompt,
            "negative_prompt": negative,
            "seed": self.get_generation_seed(character)
        }

    def clear_signature(self, character_id: int):
        """Clear cached signature for a character"""
        self.signature_cache.pop(character_id, None)

        if self.redis_client:
            try:
                self.redis_client.delete(f"casdy:signature:{character_id}")
            except Exception:
                pass


# Global instance
character_consistency = CharacterConsistencyService()
