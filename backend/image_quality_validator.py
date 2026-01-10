"""
Image Quality Validator - Evaluates photorealism based on 2025 industry standards
Based on research: GLIPS, RealBench, and AI detection criteria
"""
import sys
import io
from typing import Dict, List, Tuple
from dataclasses import dataclass
import random

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


@dataclass
class QualityScore:
    """Quality evaluation result"""
    category: str
    score: float  # 0-10
    issues: List[str]
    suggestions: List[str]


class ImageQualityValidator:
    """
    Validates image generation quality using 2025 photorealism criteria

    Based on research:
    - GLIPS (Global-Local Image Perceptual Score)
    - RealBench photorealism assessment
    - AI detection artifacts (anatomical, stylistic, physics)
    """

    def __init__(self):
        self.min_passing_score = 8.0  # Strict threshold

    def validate_prompt_diversity(self, prompt: str, previous_prompts: List[str]) -> QualityScore:
        """
        Criterion 1: Prompt Diversity (avoid "same face syndrome")

        Research: "Modern AI creates anatomically correct images, but they often
        exhibit an uncanny perfection not found in real photography"
        """
        issues = []
        suggestions = []
        score = 10.0

        # Check for generic terms
        generic_terms = ["beautiful", "gorgeous", "stunning", "attractive"]
        if any(term in prompt.lower() for term in generic_terms):
            issues.append("Generic beauty descriptors detected (beautiful/gorgeous/stunning)")
            score -= 2.0
            suggestions.append("Use specific features: 'round face', 'angular jawline', 'distinctive nose'")

        # Check for ethnic diversity specification
        ethnic_keywords = ["european", "asian", "african", "latino", "middle-eastern", "indian"]
        if not any(keyword in prompt.lower() for keyword in ethnic_keywords):
            issues.append("No ethnic/racial diversity specified")
            score -= 2.0
            suggestions.append("Add specific ethnicity: 'European woman', 'Asian features', etc.")

        # Check for age specification
        age_keywords = ["early 20s", "late 20s", "30s", "40s", "teen", "mature"]
        if not any(keyword in prompt.lower() for keyword in age_keywords):
            issues.append("No specific age range")
            score -= 1.0
            suggestions.append("Specify age: 'early 20s', 'late 30s', etc.")

        # Check similarity to previous prompts
        if previous_prompts:
            similar_count = sum(1 for prev in previous_prompts if self._prompt_similarity(prompt, prev) > 0.6)
            if similar_count > 2:
                issues.append(f"Prompt too similar to {similar_count} previous prompts")
                score -= 3.0
                suggestions.append("Vary features, context, and characteristics significantly")

        return QualityScore(
            category="Prompt Diversity",
            score=max(0, score),
            issues=issues,
            suggestions=suggestions
        )

    def validate_imperfections(self, prompt: str) -> QualityScore:
        """
        Criterion 2: Natural Imperfections (avoid "uncanny perfection")

        Research: "AI tends to 'airbrush' surfaces, making them unnaturally smooth
        where a real photo would show small bumps, variations, or wear"
        """
        issues = []
        suggestions = []
        score = 10.0

        # Check for imperfection keywords
        imperfection_keywords = [
            "asymmetrical", "crooked", "uneven", "scar", "blemish",
            "tired", "dark circles", "freckles scattered", "pores visible",
            "minor acne", "skin redness", "imperfect"
        ]

        found_imperfections = [kw for kw in imperfection_keywords if kw in prompt.lower()]

        if len(found_imperfections) == 0:
            issues.append("NO natural imperfections specified")
            score = 3.0
            suggestions.append("Add: 'slightly crooked nose', 'asymmetrical eyes', 'minor blemishes'")
        elif len(found_imperfections) < 2:
            issues.append("Only 1 imperfection type - need more")
            score = 6.0
            suggestions.append("Add 2-3 different imperfection types for realism")

        # Check for perfection keywords (bad)
        perfection_keywords = ["perfect", "flawless", "pristine", "immaculate"]
        if any(kw in prompt.lower() for kw in perfection_keywords):
            issues.append("⚠️ CRITICAL: Contains perfection keywords (perfect/flawless)")
            score -= 5.0
            suggestions.append("REMOVE all perfection keywords immediately")

        return QualityScore(
            category="Natural Imperfections",
            score=max(0, score),
            issues=issues,
            suggestions=suggestions
        )

    def validate_lighting_realism(self, prompt: str) -> QualityScore:
        """
        Criterion 3: Lighting Realism (physics-based)

        Research: "AI assembles images like a collage artist, not a photographer,
        understanding visual elements but not the geometric and physical rules"
        """
        issues = []
        suggestions = []
        score = 10.0

        # Check for specific lighting sources
        lighting_keywords = [
            "window light", "morning sun", "overcast", "golden hour",
            "sunset", "indoor lamp", "bathroom light", "car interior",
            "harsh overhead", "soft diffused", "backlit"
        ]

        found_lighting = [kw for kw in lighting_keywords if kw in prompt.lower()]

        if not found_lighting:
            issues.append("No specific lighting source specified")
            score -= 3.0
            suggestions.append("Add specific light: 'morning window light', 'harsh overhead bathroom light'")

        # Check for generic lighting (bad)
        generic_lighting = ["natural lighting", "good lighting", "soft lighting"]
        if any(kw in prompt.lower() for kw in generic_lighting):
            issues.append("Generic lighting terms detected")
            score -= 2.0
            suggestions.append("Be specific: 'window light from left', 'sunset backlight'")

        # Check for studio lighting (bad for amateur look)
        studio_keywords = ["studio", "professional lighting", "softbox", "ring light"]
        if any(kw in prompt.lower() for kw in studio_keywords):
            issues.append("⚠️ Studio lighting = professional look (not amateur)")
            score -= 4.0
            suggestions.append("Use amateur lighting: 'bathroom mirror light', 'bedroom lamp'")

        return QualityScore(
            category="Lighting Realism",
            score=max(0, score),
            issues=issues,
            suggestions=suggestions
        )

    def validate_context_detail(self, prompt: str) -> QualityScore:
        """
        Criterion 4: Context Detail (realistic environment)

        Research: "Background that seems patched together from different scenes"
        indicates AI generation
        """
        issues = []
        suggestions = []
        score = 10.0

        # Check for detailed context
        context_details = [
            "unmade bed", "clothes on floor", "messy", "cluttered",
            "toothpaste stains", "worn", "wrinkled sheets", "dirty mirror",
            "steering wheel", "dashboard", "park bench", "old furniture"
        ]

        found_details = [kw for kw in context_details if kw in prompt.lower()]

        if not found_details:
            issues.append("No environmental details specified")
            score -= 3.0
            suggestions.append("Add details: 'unmade bed', 'messy room', 'worn furniture'")

        # Check for generic context (bad)
        generic_context = ["bedroom", "beach", "luxury", "elegant", "beautiful setting"]
        generic_count = sum(1 for kw in generic_context if kw in prompt.lower())

        if generic_count > len(found_details):
            issues.append("Context too generic/perfect")
            score -= 2.0
            suggestions.append("Make context messier and more specific")

        return QualityScore(
            category="Context Detail",
            score=max(0, score),
            issues=issues,
            suggestions=suggestions
        )

    def validate_negative_prompts(self, negative: str) -> QualityScore:
        """
        Criterion 5: Negative Prompts Strength (block AI artifacts)
        """
        issues = []
        suggestions = []
        score = 10.0

        # Required negative keywords
        required_negatives = [
            "perfect", "flawless", "airbrushed", "instagram filter",
            "professional model", "magazine", "same face", "clone face",
            "beauty filter", "facetune", "retouching"
        ]

        missing_negatives = [kw for kw in required_negatives if kw not in negative.lower()]

        if len(missing_negatives) > 5:
            issues.append(f"Missing {len(missing_negatives)} critical negative keywords")
            score -= 4.0
            suggestions.append(f"Add to negatives: {', '.join(missing_negatives[:5])}")
        elif len(missing_negatives) > 0:
            issues.append(f"Missing {len(missing_negatives)} negative keywords")
            score -= 2.0

        return QualityScore(
            category="Negative Prompts",
            score=max(0, score),
            issues=issues,
            suggestions=suggestions
        )

    def validate_complete_prompt(
        self,
        prompt: str,
        negative: str,
        previous_prompts: List[str] = None
    ) -> Dict:
        """
        Complete validation of a prompt against all criteria

        Returns:
            dict with overall score and detailed breakdown
        """
        previous_prompts = previous_prompts or []

        scores = [
            self.validate_prompt_diversity(prompt, previous_prompts),
            self.validate_imperfections(prompt),
            self.validate_lighting_realism(prompt),
            self.validate_context_detail(prompt),
            self.validate_negative_prompts(negative)
        ]

        # Calculate weighted average
        total_score = sum(s.score for s in scores) / len(scores)

        # Determine pass/fail
        passed = total_score >= self.min_passing_score

        return {
            "overall_score": round(total_score, 2),
            "passed": passed,
            "threshold": self.min_passing_score,
            "detailed_scores": scores,
            "all_issues": [issue for s in scores for issue in s.issues],
            "all_suggestions": [sug for s in scores for sug in s.suggestions],
            "summary": self._generate_summary(total_score, passed, scores)
        }

    def _generate_summary(self, score: float, passed: bool, scores: List[QualityScore]) -> str:
        """Generate human-readable summary"""
        if passed:
            return f"✅ PASSED ({score}/10) - Prompt meets quality standards"
        else:
            failing_categories = [s.category for s in scores if s.score < self.min_passing_score]
            return f"❌ FAILED ({score}/10) - Issues in: {', '.join(failing_categories)}"

    def _prompt_similarity(self, prompt1: str, prompt2: str) -> float:
        """Calculate similarity between two prompts (simple word overlap)"""
        words1 = set(prompt1.lower().split())
        words2 = set(prompt2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0


# ============================================================================
# PROMPT GENERATOR WITH DIVERSITY ENFORCEMENT
# ============================================================================

class DiversePromptGenerator:
    """
    Generates diverse prompts that pass quality validation
    Forces variation to avoid "same face syndrome"
    """

    def __init__(self):
        self.validator = ImageQualityValidator()

        # Diversity pools
        self.ethnicities = [
            "European", "East Asian", "South Asian", "African",
            "Latino", "Middle-Eastern", "Mixed race", "Southeast Asian"
        ]

        self.ages = [
            "early 20s", "mid 20s", "late 20s",
            "early 30s", "mid 30s", "late 30s"
        ]

        self.face_shapes = [
            "round face with soft features",
            "angular face with defined cheekbones",
            "heart-shaped face with pointed chin",
            "oval face with balanced proportions",
            "square face with strong jawline"
        ]

        self.distinctive_features = [
            "slightly crooked nose with small bump",
            "asymmetrical eyes, left eye slightly larger",
            "fuller lower lip, thin upper lip",
            "prominent freckles across nose and cheeks",
            "defined eyebrows with natural arch",
            "small scar above right eyebrow",
            "dimples when smiling",
            "high cheekbones with hollow cheeks"
        ]

        self.skin_imperfections = [
            "visible pores especially on nose and forehead",
            "minor acne scars on cheeks",
            "slight redness around nose",
            "dark circles under eyes from tiredness",
            "uneven skin tone with some sun damage",
            "freckles scattered unevenly across face",
            "minor blemish on chin",
            "natural skin texture not airbrushed"
        ]

        self.hair_descriptions = [
            "messy shoulder-length hair with flyaways",
            "short bob cut slightly uneven",
            "long wavy hair with visible split ends",
            "curly hair not perfectly styled",
            "straight hair with natural grease at roots",
            "ponytail with loose strands falling out",
            "bed hair not combed",
            "wind-blown hair tangled"
        ]

        self.contexts = [
            "messy bedroom with unmade bed and clothes on floor, morning window light",
            "bathroom mirror selfie with toothpaste stains visible, harsh overhead light",
            "car interior with steering wheel visible, dashboard in background, afternoon sun",
            "kitchen with dirty dishes in background, fluorescent ceiling light",
            "living room couch with rumpled blanket, table lamp light from side",
            "outdoor park bench with trees behind, overcast natural light",
            "bedroom at night with bedside lamp, warm yellow light",
            "bathroom with shower curtain behind, phone reflection in mirror"
        ]

        self.poses = [
            "lying in bed looking up at phone camera",
            "sitting on edge of bed leaning forward",
            "standing in front of mirror, phone visible",
            "reclining against headboard",
            "kneeling on bed",
            "sitting cross-legged",
            "lying on side propped on elbow",
            "casual slouched posture"
        ]

    def generate_diverse_prompt(
        self,
        nsfw_level: int = 0,
        previous_prompts: List[str] = None
    ) -> Tuple[str, str]:
        """
        Generate a diverse prompt that passes validation

        Args:
            nsfw_level: 0=SFW, 1=Sensual, 2=Topless, 3=Nude
            previous_prompts: List of previously used prompts

        Returns:
            (positive_prompt, negative_prompt)
        """
        previous_prompts = previous_prompts or []

        # Build diverse prompt
        ethnicity = random.choice(self.ethnicities)
        age = random.choice(self.ages)
        face_shape = random.choice(self.face_shapes)
        features = random.sample(self.distinctive_features, 2)
        imperfections = random.sample(self.skin_imperfections, 2)
        hair = random.choice(self.hair_descriptions)
        context = random.choice(self.contexts)
        pose = random.choice(self.poses)

        # NSFW clothing
        if nsfw_level == 0:
            clothing = "wearing casual t-shirt"
        elif nsfw_level == 1:
            clothing = "wearing black lace lingerie"
        elif nsfw_level == 2:
            clothing = "topless from waist up, bare breasts visible, nipples visible"
        else:  # level 3
            clothing = "completely naked, full frontal nudity, nude body visible"

        # Assemble prompt
        positive_prompt = (
            f"{ethnicity} woman in {age}, {face_shape}, "
            f"{features[0]}, {features[1]}, "
            f"{imperfections[0]}, {imperfections[1]}, "
            f"{hair}, "
            f"{clothing}, "
            f"{pose}, "
            f"{context}"
        )

        # Ultra-strong negative prompt
        negative_prompt = (
            "perfect symmetrical face, flawless skin, airbrushed, photoshopped, "
            "professional retouching, Instagram filter, beauty filter, FaceTune, "
            "professional model, magazine cover, fashion photoshoot, "
            "professional makeup, salon hairstyle, perfect features, "
            "same face syndrome, clone face, repetitive features, "
            "unrealistic perfection, too beautiful, idealized beauty, "
            "studio lighting, professional photographer, "
            "cartoon, anime, 3d render, digital art, "
            "low quality, blurry, deformed, distorted"
        )

        return positive_prompt, negative_prompt

    def generate_validated_batch(
        self,
        count: int,
        nsfw_level: int = 0
    ) -> List[Tuple[str, str, Dict]]:
        """
        Generate a batch of prompts that all pass validation

        Returns:
            List of (positive_prompt, negative_prompt, validation_result)
        """
        validated_prompts = []
        previous_prompts = []

        attempts = 0
        max_attempts = count * 5  # Allow retries

        while len(validated_prompts) < count and attempts < max_attempts:
            attempts += 1

            positive, negative = self.generate_diverse_prompt(nsfw_level, previous_prompts)

            # Validate
            validation = self.validator.validate_complete_prompt(
                positive, negative, previous_prompts
            )

            if validation["passed"]:
                validated_prompts.append((positive, negative, validation))
                previous_prompts.append(positive)
                print(f"✅ Generated prompt {len(validated_prompts)}/{count} (score: {validation['overall_score']})")
            else:
                print(f"❌ Rejected prompt (score: {validation['overall_score']}) - {validation['summary']}")

        if len(validated_prompts) < count:
            print(f"⚠️ Only generated {len(validated_prompts)}/{count} validated prompts")

        return validated_prompts


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("🔍 IMAGE QUALITY VALIDATOR - Testing")
    print("=" * 70)

    validator = ImageQualityValidator()

    # Test 1: Bad prompt (generic)
    print("\n" + "=" * 70)
    print("Test 1: Generic Prompt (Should FAIL)")
    print("=" * 70)
    bad_prompt = "beautiful woman with long hair in bedroom"
    bad_negative = "cartoon, anime"

    result = validator.validate_complete_prompt(bad_prompt, bad_negative)
    print(f"\nPrompt: {bad_prompt}")
    print(f"\n{result['summary']}")
    print(f"\nDetailed Scores:")
    for score in result['detailed_scores']:
        print(f"  {score.category}: {score.score}/10")
        if score.issues:
            for issue in score.issues:
                print(f"    - {issue}")

    print(f"\n💡 Suggestions:")
    for sug in result['all_suggestions'][:5]:
        print(f"  - {sug}")

    # Test 2: Good prompt (diverse with imperfections)
    print("\n" + "=" * 70)
    print("Test 2: Diverse Prompt (Should PASS)")
    print("=" * 70)

    generator = DiversePromptGenerator()
    good_prompt, good_negative = generator.generate_diverse_prompt(nsfw_level=1)

    result = validator.validate_complete_prompt(good_prompt, good_negative)
    print(f"\nPrompt: {good_prompt[:150]}...")
    print(f"\n{result['summary']}")
    print(f"\nDetailed Scores:")
    for score in result['detailed_scores']:
        print(f"  {score.category}: {score.score}/10")

    # Test 3: Generate batch
    print("\n" + "=" * 70)
    print("Test 3: Generate 5 Validated Prompts")
    print("=" * 70)

    batch = generator.generate_validated_batch(count=5, nsfw_level=2)

    print(f"\n✅ Generated {len(batch)} validated prompts")
    print("\nSample prompts:")
    for i, (pos, neg, val) in enumerate(batch[:3], 1):
        print(f"\n{i}. Score: {val['overall_score']}/10")
        print(f"   {pos[:100]}...")
