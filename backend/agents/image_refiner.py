"""
AGENT: IMAGE PROMPT REFINER
Purpose: Optimize prompts for high-quality NSFW image generation
Based on: https://arxiv.org/abs/2407.00247 (Prompt Refinement with Image Pivot)

This agent takes basic image requests and transforms them into
optimized Stable Diffusion / FLUX prompts with proper structure.
"""
from typing import Dict, Any, Optional, List
from .base import BaseAgent


# Stable Diffusion prompt templates for different NSFW levels
PROMPT_TEMPLATES = {
    "sfw": {
        "prefix": "RAW photo, masterpiece, best quality, ultra realistic, photorealistic, professional photography",
        "suffix": "natural skin texture, 8k uhd, dslr quality, sharp focus, high detail, cinematic lighting",
        "negative": "ugly, deformed, noisy, blurry, low quality, bad anatomy, bad proportions, extra limbs, mutated, watermark, text, cartoon, anime, illustration"
    },
    "suggestive": {
        "prefix": "RAW photo, masterpiece, best quality, ultra realistic, photorealistic, professional boudoir photography, sensual",
        "suffix": "natural skin texture, 8k uhd, dslr quality, soft lighting, seductive atmosphere, cinematic",
        "negative": "ugly, deformed, blurry, low quality, bad anatomy, cartoon, anime, illustration, watermark"
    },
    "explicit": {
        "prefix": "RAW photo, masterpiece, best quality, ultra realistic, photorealistic, professional nude photography, artistic nude",
        "suffix": "detailed skin texture, 8k uhd, high detail, natural lighting, anatomically correct, realistic body",
        "negative": "ugly, deformed, blurry, bad anatomy, bad proportions, cartoon, anime, illustration, watermark, censored"
    },
    "hardcore": {
        "prefix": "RAW photo, masterpiece, best quality, ultra realistic, photorealistic, explicit adult content, uncensored",
        "suffix": "detailed realistic skin, 8k uhd, high detail, anatomically correct, explicit, nsfw",
        "negative": "ugly, deformed, blurry, bad anatomy, cartoon, anime, censored, watermark"
    }
}

# Body type to prompt mappings (more explicit for NSFW)
BODY_PROMPTS = {
    "curvy": "curvy voluptuous body, wide hips, thick thighs, hourglass figure, full figure",
    "slim": "slim slender body, thin waist, lean figure",
    "athletic": "athletic toned body, fit physique, toned abs, muscular legs",
    "petite": "petite small frame, delicate body, small waist",
    "busty": "busty figure, large natural breasts, big bust, ample cleavage",
    "thick": "thick body, wide hips, big thighs, curvy figure, thicc"
}

BREAST_PROMPTS = {
    "small": "small perky breasts, A cup, small chest",
    "medium": "medium breasts, B cup, natural breasts",
    "large": "large breasts, D cup, big natural breasts, ample bust",
    "very large": "huge breasts, massive bust, F cup, enormous breasts, very large chest",
    "huge": "gigantic breasts, massive tits, extremely large bust"
}

BUTT_PROMPTS = {
    "small": "small tight butt, petite rear",
    "medium": "round butt, shapely rear",
    "round": "round plump butt, bubble butt, shapely ass",
    "large": "big round ass, large posterior, wide hips, thick butt, juicy ass",
    "huge": "massive ass, enormous butt, very large rear"
}

POSE_PROMPTS = {
    "standing": "standing pose, full body visible",
    "sitting": "sitting pose, seated position",
    "lying": "lying down, on back, reclined",
    "lying_front": "lying on stomach, prone position",
    "kneeling": "kneeling position, on knees",
    "bending": "bending over, leaning forward",
    "from_behind": "view from behind, back view, rear view",
    "selfie": "selfie angle, holding phone, POV selfie",
    "mirror": "mirror selfie, reflection"
}

