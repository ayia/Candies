"""
AGENT: IMAGE PROMPT GENERATOR (Enhanced v3.0)
Purpose: Generate optimized image generation prompts using Multi-Agent System
Model: Fast model for structured output + Multi-Agent Pipeline for optimization

Architecture:
- IntentionAnalyzer: Extracts user intent, scene type, mood
- CharacterContextBuilder: Builds character-specific visual context
- PromptEngineer: Creates optimized prompts for Z-Image-Turbo/FLUX
- ContentModerator: Adjusts NSFW level based on relationship
- PromptValidator: Final validation and refinement
"""
import json
from typing import Dict, Any, Optional
from .base import BaseAgent
from .image_refiner import ImageRefinerAgent, PROMPT_TEMPLATES, BODY_PROMPTS, BREAST_PROMPTS, BUTT_PROMPTS

# Import new multi-agent system
try:
    from services.image_prompt_agents import generate_image_prompt as multi_agent_generate
    MULTI_AGENT_AVAILABLE = True
    print("[ImageAgent] Multi-agent prompt system loaded")
except ImportError as e:
    MULTI_AGENT_AVAILABLE = False
    print(f"[ImageAgent] Multi-agent system not available: {e}")


class ImagePromptAgent(BaseAgent):
    """
    Enhanced Image Agent with:
    1. Integration with ImageRefinerAgent for optimized prompts
    2. Multi-level NSFW support
    3. Character-accurate physical descriptions
    4. Provider-specific prompt optimization
    """

    def __init__(self, provider: str, model: str, api_key: str):
        super().__init__(provider, model, api_key)
        # Initialize the refiner agent with same credentials
        self.refiner = ImageRefinerAgent(provider, model, api_key)

    def get_system_prompt(self) -> str:
        return """You are an expert at creating image generation prompts for Stable Diffusion / FLUX models.

TASK: Given a character description and user request, create an optimized image prompt.

OUTPUT FORMAT (JSON only):
{
    "prompt": "detailed positive prompt for image generation",
    "negative_prompt": "things to avoid",
    "nsfw": true/false,
    "style": "realistic" or "anime"
}

PROMPT STRUCTURE FOR REALISTIC PHOTOS:
1. Quality prefix: "RAW photo, masterpiece, best quality, ultra realistic, photorealistic"
2. Subject: "1girl, solo, single woman"
3. Ethnicity and age
4. Body details: body type, breast size, butt size (be specific!)
5. Hair: length, color, style
6. Eyes: color, expression
7. Face: features, expression
8. Clothing/nudity state
9. Pose and camera angle
10. Setting/background
11. Quality suffix: "8k uhd, dslr quality, detailed skin texture"

FOR NSFW CONTENT:
- Level 1 (Suggestive): lingerie, revealing, seductive poses
- Level 2 (Explicit): topless, nudity, exposed body
- Level 3 (Hardcore): full nudity, explicit poses, sexual content

Be VERY specific about physical attributes for consistent character appearance.
Output ONLY valid JSON."""

    async def generate_image_prompt(
        self,
        character: Dict[str, Any],
        intent_data: Dict[str, Any],
        user_request: str,
        relationship_level: int = 0,
        current_mood: str = "neutral",
        conversation_context: str = ""
    ) -> Dict[str, Any]:
        """
        Generate an optimized image prompt using the multi-agent system.

        Pipeline:
        1. Try new multi-agent system (5 specialized agents)
        2. Fallback to ImageRefiner
        3. Final fallback to LLM-based generation
        """
        nsfw_level = intent_data.get("nsfw_level", 0)

        # PRIORITY 1: Use the new multi-agent prompt system
        if MULTI_AGENT_AVAILABLE:
            try:
                print("[ImageAgent] Using multi-agent prompt system...")

                # Build character data dict for agents
                character_data = {
                    "name": character.get("name", ""),
                    "physical_traits": self._build_character_description(character),
                    "personality": character.get("personality", "friendly"),
                    "style": character.get("style", "realistic"),
                    "age": character.get("age_range", "25-30"),
                    "ethnicity": character.get("ethnicity", ""),
                    "body_type": character.get("body_type", ""),
                    "breast_size": character.get("breast_size", ""),
                    "butt_size": character.get("butt_size", ""),
                    "hair_color": character.get("hair_color", ""),
                    "hair_length": character.get("hair_length", ""),
                    "eye_color": character.get("eye_color", "")
                }

                result = await multi_agent_generate(
                    user_message=user_request,
                    character_data=character_data,
                    relationship_level=relationship_level,
                    current_mood=current_mood,
                    conversation_context=conversation_context,
                    style=character.get("style", "realistic")
                )

                if result and result.get("prompt"):
                    # Get the NSFW level from the multi-agent result
                    multi_agent_nsfw_level = result.get("nsfw_level", nsfw_level)
                    print(f"[ImageAgent] Multi-agent success: {result['prompt'][:80]}...")
                    print(f"[ImageAgent] Multi-agent NSFW level: {multi_agent_nsfw_level}")
                    return {
                        "prompt": result["prompt"],
                        "negative_prompt": result.get("negative_prompt", ""),
                        "nsfw": result.get("is_nsfw", multi_agent_nsfw_level >= 1),
                        "nsfw_level": multi_agent_nsfw_level,  # Propagate the NSFW level!
                        "style": character.get("style", "realistic"),
                        "steps": 8,  # Z-Image-Turbo optimal
                        "guidance": 0.0,  # Z-Image-Turbo doesn't use guidance
                        "metadata": result.get("metadata", {})
                    }
            except Exception as e:
                print(f"[ImageAgent] Multi-agent error: {e}, trying refiner...")

        # PRIORITY 2: Use the ImageRefiner
        try:
            refined = await self.refiner.refine_prompt(
                character=character,
                intent_data=intent_data,
                user_request=user_request
            )

            if refined and refined.get("prompt"):
                return {
                    "prompt": refined["prompt"],
                    "negative_prompt": refined.get("negative_prompt", self._get_negative_prompt(intent_data)),
                    "nsfw": refined.get("is_nsfw", nsfw_level >= 1),
                    "style": character.get("style", "realistic"),
                    "steps": refined.get("recommended_steps", 30),
                    "guidance": refined.get("recommended_guidance", 7.0)
                }
        except Exception as e:
            print(f"[ImageAgent] Refiner error: {e}, using LLM fallback")

        # PRIORITY 3: Fallback to LLM-based generation
        return await self._llm_generate(character, intent_data, user_request)

    async def _llm_generate(
        self,
        character: Dict[str, Any],
        intent_data: Dict[str, Any],
        user_request: str
    ) -> Dict[str, Any]:
        """Fallback LLM-based prompt generation"""
        char_description = self._build_character_description(character)
        image_details = intent_data.get("image_details", {})
        nsfw_level = intent_data.get("nsfw_level", 0)

        context_message = f"""CHARACTER DESCRIPTION:
{char_description}

USER REQUEST: {user_request}

IMAGE DETAILS:
- Type: {image_details.get('type', 'selfie')}
- Outfit: {image_details.get('outfit', 'not specified')}
- Pose: {image_details.get('pose', 'not specified')}
- Setting: {image_details.get('setting', 'not specified')}
- NSFW Level: {nsfw_level} (0=SFW, 1=suggestive, 2=explicit, 3=hardcore)

Generate an optimized, detailed image prompt for Stable Diffusion.
Be VERY specific about physical attributes (body type, breast size, etc.)
For NSFW: be explicit about nudity and body exposure."""

        try:
            response = await self.call(
                message=context_message,
                temperature=0.3,
                max_tokens=600
            )

            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = clean_response.split("```")[1]
                if clean_response.startswith("json"):
                    clean_response = clean_response[4:]
            clean_response = clean_response.strip()

            result = json.loads(clean_response)
            result["nsfw"] = result.get("nsfw", nsfw_level >= 1)
            return result
        except (json.JSONDecodeError, Exception) as e:
            print(f"[ImageAgent] LLM parse error: {e}")
            return self._fallback_prompt(character, intent_data)

    def _build_character_description(self, character: Dict[str, Any]) -> str:
        """Build detailed character description for LLM"""
        parts = []

        if character.get("name"):
            parts.append(f"Name: {character['name']}")
        if character.get("ethnicity"):
            parts.append(f"Ethnicity: {character['ethnicity']}")
        if character.get("age_range"):
            parts.append(f"Age: {character['age_range']}")
        if character.get("body_type"):
            parts.append(f"Body type: {character['body_type']}")
        if character.get("breast_size"):
            parts.append(f"Breast size: {character['breast_size']}")
        if character.get("butt_size"):
            parts.append(f"Butt size: {character['butt_size']}")
        if character.get("hair_color"):
            hair = character['hair_color']
            if character.get("hair_length"):
                hair = f"{character['hair_length']} {hair}"
            parts.append(f"Hair: {hair}")
        if character.get("eye_color"):
            parts.append(f"Eyes: {character['eye_color']}")

        return "\n".join(parts) if parts else "Attractive woman"

    def _get_negative_prompt(self, intent_data: Dict[str, Any]) -> str:
        """Get appropriate negative prompt based on NSFW level"""
        nsfw_level = intent_data.get("nsfw_level", 0)

        if nsfw_level >= 3:
            return PROMPT_TEMPLATES["hardcore"]["negative"]
        elif nsfw_level >= 2:
            return PROMPT_TEMPLATES["explicit"]["negative"]
        elif nsfw_level >= 1:
            return PROMPT_TEMPLATES["suggestive"]["negative"]
        else:
            return PROMPT_TEMPLATES["sfw"]["negative"]

    def _fallback_prompt(self, character: Dict[str, Any], intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a fallback prompt using templates"""
        nsfw_level = intent_data.get("nsfw_level", 0)
        style = character.get("style", "realistic")
        image_details = intent_data.get("image_details", {})

        # Select template
        if nsfw_level >= 3:
            template = PROMPT_TEMPLATES["hardcore"]
        elif nsfw_level >= 2:
            template = PROMPT_TEMPLATES["explicit"]
        elif nsfw_level >= 1:
            template = PROMPT_TEMPLATES["suggestive"]
        else:
            template = PROMPT_TEMPLATES["sfw"]

        parts = [template["prefix"]]

        # Subject
        parts.append("1girl, solo, single woman")

        # Ethnicity
        ethnicity = (character.get("ethnicity") or "").lower()
        ethnicity_map = {
            "caucasian": "caucasian white woman, european features",
            "asian": "asian woman, asian features, asian beauty",
            "latina": "latina woman, hispanic features, tan skin",
            "african": "black african woman, dark skin, african beauty",
            "indian": "indian woman, south asian features",
            "arab": "arab middle eastern woman",
            "mixed": "mixed race woman, exotic features"
        }
        if ethnicity in ethnicity_map:
            parts.append(ethnicity_map[ethnicity])
        elif ethnicity:
            parts.append(f"{ethnicity} woman")

        # Age
        age = character.get("age_range", "25-30")
        parts.append(f"{age} years old")

        # Body type
        body_type = (character.get("body_type") or "").lower()
        if body_type in BODY_PROMPTS:
            parts.append(BODY_PROMPTS[body_type])

        # Breast size
        breast_size = (character.get("breast_size") or "").lower()
        if breast_size in BREAST_PROMPTS:
            parts.append(BREAST_PROMPTS[breast_size])

        # Butt size
        butt_size = (character.get("butt_size") or "").lower()
        if butt_size in BUTT_PROMPTS:
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

        # Outfit based on request and NSFW level
        outfit_type = (image_details.get("outfit") or "").lower()
        image_type = (image_details.get("type") or "").lower()

        if image_type == "nude" or "nude" in outfit_type or nsfw_level >= 3:
            parts.append("nude, naked, no clothes, fully nude, bare skin, exposed breasts")
        elif nsfw_level >= 2 or "topless" in outfit_type:
            parts.append("topless, bare breasts, exposed chest")
        elif "lingerie" in outfit_type:
            parts.append("wearing sexy lingerie, lace bra and panties")
        elif "bikini" in outfit_type:
            parts.append("wearing bikini, swimsuit")
        elif nsfw_level >= 1:
            parts.append("wearing sexy lingerie, revealing outfit")
        else:
            parts.append("wearing attractive clothing")

        # Pose
        pose = image_details.get("pose", "")
        if pose:
            parts.append(pose)
        elif nsfw_level >= 2:
            parts.append("seductive pose, bedroom eyes, parted lips, looking at viewer")
        elif nsfw_level >= 1:
            parts.append("flirty pose, seductive smile, looking at viewer")
        else:
            parts.append("natural pose, looking at viewer, confident expression")

        # Setting
        setting = image_details.get("setting", "")
        if setting:
            parts.append(f"{setting} background")
        else:
            parts.append("soft lighting, clean background")

        # Quality suffix
        parts.append(template["suffix"])

        prompt = ", ".join(parts)

        return {
            "prompt": prompt,
            "negative_prompt": template["negative"],
            "nsfw": nsfw_level >= 1,
            "style": style,
            "steps": 30 if nsfw_level < 2 else 35,
            "guidance": 7.0 if nsfw_level < 2 else 6.5
        }
