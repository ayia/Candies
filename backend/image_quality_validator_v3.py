"""
Image Quality Validator V3 - Candy.ai Standard + FLUX Techniques
Incorporates deep research findings from 30+ sources
Target: 9.5/10 photorealism matching Candy.ai industry leader
"""
import sys
from typing import Dict, List, Tuple
from dataclasses import dataclass
import random

# Import V2 components
from image_quality_validator import QualityScore, ImageQualityValidator


class CandyAIStandardValidator(ImageQualityValidator):
    """
    V3: Enhanced validator incorporating Candy.ai standards + FLUX techniques

    Based on research:
    - Candy.ai: "Hyper-realistic and almost indistinguishable from real photographs"
    - FLUX Raw: Natural imperfections, organic lighting, authentic skin textures
    - Realistic Vision: Exceptional facial features and eyes
    - Industry standard: 4.5/5 minimum for "Best AI Girlfriend with Pictures"
    """

    def __init__(self):
        super().__init__()
        self.min_passing_score = 9.0  # Candy.ai standard (raised from 8.0)

    def validate_anatomy_hands(self, prompt: str) -> QualityScore:
        """
        NEW V3: Validate hand anatomy (27 bones - most difficult!)

        Research: "Hands remain particularly challenging due to their 27 distinct
        bones, with errors often manifesting as merged fingers or disproportionate
        segment lengths"
        """
        issues = []
        suggestions = []
        score = 10.0

        # Check if hands are mentioned in prompt
        hand_keywords = ["hand", "finger", "palm", "fist", "gesture"]
        has_hands = any(kw in prompt.lower() for kw in hand_keywords)

        if has_hands:
            # Hands are explicitly mentioned - validate description
            good_hand_prompts = [
                "five natural-looking fingers",
                "relaxed hand posture",
                "gently curled fingers",
                "not overlapping",
                "clearly visible hands"
            ]

            found_good = sum(1 for kw in good_hand_prompts if kw in prompt.lower())

            if found_good == 0:
                issues.append("Hands mentioned but not properly described")
                score = 5.0
                suggestions.append("Add: 'hands clearly visible with five natural-looking fingers, relaxed posture'")
            elif found_good < 2:
                issues.append("Hand description incomplete")
                score = 7.0
                suggestions.append("Add more hand details: 'fingers gently curled, not overlapping'")

        return QualityScore(
            category="Anatomy - Hands",
            score=max(0, score),
            issues=issues,
            suggestions=suggestions
        )

    def validate_face_symmetry(self, prompt: str) -> QualityScore:
        """
        NEW V3: Validate facial symmetry specifications

        Research: "Provide guidelines for symmetry and anatomical balance,
        highlighting specifics such as 'aligned eyes, balanced facial symmetry,
        and proportionate jawlines'"
        """
        issues = []
        suggestions = []
        score = 10.0

        # Check for facial feature specifications
        face_features = [
            "aligned eyes", "balanced facial", "proportionate jawline",
            "natural asymmetry", "facial proportions", "eye level"
        ]

        found_features = [f for f in face_features if f in prompt.lower()]

        if len(found_features) == 0:
            issues.append("No facial symmetry/proportion specifications")
            score = 6.0
            suggestions.append("Add: 'aligned eyes, balanced facial symmetry, proportionate jawlines'")
        elif len(found_features) < 2:
            issues.append("Minimal facial feature specifications")
            score = 8.0
            suggestions.append("Add more facial details for better anatomy")

        return QualityScore(
            category="Anatomy - Face Symmetry",
            score=max(0, score),
            issues=issues,
            suggestions=suggestions
        )

    def validate_lighting_specificity(self, prompt: str) -> QualityScore:
        """
        ENHANCED V3: More rigorous lighting validation (FLUX Raw standard)

        Research: "Specify whether you want soft, diffused light or hard, direct light
        - phrases like 'soft natural lighting' or 'studio spotlight with defined shadows'"
        """
        issues = []
        suggestions = []
        score = 10.0

        # V3: Specific lighting sources (not generic)
        specific_sources = [
            "window light", "golden hour", "sunset", "morning sun",
            "overhead lamp", "bedside lamp", "bathroom light",
            "car interior", "fluorescent", "backlit",
            "harsh overhead", "soft diffused", "warm yellow light"
        ]

        # V3: Lighting quality descriptors
        quality_descriptors = [
            "soft", "hard", "diffused", "direct", "warm", "cool",
            "harsh", "gentle", "dramatic", "subtle"
        ]

        # V3: Lighting direction
        direction_keywords = [
            "from left", "from right", "from above", "from behind",
            "side light", "backlight", "front light"
        ]

        found_sources = [s for s in specific_sources if s in prompt.lower()]
        found_quality = [q for q in quality_descriptors if q in prompt.lower()]
        found_direction = [d for d in direction_keywords if d in prompt.lower()]

        if not found_sources:
            issues.append("No specific light source (window, lamp, sun, etc.)")
            score -= 4.0
            suggestions.append("Add specific source: 'warm golden hour light', 'bedside lamp'")

        if not found_quality:
            issues.append("No lighting quality descriptor (soft/hard/diffused)")
            score -= 3.0
            suggestions.append("Add quality: 'soft diffused', 'harsh direct'")

        if not found_direction:
            issues.append("No lighting direction specified")
            score -= 2.0
            suggestions.append("Add direction: 'from left side', 'backlit'")

        # Check for bad generic terms
        generic_bad = ["natural lighting", "good lighting", "nice light"]
        if any(bad in prompt.lower() for bad in generic_bad):
            issues.append("⚠️ Generic lighting terms detected (too vague)")
            score -= 3.0
            suggestions.append("Replace with specific: 'morning window light from left'")

        return QualityScore(
            category="Lighting Specificity (FLUX)",
            score=max(0, score),
            issues=issues,
            suggestions=suggestions
        )

    def validate_camera_specs(self, prompt: str) -> QualityScore:
        """
        NEW V3: Camera specifications for photorealism

        Research: "Add camera details like 'shot on DSLR, f/1.8 aperture' to
        enhance realism of shadows and highlights"
        """
        issues = []
        suggestions = []
        score = 10.0

        # Camera/device keywords
        camera_keywords = [
            "shot on", "iPhone", "DSLR", "camera", "f/", "aperture",
            "Canon", "Nikon", "Sony", "lens"
        ]

        found_camera = [kw for kw in camera_keywords if kw in prompt]

        if len(found_camera) == 0:
            issues.append("No camera/device specification")
            score = 7.0
            suggestions.append("Add: 'shot on iPhone' or 'shot on DSLR f/1.8'")
        elif len(found_camera) == 1:
            issues.append("Minimal camera specs")
            score = 8.5
            suggestions.append("Add aperture: 'f/1.8 aperture' for realistic depth")

        return QualityScore(
            category="Camera Specifications",
            score=max(0, score),
            issues=issues,
            suggestions=suggestions
        )

    def validate_texture_detail(self, prompt: str) -> QualityScore:
        """
        NEW V3: Texture and surface detail validation (FLUX Raw approach)

        Research: "Raw Mode retains textures and imperfections, such as the
        natural unevenness of skin or the subtle grain of fabric"
        """
        issues = []
        suggestions = []
        score = 10.0

        # Skin texture keywords
        skin_texture = [
            "visible pores", "skin texture", "pores on", "skin imperfections",
            "natural skin", "uneven skin", "skin grain"
        ]

        # Hair detail keywords
        hair_detail = [
            "individual hair strands", "hair strands visible", "flyaway",
            "messy hair", "stray hairs", "hair texture"
        ]

        # Fabric/surface keywords
        surface_detail = [
            "fabric texture", "wrinkles", "grain", "surface texture",
            "material texture", "visible weave"
        ]

        found_skin = [kw for kw in skin_texture if kw in prompt.lower()]
        found_hair = [kw for kw in hair_detail if kw in prompt.lower()]
        found_surface = [kw for kw in surface_detail if kw in prompt.lower()]

        total_texture = len(found_skin) + len(found_hair) + len(found_surface)

        if total_texture == 0:
            issues.append("NO texture/detail specifications (critical for FLUX Raw)")
            score = 4.0
            suggestions.append("Add: 'visible skin pores, individual hair strands, fabric texture'")
        elif total_texture < 2:
            issues.append("Minimal texture details")
            score = 7.0
            suggestions.append("Add more texture: skin pores + hair strands + surface grain")

        return QualityScore(
            category="Texture & Surface Detail (FLUX Raw)",
            score=max(0, score),
            issues=issues,
            suggestions=suggestions
        )

    def validate_prompt_complete_candy_standard(
        self,
        prompt: str,
        negative: str,
        previous_prompts: List[str] = None
    ) -> Dict:
        """
        V3: Complete validation against Candy.ai standard (9.5/10 target)

        Includes ALL validators:
        - V2: Diversity, Imperfections, Lighting, Context, Negatives
        - V3: Hands, Face Symmetry, Lighting Specificity, Camera, Texture
        """
        previous_prompts = previous_prompts or []

        # V2 validators
        v2_scores = [
            self.validate_prompt_diversity(prompt, previous_prompts),
            self.validate_imperfections(prompt),
            self.validate_context_detail(prompt),
            self.validate_negative_prompts(negative)
        ]

        # V3 NEW validators
        v3_scores = [
            self.validate_anatomy_hands(prompt),
            self.validate_face_symmetry(prompt),
            self.validate_lighting_specificity(prompt),
            self.validate_camera_specs(prompt),
            self.validate_texture_detail(prompt)
        ]

        all_scores = v2_scores + v3_scores

        # Weighted average (V3 criteria have higher weight)
        v2_weight = 0.4
        v3_weight = 0.6

        v2_avg = sum(s.score for s in v2_scores) / len(v2_scores)
        v3_avg = sum(s.score for s in v3_scores) / len(v3_scores)

        total_score = (v2_avg * v2_weight) + (v3_avg * v3_weight)

        # Candy.ai standard: 9.0+ required
        passed = total_score >= self.min_passing_score

        return {
            "overall_score": round(total_score, 2),
            "v2_score": round(v2_avg, 2),
            "v3_score": round(v3_avg, 2),
            "passed": passed,
            "threshold": self.min_passing_score,
            "candy_ai_standard": "9.5/10 target",
            "detailed_scores": all_scores,
            "all_issues": [issue for s in all_scores for issue in s.issues],
            "all_suggestions": [sug for s in all_scores for sug in s.suggestions],
            "summary": self._generate_candy_summary(total_score, passed, all_scores)
        }

    def _generate_candy_summary(self, score: float, passed: bool, scores: List[QualityScore]) -> str:
        """Generate Candy.ai-standard summary"""
        if score >= 9.5:
            return f"🌟 CANDY.AI STANDARD EXCEEDED ({score}/10) - Industry leader quality!"
        elif passed:
            return f"✅ CANDY.AI STANDARD MET ({score}/10) - Excellent quality"
        else:
            failing = [s.category for s in scores if s.score < self.min_passing_score]
            return f"❌ BELOW CANDY.AI STANDARD ({score}/10) - Issues: {', '.join(failing[:3])}"