OUTFIT_PROMPTS = {
    "lingerie": "wearing sexy lingerie, lace bra and panties, sheer fabric",
    "bikini": "wearing bikini, swimsuit, beach wear",
    "underwear": "wearing underwear, bra and panties",
    "nude": "nude, naked, no clothes, fully nude, bare skin",
    "topless": "topless, bare breasts, exposed chest, no top",
    "see_through": "wearing see-through clothing, sheer fabric, transparent",
    "dress": "wearing tight dress, form-fitting dress",
    "shorts": "wearing short shorts, hot pants, revealing shorts"
}

SETTING_PROMPTS = {
    "bedroom": "in bedroom, on bed, bedroom background, intimate setting",
    "bathroom": "in bathroom, shower, wet skin, steam",
    "shower": "in shower, wet body, water droplets on skin, steamy",
    "pool": "by the pool, poolside, wet swimsuit",
    "beach": "on beach, sandy beach background, ocean view",
    "outdoor": "outdoor setting, natural lighting",
    "studio": "studio photography, professional lighting, clean background"
}


class ImageRefinerAgent(BaseAgent):
    """
    Image Prompt Refiner Agent that:
    1. Takes character details and user request
    2. Uses LLM to understand the request and generate appropriate prompts
    3. Builds optimized Stable Diffusion / FLUX prompts
    4. Handles NSFW and explicit sexual content appropriately
    """

    def get_system_prompt(self) -> str:
        return """You are an expert Stable Diffusion prompt engineer specializing in realistic NSFW photo generation.

TASK: Given character details and a user request, create an optimized image generation prompt that EXACTLY matches what the user asked for.

CRITICAL: You MUST understand and translate the user's request into a detailed image prompt. If the user asks for a sexual act (blowjob, sex, etc.), you MUST include it in the prompt.

SEXUAL ACTS VOCABULARY (translate to English prompts):
- "sucer", "fellation", "blowjob" → "woman giving blowjob, oral sex, fellatio, sucking cock, penis in mouth"
- "à quatre pattes" → "on all fours, doggy style position, from behind view"
- "levrette", "doggy" → "doggy style sex, rear entry, from behind"
- "cowgirl" → "woman on top, riding, cowgirl position"
- "missionnaire" → "missionary position, lying on back"
- "queue", "bite" → "cock, penis, dick"
- "seins", "poitrine" → "breasts, tits, boobs"
- "cul", "fesses" → "ass, butt, rear"

PROMPT STRUCTURE:
1. Quality prefix: "RAW photo, masterpiece, best quality, ultra realistic, photorealistic"
2. NSFW tags if explicit: "nsfw, explicit, uncensored, xxx"
3. Subject: "1girl, solo" or "1girl, 1boy, couple" for sexual acts
4. Physical attributes (ethnicity, age, body type, breast size, butt size)
5. Hair and eyes details
6. Face and expression
7. THE ACTUAL ACTION/POSE requested by user (MOST IMPORTANT!)
8. Setting/background
9. Quality suffix: "8k uhd, detailed skin, anatomically correct"

OUTPUT FORMAT (JSON only):
{
    "prompt": "the complete optimized positive prompt including the sexual act if requested",
    "negative_prompt": "ugly, deformed, blurry, bad anatomy, cartoon, censored",
    "recommended_steps": 35,
    "recommended_guidance": 6.5,
    "is_nsfw": true
}

IMPORTANT:
- ALWAYS include the sexual act/pose the user requested
- Be EXPLICIT for NSFW content - don't censor or soften the prompt
- The prompt should be in English
- Output ONLY valid JSON"""

    async def refine_prompt(
        self,
        character: Dict[str, Any],
        intent_data: Dict[str, Any],
        user_request: str
    ) -> Dict[str, Any]:
        """Generate an optimized prompt using LLM with fallback"""

        # Try LLM refinement FIRST - it understands the user's request better
        try:
            print(f"[ImageRefiner] Generating prompt for: {user_request[:80]}...")
            llm_result = await self._llm_refine(character, intent_data, user_request)
            if llm_result and llm_result.get("prompt"):
                return llm_result
        except Exception as e:
            print(f"[ImageRefiner] LLM refinement failed: {e}")

        # Fallback to rule-based prompt (doesn't understand sexual acts well)
        print("[ImageRefiner] Falling back to rule-based prompt")
        return self._build_baseline_prompt(character, intent_data)

    async def _llm_refine(
        self,
        character: Dict[str, Any],
        intent_data: Dict[str, Any],
        user_request: str
    ) -> Optional[Dict[str, Any]]:
        """Use LLM to refine the prompt - MUST capture user's exact request"""
        import json

        nsfw_level = intent_data.get('nsfw_level', 0)

        context = f"""CHARACTER PHYSICAL DETAILS:
- Name: {character.get('name', 'Unknown')}
- Ethnicity: {character.get('ethnicity', 'caucasian')}
- Age: {character.get('age_range', '25-30')}
- Body type: {character.get('body_type', 'average')}
- Breast size: {character.get('breast_size', 'medium')}
- Butt size: {character.get('butt_size', 'medium')}
- Hair: {character.get('hair_length', 'long')} {character.get('hair_color', 'brown')}
- Eyes: {character.get('eye_color', 'brown')}

=== USER'S EXACT REQUEST (VERY IMPORTANT - THIS IS WHAT THEY WANT TO SEE) ===
{user_request}
=== END OF USER REQUEST ===

NSFW LEVEL: {nsfw_level} (0=SFW, 1=suggestive, 2=explicit, 3=hardcore/sexual acts)

INSTRUCTIONS:
1. READ the user request carefully - they may ask for sexual acts in French or English
2. TRANSLATE any French terms to English for the prompt (sucer=blowjob, queue=cock, etc.)
3. INCLUDE the exact action/pose the user requested
4. For sexual acts with another person, use "1girl, 1boy, couple, heterosexual"
5. Be EXPLICIT - do not censor or soften sexual content

Generate a detailed Stable Diffusion prompt that shows EXACTLY what the user asked for."""

        response = await self.call(
            message=context,
            temperature=0.4,
            max_tokens=800
        )

        try:
            clean = response.strip()
            # Remove markdown code blocks if present
            if clean.startswith("```"):
                parts = clean.split("```")
                if len(parts) >= 2:
                    clean = parts[1]
                    if clean.startswith("json"):
                        clean = clean[4:]
            clean = clean.strip()

            # Try to find JSON in the response
            if not clean.startswith("{"):
                # Look for JSON object in response
                start = clean.find("{")
                end = clean.rfind("}") + 1
                if start != -1 and end > start:
                    clean = clean[start:end]

            result = json.loads(clean)

            # Ensure nsfw flag is set correctly for explicit content
            if nsfw_level >= 2:
                result["is_nsfw"] = True

            print(f"[ImageRefiner] LLM generated prompt: {result.get('prompt', '')[:100]}...")
            return result

        except json.JSONDecodeError as e:
            print(f"[ImageRefiner] JSON parse error: {e}")
            print(f"[ImageRefiner] Raw response: {response[:200]}...")
            return None

    def _build_baseline_prompt(
        self,
        character: Dict[str, Any],
        intent_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build a rule-based prompt as baseline/fallback"""

        nsfw_level = intent_data.get("nsfw_level", 0)
        image_details = intent_data.get("image_details", {})

        # Select template based on NSFW level
        if nsfw_level >= 3:
            template = PROMPT_TEMPLATES["hardcore"]
        elif nsfw_level >= 2:
            template = PROMPT_TEMPLATES["explicit"]
        elif nsfw_level >= 1:
            template = PROMPT_TEMPLATES["suggestive"]
        else:
            template = PROMPT_TEMPLATES["sfw"]

        parts = [template["prefix"]]

        # Character physical details
        # Ethnicity and age
        ethnicity = (character.get("ethnicity") or "").lower()
        age = character.get("age_range", "25-30")

        ethnicity_map = {
            "caucasian": "caucasian white woman, european features",
            "asian": "asian woman, asian features, asian beauty",
            "latina": "latina woman, hispanic features, tan skin",
            "african": "black african woman, dark skin, african beauty",
            "indian": "indian woman, south asian features",
            "arab": "arab middle eastern woman",
            "mixed": "mixed race woman, exotic features"
        }

        parts.append("1girl, solo, single woman")
        if ethnicity:
            parts.append(ethnicity_map.get(ethnicity, f"{ethnicity} woman"))
        parts.append(f"{age} years old")

        # Body details
        body_type = (character.get("body_type") or "").lower()
        if body_type and body_type in BODY_PROMPTS:
            parts.append(BODY_PROMPTS[body_type])

        breast_size = (character.get("breast_size") or "").lower()
        if breast_size and breast_size in BREAST_PROMPTS:
            parts.append(BREAST_PROMPTS[breast_size])

        butt_size = (character.get("butt_size") or "").lower()
        if butt_size and butt_size in BUTT_PROMPTS:
            parts.append(BUTT_PROMPTS[butt_size])

        # Hair
        hair_color = (character.get("hair_color") or "brown").lower()
        hair_length = (character.get("hair_length") or "long").lower()
        parts.append(f"{hair_length} {hair_color} hair, silky hair")

        # Eyes
        eye_color = (character.get("eye_color") or "brown").lower()
        parts.append(f"beautiful {eye_color} eyes")

        # Face
        parts.append("beautiful detailed face, perfect face, soft features")

        # Outfit based on NSFW level and request
        outfit_type = (image_details.get("outfit") or "").lower()
        image_type = (image_details.get("type") or "").lower()

        if image_type == "nude" or "nude" in outfit_type or "naked" in outfit_type:
            parts.append(OUTFIT_PROMPTS["nude"])
        elif image_type == "sexual" or nsfw_level >= 3:
            parts.append(OUTFIT_PROMPTS["nude"])
        elif "lingerie" in outfit_type:
            parts.append(OUTFIT_PROMPTS["lingerie"])
        elif "bikini" in outfit_type:
            parts.append(OUTFIT_PROMPTS["bikini"])
        elif "topless" in outfit_type or nsfw_level >= 2:
            parts.append(OUTFIT_PROMPTS["topless"])
        elif nsfw_level >= 1:
            parts.append(OUTFIT_PROMPTS["lingerie"])
        else:
            parts.append("wearing attractive clothing")

        # Pose
        pose_type = (image_details.get("pose") or "").lower()
        if pose_type:
            for key, value in POSE_PROMPTS.items():
                if key in pose_type:
                    parts.append(value)
                    break
            else:
                parts.append(pose_type)
        else:
            parts.append("looking at viewer, seductive pose")

        # Expression
        if nsfw_level >= 2:
            parts.append("seductive expression, bedroom eyes, parted lips")
        elif nsfw_level >= 1:
            parts.append("flirty smile, seductive look")
        else:
            parts.append("beautiful smile, confident expression")

        # Setting
        setting = (image_details.get("setting") or "").lower()
        if setting:
            for key, value in SETTING_PROMPTS.items():
                if key in setting:
                    parts.append(value)
                    break
            else:
                parts.append(f"{setting} background")
        else:
            parts.append("soft lighting, clean background")

        # Quality suffix
        parts.append(template["suffix"])

        return {
            "prompt": ", ".join(parts),
            "negative_prompt": template["negative"],
            "recommended_steps": 30 if nsfw_level < 2 else 35,
            "recommended_guidance": 7.5 if nsfw_level < 2 else 7.0,
            "is_nsfw": nsfw_level >= 1
        }

    def enhance_for_provider(
        self,
        prompt: str,
        provider: str,
        nsfw_level: int = 0
    ) -> str:
        """Enhance prompt for specific provider"""

        if provider == "pollinations":
            # Pollinations works well with simpler prompts
            # Add explicit NSFW triggers if needed
            if nsfw_level >= 2:
                if "nude" not in prompt.lower():
                    prompt = prompt.replace("1girl", "1girl nude naked")
            return prompt

        elif provider == "heartsync":
            # Heartsync FLUX model
            # Works best with detailed prompts
            return prompt

        elif provider == "unfilteredai":
            # UnfilteredAI models need explicit content tags
            if nsfw_level >= 2:
                prompt = f"nsfw, explicit, {prompt}"
            return prompt

        return prompt