class FluxRawPromptGenerator:
    """
    V3: Enhanced prompt generator using FLUX Raw + Candy.ai techniques

    Research findings applied:
    - FLUX Raw: Natural imperfections, organic lighting, authentic textures
    - Candy.ai: Hyper-realistic, indistinguishable from real photos
    - Industry standard: Consistent visual quality, proper anatomy
    """

    def __init__(self):
        self.validator = CandyAIStandardValidator()

        # V2 pools (keep diversity)
        self.ethnicities = [
            "European", "East Asian", "South Asian", "African",
            "Latino", "Middle-Eastern", "Mixed race", "Southeast Asian"
        ]

        self.ages = [
            "early 20s", "mid 20s", "late 20s",
            "early 30s", "mid 30s", "late 30s"
        ]

        # V3: ENHANCED face shapes (Candy.ai standard)
        self.face_shapes = [
            "round face with soft features and full cheeks",
            "angular face with defined cheekbones and strong jawline",
            "heart-shaped face with pointed chin and wide forehead",
            "oval face with balanced proportions and gentle curves",
            "square face with strong jaw and broad features",
            "diamond face with high cheekbones and narrow forehead"
        ]

        # V3: ENHANCED distinctive features (with symmetry notes)
        self.distinctive_features = [
            "slightly crooked nose with small bump, adds character",
            "asymmetrical eyes with left eye slightly larger, natural imperfection",
            "fuller lower lip and thin upper lip, unique mouth shape",
            "prominent freckles scattered across nose and cheeks naturally",
            "defined eyebrows with natural arch, not perfectly symmetrical",
            "small scar above right eyebrow from childhood, barely visible",
            "dimples when smiling on one side more than other",
            "high cheekbones with hollow cheeks, striking bone structure",
            "slightly uneven eyebrows, left higher than right",
            "beauty mark on left cheek near mouth"
        ]

        # V3: ENHANCED skin imperfections (FLUX Raw approach)
        self.skin_imperfections = [
            "visible pores especially on nose and forehead, natural skin texture",
            "minor acne scars on cheeks from teenage years, faded but visible",
            "slight redness around nose and cheeks, natural coloring",
            "dark circles under eyes from tiredness, authentic tired look",
            "uneven skin tone with some sun damage on cheeks, realistic aging",
            "freckles scattered unevenly across face and shoulders, sun-kissed",
            "minor blemish on chin, small imperfection",
            "natural skin texture not airbrushed, pores and fine lines visible",
            "slight hyperpigmentation on forehead, natural skin variation",
            "small mole on neck, distinctive mark"
        ]

        # V3: ENHANCED hair (texture details)
        self.hair_descriptions = [
            "messy shoulder-length hair with flyaway strands and split ends visible",
            "short bob cut slightly uneven, natural home-cut look",
            "long wavy hair with visible split ends and natural frizz",
            "curly hair not perfectly styled, individual curls visible",
            "straight hair with natural grease at roots, unwashed look",
            "ponytail with loose strands falling out and messy texture",
            "bed hair not combed, tangled and natural morning look",
            "wind-blown hair tangled with individual strands visible"
        ]

        # V3: ENHANCED contexts (FLUX Raw lighting + camera specs)
        self.contexts = [
            "messy bedroom with unmade bed and clothes on floor, warm bedside lamp light from right, shot on iPhone",
            "bathroom mirror selfie with toothpaste stains on mirror, harsh overhead fluorescent light, phone visible in reflection",
            "car interior with steering wheel and dashboard visible, afternoon sun through windshield, candid moment",
            "kitchen with dirty dishes stacked in sink background, overhead fluorescent ceiling light, casual home photo",
            "living room couch with rumpled blanket, warm table lamp light from side, relaxed evening",
            "outdoor park bench with trees and grass behind, overcast natural diffused light, cloudy day",
            "bedroom at night with yellow bedside lamp visible, warm intimate lighting from single source",
            "bathroom with shower curtain behind, phone reflection in foggy mirror, bathroom light overhead"
        ]

        # V3: ENHANCED poses (natural, not model-like)
        self.poses = [
            "lying in bed looking up at phone camera, relaxed casual pose",
            "sitting on edge of bed leaning forward toward camera, intimate moment",
            "standing in front of mirror with phone visible, taking selfie",
            "reclining against headboard with one knee up, comfortable position",
            "kneeling on bed leaning on hands, playful casual pose",
            "sitting cross-legged looking at camera, natural relaxed posture",
            "lying on side propped on elbow, casual resting pose",
            "casual slouched posture sitting, authentic tired look"
        ]

        # V3: NEW - Hand descriptions (when needed)
        self.hand_descriptions = [
            "hands clearly visible with five natural-looking fingers, relaxed posture, gently curled",
            "one hand holding phone, fingers naturally positioned around device",
            "hands resting on lap, relaxed natural pose with fingers gently touching",
            "hand running through hair, natural gesture with five fingers visible"
        ]

    def generate_flux_raw_prompt(
        self,
        nsfw_level: int = 0,
        previous_prompts: List[str] = None,
        include_hands: bool = False
    ) -> Tuple[str, str]:
        """
        Generate FLUX Raw style prompt meeting Candy.ai 9.5/10 standard

        Returns:
            (positive_prompt, negative_prompt)
        """
        previous_prompts = previous_prompts or []

        # Build comprehensive prompt
        ethnicity = random.choice(self.ethnicities)
        age = random.choice(self.ages)
        face_shape = random.choice(self.face_shapes)
        features = random.sample(self.distinctive_features, 2)
        imperfections = random.sample(self.skin_imperfections, 3)  # V3: 3 instead of 2
        hair = random.choice(self.hair_descriptions)
        context = random.choice(self.contexts)
        pose = random.choice(self.poses)

        # NSFW clothing
        if nsfw_level == 0:
            clothing = "wearing casual t-shirt and jeans"
        elif nsfw_level == 1:
            clothing = "wearing black lace lingerie, sensual"
        elif nsfw_level == 2:
            clothing = "topless from waist up, bare breasts clearly visible, nipples visible, natural chest"
        else:  # level 3
            clothing = "completely naked, full frontal nudity, nude body fully visible, bare breasts and intimate areas shown"

        # V3: Optional hand description
        hand_desc = ""
        if include_hands:
            hand_desc = ", " + random.choice(self.hand_descriptions)

        # V3: FLUX Raw quality tags (enhanced from V2)
        flux_raw_tags = (
            "raw candid photo shot on iPhone, amateur photography, "
            "natural unedited with visible skin pores and texture, "
            "individual hair strands visible with flyaway hairs, "
            "natural imperfect skin NOT airbrushed or retouched, "
            "genuine authentic real person NOT professional model, "
            "photorealistic, hyper-realistic, looks indistinguishable from real photograph"
        )

        # Assemble complete prompt
        positive_prompt = (
            f"{ethnicity} woman in {age}, {face_shape}, "
            f"{features[0]}, {features[1]}, "
            f"{imperfections[0]}, {imperfections[1]}, {imperfections[2]}, "
            f"{hair}, "
            f"{clothing}, "
            f"{pose}{hand_desc}, "
            f"{context}, "
            f"{flux_raw_tags}"
        )

        # V3: ULTRA-STRONG negative prompts (Candy.ai + FLUX + Industry standard)
        negative_prompt = (
            # Candy.ai standard
            "professional model, magazine cover, fashion photoshoot, studio portrait, "
            "professional makeup artist, salon hairstyle, glamour shot, "

            # FLUX Raw blocking
            "perfect symmetrical face, flawless skin, airbrushed skin, photoshopped, "
            "Instagram filter, beauty filter, FaceTune app, professional retouching, "
            "oversaturated colors, oversmooth skin, plastic skin texture, "

            # Same face syndrome
            "same face syndrome, clone face, repetitive features, generic beauty, "
            "unrealistic perfection, too beautiful, idealized beauty, "

            # Anatomical issues (V3 focus)
            "deformed eyes, extra fingers, merged fingers, six fingers, four fingers, "
            "disproportionate hands, wrong hand anatomy, odd limbs, "
            "malformed face, distorted features, asymmetrical eyes wrong, "

            # Technical quality
            "studio lighting, professional photographer, ring light, softbox, "
            "cartoon, anime, 3d render, digital art, painting, illustration, "
            "low quality, blurry, pixelated, jpeg artifacts, compression, "
            "watermark, signature, text, logo, username"
        )

        return positive_prompt, negative_prompt


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("🌟 IMAGE QUALITY VALIDATOR V3 - Candy.ai Standard")
    print("=" * 70)

    validator = CandyAIStandardValidator()
    generator = FluxRawPromptGenerator()

    # Test 1: Generate and validate FLUX Raw prompt
    print("\n" + "=" * 70)
    print("Test 1: FLUX Raw Prompt Generation + Validation")
    print("=" * 70)

    prompt, negative = generator.generate_flux_raw_prompt(
        nsfw_level=2,
        include_hands=True
    )

    print(f"\nGenerated Prompt (first 150 chars):")
    print(f"{prompt[:150]}...")

    result = validator.validate_prompt_complete_candy_standard(prompt, negative)

    print(f"\n{result['summary']}")
    print(f"\nScores:")
    print(f"  Overall: {result['overall_score']}/10")
    print(f"  V2 Score: {result['v2_score']}/10")
    print(f"  V3 Score: {result['v3_score']}/10")
    print(f"  Target: {result['candy_ai_standard']}")
    print(f"  Passed: {'✅ YES' if result['passed'] else '❌ NO'}")

    if result['detailed_scores']:
        print(f"\nDetailed Breakdown:")
        for score in result['detailed_scores']:
            status = "✅" if score.score >= 9.0 else "⚠️" if score.score >= 7.0 else "❌"
            print(f"  {status} {score.category}: {score.score}/10")
            if score.issues:
                for issue in score.issues[:2]:
                    print(f"      - {issue}")

    # Test 2: Generate 5 prompts and show diversity
    print("\n" + "=" * 70)
    print("Test 2: Generate 5 Diverse FLUX Raw Prompts")
    print("=" * 70)

    previous = []
    for i in range(5):
        prompt, neg = generator.generate_flux_raw_prompt(
            nsfw_level=random.choice([0, 1, 2, 3]),
            previous_prompts=previous
        )

        validation = validator.validate_prompt_complete_candy_standard(prompt, neg, previous)

        previous.append(prompt)

        print(f"\n{i+1}. Score: {validation['overall_score']}/10")
        print(f"   {prompt[:100]}...")
        print(f"   Status: {validation['summary']}")

    print(f"\n{'='*70}")
    print(f"✅ V3 Validator Ready - Candy.ai 9.5/10 Standard Implemented")
    print(f"{'='*70}")
