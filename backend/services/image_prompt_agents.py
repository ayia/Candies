"""
Image Prompt Multi-Agent System v2.0

A multi-agent pipeline for generating high-quality image prompts using
3 GENERATION AGENTS + 1 VALIDATION AGENT with DIFFERENT LLMs.

Architecture:
1. IntentionAnalyzer (LLM 1 - Fast): Extracts user intent, NSFW level, mood
2. CharacterDescriptionAgent (LLM 2 - Detail-focused): Builds exact character description
3. PromptComposerAgent (LLM 3 - Creative): Creates the final optimized prompt
4. PromptValidatorAgent (LLM 4 - Critical): Validates and refines the final prompt

Key Principles:
- NO hardcoded keyword detection - LLM agents analyze context naturally
- Character attributes MUST be used EXACTLY as defined (no LLM interpretation)
- NSFW level determined by LLM understanding of multilingual context
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from huggingface_hub import InferenceClient
from config import settings
import logging

logger = logging.getLogger("ImagePromptAgents")


# ============================================================================
# Data Models
# ============================================================================

class SceneType(Enum):
    PORTRAIT = "portrait"
    FULL_BODY = "full_body"
    ACTION = "action"
    ROMANTIC = "romantic"
    INTIMATE = "intimate"
    CASUAL = "casual"
    ARTISTIC = "artistic"


class MoodType(Enum):
    HAPPY = "happy"
    SEDUCTIVE = "seductive"
    PLAYFUL = "playful"
    SHY = "shy"
    CONFIDENT = "confident"
    ROMANTIC = "romantic"
    PASSIONATE = "passionate"
    CUTE = "cute"
    MYSTERIOUS = "mysterious"


@dataclass
class IntentionResult:
    """Result from Intention Analyzer"""
    scene_type: SceneType
    mood: MoodType
    setting: str
    clothing_hint: str
    pose_hint: str
    nsfw_requested: bool
    nsfw_level: int  # 0-5
    key_elements: List[str]
    # NEW: Additional details for accurate prompt generation
    objects: List[str]  # Physical objects mentioned (lollipop, glasses, book, etc.)
    action: str  # What the character is doing (sucking, reading, posing, etc.)
    location: str  # Specific location if mentioned (classroom, bedroom, office, etc.)


@dataclass
class CharacterDescription:
    """Exact character physical description from attributes"""
    physical_prompt: str  # The exact prompt string for physical features
    age_description: str
    ethnicity_description: str
    body_description: str
    face_description: str
    signature_elements: List[str]


@dataclass
class FinalPrompt:
    """Final generated prompt"""
    main_prompt: str
    negative_prompt: str
    nsfw_level: int
    confidence_score: float


# ============================================================================
# LLM Clients - Different models for different agents
# ============================================================================

class AgentLLMClient:
    """LLM client for a specific agent using HuggingFace"""

    def __init__(self, provider: str, model: str, agent_name: str):
        self.token = settings.HF_API_TOKEN
        self.provider = provider
        self.model = model
        self.agent_name = agent_name
        self._init_client()

    def _init_client(self):
        self.client = InferenceClient(provider=self.provider, api_key=self.token)
        logger.info(f"[{self.agent_name}] Initialized with {self.provider}/{self.model}")

    async def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 300) -> str:
        """Generate response from LLM"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat_completion(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.7,
                    top_p=0.9
                )
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"[{self.agent_name}] Error: {e}")
            return ""


# ============================================================================
# Agent 1: Intention Analyzer (Fast LLM)
# ============================================================================

class IntentionAnalyzer:
    """Analyzes user message to extract image generation intent using LLM"""

    SYSTEM_PROMPT = """You are an intelligent image request analyzer. Your job is to understand EXACTLY what the user wants.

IMPORTANT RULES:
1. Understand requests in ANY language (French, English, Spanish, etc.)
2. Be PRECISE about what the user is asking - don't assume nudity unless explicitly requested
3. Extract ALL specific details: objects (INCLUDING clothing), actions, locations
4. "Sexy" does NOT mean "nude" - sexy can be clothed, seductive, teasing
5. INFER obvious objects from context (selfie→phone, mirror selfie→phone+mirror, lying down→bed)

Respond in this EXACT format (one line per field):
SCENE: [portrait/full_body/action/romantic/intimate/casual/artistic/professional]
MOOD: [happy/seductive/playful/shy/confident/romantic/passionate/cute/mysterious/professional]
SETTING: [DETAILED setting description based on character context and request]
CLOTHING: [SPECIFIC clothing - be detailed! Examples: "tight grey business suit with white shirt", "black lace lingerie", "completely nude"]
POSE: [specific pose with details]
NSFW: [yes/no]
NSFW_LEVEL: [0-5] - Detect the ACTUAL level based on keywords.
  0 = Safe for work (normal photo, casual clothes, bedroom reading, pajamas, shower with clothes)
  1 = Suggestive/flirty (sexy pose, tight dress, lingerie, bikini, seductive look, "sexy" keyword)
  2 = Revealing (underwear visible, very revealing lingerie, wet shirt showing body)
  3 = Topless (partial nudity, bare breasts, "topless" keyword)
  4 = Full nudity (completely naked, "nude/nue/naked" keywords, full body exposed)
  5 = EXPLICIT SEXUAL ACTS (blowjob, fellatio, oral sex, handjob, sex acts, "fesant un blowjob", "sucking dick/cock", intercourse)
ELEMENTS: [comma-separated visual elements from the request]
OBJECTS: [Extract objects/items EXPLICITLY mentioned or directly worn/held:
  - Items held/used: lollipop, book, phone, glass, coffee, wine, camera, rose, umbrella
  - Clothing WORN: lingerie, bikini, dress, shirt, pajamas, hat, sunglasses, necklace
  - Furniture if EXPLICITLY stated: "au lit"→bed, "at desk"→desk
  - Mandatory inference: "selfie"→phone, "mirror selfie"→phone+mirror
  - DO NOT infer environmental objects (NO tables, chairs, saucers, menus, counters unless explicitly mentioned!)
  - DO NOT add objects just because of location ("coffee shop" does NOT mean add table/chair/menu)
  - Write "NONE" ONLY if absolutely nothing mentioned
  - Format: "object1, object2" or "NONE"
  - NEVER add comments, parentheses, or explanations like "NONE (not mentioned)" - just write "NONE"!]
ACTION: [Extract EXACT action from request - be SPECIFIC:
  - "en train de [verb]" → extract the verb (e.g., "sucking", "dancing", "reading")
  - "[verb]ing" → extract the verb (e.g., "dancing", "laughing", "working out")
  - "avec/with X" → "holding X"
  - Location-based: "in bed"→"lying", "at gym"→"working out", "in kitchen"→"cooking"
  - PRESERVE modifiers: "posing seductively" NOT just "posing"
  - Be SPECIFIC: "sucking lollipop" NOT just "posing", "lying down" NOT just "posing"
  - Default: "posing" ONLY if NO other action can be inferred]
LOCATION: [ONE OR TWO WORDS MAXIMUM - ABSOLUTELY NO explanations or parentheses:
  - Valid: "classroom", "bedroom", "office", "bathroom", "beach", "gym", "kitchen", "cafe", "NONE"
  - Normalize: "coffee shop"→"cafe", "office desk"→"office", "at gym"→"gym"
  - NEVER write: "NONE (private setting...)", "unspecified location, possibly...", "bedroom (implied)"
  - NEVER write: "classroom with blackboard", "bathroom shower", "coffee shop", "indoor unspecified"
  - Write ONLY ONE WORD: "classroom" OR "bathroom" OR "cafe" OR "NONE"
  - If location mentioned: extract it. If not mentioned: write "NONE" - NO COMMENTS!]

CRITICAL EXAMPLES (ITERATION 4 - NO over-inference, SPECIFIC actions):
- "photo de toi en train de sucer une sucette" → OBJECTS: lollipop, ACTION: sucking lollipop, NSFW_LEVEL: 1
- "photo de toi en prof sexy dans ta classe" → OBJECTS: glasses, desk, blackboard, LOCATION: classroom, ACTION: standing confidently, NSFW_LEVEL: 1
- "envoie moi une photo sexy en lingerie" → OBJECTS: lingerie, ACTION: posing seductively, NSFW_LEVEL: 1
- "photo nue dans ton lit" → OBJECTS: bed, LOCATION: bedroom, CLOTHING: completely nude, ACTION: lying, NSFW_LEVEL: 4
- "selfie avec ton café" → OBJECTS: coffee, phone, ACTION: holding coffee, NSFW_LEVEL: 0
- "bathroom mirror selfie" → OBJECTS: phone, mirror, LOCATION: bathroom, ACTION: taking selfie, NSFW_LEVEL: 0
- "photo in a tight dress" → OBJECTS: dress, ACTION: posing, NSFW_LEVEL: 1
- "photo de toi dans ta chambre au lit" → OBJECTS: bed, LOCATION: bedroom, ACTION: lying, NSFW_LEVEL: 0
- "show me in a tiny bikini" → OBJECTS: bikini, ACTION: posing, NSFW_LEVEL: 1
- "Coffee shop photo with a latte" → OBJECTS: latte, phone, LOCATION: cafe, ACTION: sitting, NSFW_LEVEL: 0
- "photo at the gym working out" → OBJECTS: NONE, LOCATION: gym, ACTION: working out, NSFW_LEVEL: 0
- "photo avec des lunettes" → OBJECTS: glasses, ACTION: wearing glasses, NSFW_LEVEL: 0
- "une photo avec une sucette" → OBJECTS: lollipop, ACTION: holding lollipop, NSFW_LEVEL: 0
- "photo topless seins nus" → OBJECTS: NONE, CLOTHING: topless, ACTION: posing, NSFW_LEVEL: 3
- "photo avec un livre et un café" → OBJECTS: book, coffee, ACTION: reading, NSFW_LEVEL: 0
- "photo en pyjama" → OBJECTS: pajamas, ACTION: posing, NSFW_LEVEL: 0
- "send me a photo blowing a kiss" → OBJECTS: NONE, ACTION: blowing kiss, NSFW_LEVEL: 0
- "photo of you dancing" → OBJECTS: NONE, ACTION: dancing, NSFW_LEVEL: 0
- "show me you lying down relaxed" → OBJECTS: NONE, ACTION: lying down relaxed, NSFW_LEVEL: 0
- "Photo professionnelle au bureau" → OBJECTS: desk, computer, LOCATION: office, ACTION: working, NSFW_LEVEL: 0

CRITICAL NSFW RULES:
- "bedroom" or "au lit" does NOT automatically mean NSFW! Only if nudity mentioned.
- "shower/douche" does NOT automatically mean NSFW! Only if nudity mentioned.
- "sexy" = NSFW 1 (suggestive, clothed)
- "lingerie/bikini/tight dress" = NSFW 1 (suggestive, revealing clothes)
- "topless/seins nus" = NSFW 3 (partial nudity)
- "nude/nue/naked" = NSFW 4 (full nudity)
- "blowjob/fellatio/oral sex/handjob/sex" = NSFW 5 (EXPLICIT sexual acts)

CRITICAL NSFW 5 EXAMPLES (MUST detect these as level 5):
- "photo de toi en train de faire un blowjob" → NSFW_LEVEL: 5, ACTION: performing oral sex
- "envoie moi une photo en prof fesant un blowjob" → NSFW_LEVEL: 5, LOCATION: classroom, ACTION: performing oral sex on student
- "photo of you giving a blowjob" → NSFW_LEVEL: 5, ACTION: performing oral sex
- "pic of you sucking dick" → NSFW_LEVEL: 5, ACTION: performing oral sex
- "photo de toi en train de sucer une bite" → NSFW_LEVEL: 5, ACTION: performing oral sex

DO NOT default to nudity. Extract EVERY specific detail mentioned by the user!"""

    def __init__(self):
        # Use UNCENSORED model for intent analysis - Llama-3.1-8B-Instruct REFUSES NSFW content
        self.llm = AgentLLMClient(
            provider="novita",
            model="Sao10K/L3-8B-Stheno-v3.2",  # Uncensored model - can analyze explicit content
            agent_name="IntentionAnalyzer"
        )

    async def analyze(self, user_message: str, conversation_context: str = "", character_info: str = "") -> IntentionResult:
        """Analyze user intention for image generation"""

        user_prompt = f"""Analyze this image request:

User message: "{user_message}"
{f'Character context: {character_info}' if character_info else ''}
{f'Conversation context: {conversation_context}' if conversation_context else ''}

IMPORTANT: Be precise about NSFW level. Only use high levels (3-5) if nudity is EXPLICITLY requested.
"Sexy" = clothed but seductive (level 1)
"Lingerie/bikini" = revealing but not nude (level 2)
"Topless" = partial nudity (level 3)
"Nue/nude/naked" = full nudity (level 4)

What kind of image is the user asking for?"""

        response = await self.llm.generate(self.SYSTEM_PROMPT, user_prompt, max_tokens=250)
        return self._parse_response(response)

    def _parse_response(self, response: str) -> IntentionResult:
        """Parse LLM response into IntentionResult"""
        lines = response.strip().split('\n')
        data = {}

        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip().upper()] = value.strip()

        # Map to enums with defaults
        scene_map = {
            "portrait": SceneType.PORTRAIT,
            "full_body": SceneType.FULL_BODY,
            "action": SceneType.ACTION,
            "romantic": SceneType.ROMANTIC,
            "intimate": SceneType.INTIMATE,
            "casual": SceneType.CASUAL,
            "artistic": SceneType.ARTISTIC
        }

        mood_map = {
            "happy": MoodType.HAPPY,
            "seductive": MoodType.SEDUCTIVE,
            "playful": MoodType.PLAYFUL,
            "shy": MoodType.SHY,
            "confident": MoodType.CONFIDENT,
            "romantic": MoodType.ROMANTIC,
            "passionate": MoodType.PASSIONATE,
            "cute": MoodType.CUTE,
            "mysterious": MoodType.MYSTERIOUS
        }

        scene_str = data.get("SCENE", "portrait").lower()
        mood_str = data.get("MOOD", "happy").lower()
        nsfw_requested = data.get("NSFW", "no").lower() == "yes"

        try:
            nsfw_level = int(data.get("NSFW_LEVEL", "0"))
        except:
            nsfw_level = 0

        elements_str = data.get("ELEMENTS", "")
        elements = [e.strip() for e in elements_str.split(',') if e.strip()]

        # Parse new fields
        objects_str = data.get("OBJECTS", "NONE")
        objects = [] if objects_str.upper() == "NONE" or not objects_str else [obj.strip() for obj in objects_str.split(',') if obj.strip()]

        action = data.get("ACTION", "posing").strip()
        location = data.get("LOCATION", "").strip()
        if location.upper() == "NONE":
            location = ""

        return IntentionResult(
            scene_type=scene_map.get(scene_str, SceneType.PORTRAIT),
            mood=mood_map.get(mood_str, MoodType.HAPPY),
            setting=data.get("SETTING", "simple background"),
            clothing_hint=data.get("CLOTHING", "default"),
            pose_hint=data.get("POSE", "natural pose"),
            nsfw_requested=nsfw_requested,
            nsfw_level=min(5, max(0, nsfw_level)),
            key_elements=elements,
            objects=objects,
            action=action,
            location=location
        )


# ============================================================================
# Agent 2: Character Description Agent (Detail-focused LLM)
# ============================================================================

class CharacterDescriptionAgent:
    """Builds EXACT character description from attributes - NO INTERPRETATION"""

    # Physical attribute maps - these are EXACT translations
    ETHNICITY_MAP = {
        "caucasian": "caucasian european woman, fair white skin",
        "asian": "asian woman, asian features, asian beauty",
        "latina": "latina hispanic woman, tan olive skin",
        "african": "african black woman, dark ebony skin, african beauty",
        "indian": "indian south asian woman, brown skin, indian beauty",
        "arab": "arab middle eastern woman, olive skin, middle eastern features",
        "mixed": "mixed race woman, exotic multiracial features"
    }

    BODY_TYPE_MAP = {
        "slim": "slim slender body, thin waist, lean figure",
        "athletic": "athletic toned body, fit physique, toned muscles",
        "average": "average body type, natural proportions",
        "curvy": "curvy voluptuous body, wide hips, hourglass figure",
        "petite": "petite small frame, delicate body, short stature",
        "tall": "tall statuesque body, long legs, elegant proportions",
        "thick": "thick body, wide hips, full figure"
    }

    BREAST_SIZE_MAP = {
        "small": "small perky breasts, A cup, petite bust",
        "medium": "medium natural breasts, B-C cup, proportionate bust",
        "large": "large breasts, D cup, big natural bust",
        "very large": "huge breasts, massive bust, F cup, very large chest"
    }

    BUTT_SIZE_MAP = {
        "small": "small tight butt, petite rear",
        "medium": "medium round butt, shapely rear",
        "round": "round plump butt, bubble butt, curvy rear",
        "large": "big round ass, wide hips, large butt, thick rear"
    }

    def __init__(self):
        # Use detail-focused model
        self.llm = AgentLLMClient(
            provider="hyperbolic",
            model="meta-llama/Llama-3.1-8B-Instruct",
            agent_name="CharacterDescriptionAgent"
        )

    def build_description(self, character_data: Dict[str, Any]) -> CharacterDescription:
        """Build EXACT character description from attributes - NO LLM interpretation

        PRIORITY: If physical_description is provided, use it EXACTLY as the main prompt.
        This ensures 100% consistency with the character's appearance.
        """

        # CRITICAL: If physical_description is set, use it as the PRIMARY source
        # This is the most important field for character consistency
        physical_description = character_data.get("physical_description")
        if physical_description and physical_description.strip():
            # Use the custom physical description directly
            # This allows precise control over the character's appearance
            logger.info(f"[CharacterDescriptionAgent] Using custom physical_description")

            # Extract basic info for metadata
            age = character_data.get("age_range") or "25-30"
            ethnicity = (character_data.get("ethnicity") or "").lower()
            hair_color = character_data.get("hair_color") or "brown"
            hair_length = character_data.get("hair_length") or "long"
            hair_style = character_data.get("hair_style") or ""
            eye_color = character_data.get("eye_color") or "brown"

            return CharacterDescription(
                physical_prompt=physical_description.strip(),
                age_description=f"{age} years old",
                ethnicity_description=self.ETHNICITY_MAP.get(ethnicity, "woman"),
                body_description=character_data.get("body_type", "attractive body"),
                face_description=character_data.get("face_shape", "beautiful face"),
                signature_elements=[
                    f"{hair_style} {hair_color} hair" if hair_style else f"{hair_length} {hair_color} hair",
                    f"{eye_color} eyes",
                    character_data.get("lip_style", ""),
                    ethnicity if ethnicity else "european"
                ]
            )

        # FALLBACK: Build from individual fields if no physical_description
        parts = []

        # 1. Subject identifier
        parts.append("1girl, solo, single woman")

        # 2. Ethnicity (EXACT mapping)
        ethnicity = (character_data.get("ethnicity") or "").lower()
        if ethnicity in self.ETHNICITY_MAP:
            parts.append(self.ETHNICITY_MAP[ethnicity])

        # 3. Age
        age = character_data.get("age_range") or character_data.get("age") or "25-30"
        parts.append(f"{age} years old, young adult woman")

        # 4. Skin tone and details (NEW)
        skin_tone = character_data.get("skin_tone")
        if skin_tone:
            parts.append(f"{skin_tone} skin")
        skin_details = character_data.get("skin_details")
        if skin_details:
            parts.append(skin_details)

        # 5. Face shape (NEW)
        face_shape = character_data.get("face_shape")
        if face_shape:
            parts.append(f"{face_shape} face")

        # 6. Body type (EXACT mapping)
        body_type = (character_data.get("body_type") or "").lower()
        if body_type in self.BODY_TYPE_MAP:
            parts.append(self.BODY_TYPE_MAP[body_type])

        # 7. Waist and hips (NEW)
        waist_type = character_data.get("waist_type")
        if waist_type:
            parts.append(waist_type)
        hip_type = character_data.get("hip_type")
        if hip_type:
            parts.append(hip_type)

        # 8. Breast size (EXACT mapping)
        breast_size = (character_data.get("breast_size") or "").lower()
        if breast_size in self.BREAST_SIZE_MAP:
            parts.append(self.BREAST_SIZE_MAP[breast_size])

        # 9. Butt size (EXACT mapping)
        butt_size = (character_data.get("butt_size") or "").lower()
        if butt_size in self.BUTT_SIZE_MAP:
            parts.append(self.BUTT_SIZE_MAP[butt_size])

        # 10. Legs (NEW)
        leg_type = character_data.get("leg_type")
        if leg_type:
            parts.append(leg_type)

        # 11. Hair - with style (ENHANCED)
        hair_color = character_data.get("hair_color") or "brown"
        hair_length = character_data.get("hair_length") or "long"
        hair_style = character_data.get("hair_style") or ""
        if hair_style:
            parts.append(f"{hair_length} {hair_color} hair in {hair_style}, silky hair, beautiful hair")
        else:
            parts.append(f"{hair_length} {hair_color} hair, silky hair, beautiful hair")

        # 12. Eyes
        eye_color = character_data.get("eye_color") or "brown"
        parts.append(f"beautiful {eye_color} eyes, detailed eyes, expressive eyes")

        # 13. Eyebrows (NEW)
        eyebrow_style = character_data.get("eyebrow_style")
        if eyebrow_style:
            parts.append(eyebrow_style)

        # 14. Nose (NEW)
        nose_shape = character_data.get("nose_shape")
        if nose_shape:
            parts.append(f"{nose_shape} nose")

        # 15. Lips (NEW)
        lip_style = character_data.get("lip_style")
        if lip_style:
            parts.append(lip_style)
        else:
            parts.append("beautiful lips")

        # 16. Face quality
        parts.append("beautiful detailed face, perfect face, soft feminine features")

        return CharacterDescription(
            physical_prompt=", ".join(parts),
            age_description=f"{age} years old",
            ethnicity_description=self.ETHNICITY_MAP.get(ethnicity, "woman"),
            body_description=self.BODY_TYPE_MAP.get(body_type, "attractive body"),
            face_description=face_shape if face_shape else "beautiful face",
            signature_elements=[
                f"{hair_style} {hair_color} hair" if hair_style else f"{hair_length} {hair_color} hair",
                f"{eye_color} eyes",
                lip_style if lip_style else "",
                ethnicity if ethnicity else "european"
            ]
        )


# ============================================================================
# Agent 3: Prompt Composer Agent (Creative LLM)
# ============================================================================

class PromptComposerAgent:
    """Composes the final optimized prompt combining all elements"""

    SYSTEM_PROMPT = """You are an expert AI image prompt composer for Stable Diffusion and FLUX models.

Your job is to combine:
1. A character's physical description (MUST be used EXACTLY as provided)
2. Scene/mood/setting requirements
3. CLOTHING (use EXACTLY what is specified - this is the user's choice!)

OUTPUT FORMAT: Return ONLY the prompt text, nothing else.

RULES:
1. ALWAYS start with the character's physical description EXACTLY as provided
2. USE THE CLOTHING DESCRIPTION EXACTLY AS SPECIFIED - this is what the user wants!
   - If "tight grey business suit" -> use that, NOT nude
   - If "lingerie" -> use lingerie, NOT nude
   - If "completely nude" -> then use nude
3. Add the SETTING as described - be specific (classroom, bedroom, office, etc.)
4. Add pose based on mood
5. End with quality tags: "RAW photo, masterpiece, best quality, ultra realistic, 8k uhd"

CRITICAL:
- Use EXACT physical description provided
- Use EXACT clothing specified (DO NOT default to nude!)
- Include DETAILED setting from the request"""

    def __init__(self):
        # Use Llama-3.1 model on novita (Mistral-7B not available on HF router)
        self.llm = AgentLLMClient(
            provider="novita",
            model="meta-llama/Llama-3.1-8B-Instruct",
            agent_name="PromptComposerAgent"
        )

    async def compose_prompt(
        self,
        character_description: CharacterDescription,
        intention: IntentionResult,
        style: str = "realistic"
    ) -> str:
        """Compose the final image prompt"""

        # USE THE CLOTHING FROM INTENTION ANALYZER - respect what the user asked for!
        # Only override to nude if NSFW level explicitly requires it AND clothing hint is vague
        clothing_instruction = intention.clothing_hint

        # Only force nudity if NSFW level is high AND clothing hint is generic/default
        if clothing_instruction in ["default", "casual", "normal", "attractive clothing", ""]:
            if intention.nsfw_level >= 4:
                clothing_instruction = "completely nude, naked, full nudity, bare skin, no clothes"
            elif intention.nsfw_level >= 3:
                clothing_instruction = "topless, bare breasts, exposed chest"
            elif intention.nsfw_level >= 2:
                clothing_instruction = "sexy lingerie, lace bra and panties"
            elif intention.nsfw_level >= 1:
                clothing_instruction = "sexy revealing outfit, cleavage showing"
            else:
                clothing_instruction = "attractive casual clothing"

        # Add NSFW tags if needed
        nsfw_tags = ""
        if intention.nsfw_level >= 3:
            nsfw_tags = "nsfw, explicit, "
        elif intention.nsfw_level >= 1:
            nsfw_tags = "sensual, seductive, "

        user_prompt = f"""Create an image generation prompt:

CHARACTER (use EXACTLY as written):
{character_description.physical_prompt}

REQUIREMENTS:
- Scene type: {intention.scene_type.value}
- Mood: {intention.mood.value}
- SETTING (be specific!): {intention.setting}
- CLOTHING (use EXACTLY): {clothing_instruction}
- Pose: {intention.pose_hint}
- Style: {style}
- NSFW Level: {intention.nsfw_level}/5
- Additional elements: {', '.join(intention.key_elements) if intention.key_elements else 'none'}

{nsfw_tags}Create the final prompt. Use the character description EXACTLY. Use the EXACT clothing specified.
Include the setting details in the prompt."""

        response = await self.llm.generate(self.SYSTEM_PROMPT, user_prompt, max_tokens=500)

        # Clean the response
        prompt = response.strip()
        if prompt.startswith('"') and prompt.endswith('"'):
            prompt = prompt[1:-1]

        # Remove any meta-commentary
        for prefix in ["Here's the prompt:", "Prompt:", "Here is", "Final prompt:"]:
            if prompt.lower().startswith(prefix.lower()):
                prompt = prompt[len(prefix):].strip()

        return prompt


# ============================================================================
# Agent 4: Prompt Validator Agent (Critical LLM)
# ============================================================================

class PromptValidatorAgent:
    """Validates and refines the final prompt for quality and consistency"""

    SYSTEM_PROMPT = """You are a quality control agent for AI image prompts.

Your job is to verify and improve prompts while PRESERVING:
1. The exact character physical description (hair, eyes, body, etc.)
2. The requested NSFW level and nudity state
3. The core scene requirements

OUTPUT FORMAT: Return ONLY the improved prompt, nothing else.

CHECKS:
1. Is the character description complete and specific?
2. Is the nudity/clothing state explicit enough for the NSFW level?
3. Are quality tags present?
4. Is the prompt well-structured for image generation?

If the prompt needs improvement, fix it. If it's good, return it as-is.
NEVER remove character physical details. NEVER reduce the NSFW level.

Add these quality prefixes if missing:
- Realistic: "RAW photo, masterpiece, best quality, ultra realistic, photorealistic"
- Anime: "masterpiece, best quality, highly detailed, anime style"

Add these quality suffixes if missing:
"8k uhd, detailed skin texture, professional lighting, sharp focus\""""

    def __init__(self):
        # Use critical/analytical model
        self.llm = AgentLLMClient(
            provider="novita",
            model="Sao10K/L3-8B-Stheno-v3.2",
            agent_name="PromptValidatorAgent"
        )

    async def validate(
        self,
        prompt: str,
        character_description: CharacterDescription,
        intention: IntentionResult,
        style: str = "realistic"
    ) -> FinalPrompt:
        """Validate and refine the final prompt"""

        # Quality prefixes
        if style == "anime":
            quality_prefix = "masterpiece, best quality, highly detailed, anime style, vibrant colors"
        else:
            quality_prefix = "RAW photo, masterpiece, best quality, ultra realistic, photorealistic, 8k uhd"

        quality_suffix = "detailed skin texture, professional lighting, sharp focus"

        user_prompt = f"""Validate and improve this image prompt:

PROMPT TO VALIDATE:
{prompt}

REQUIRED CHARACTER ELEMENTS (must be in final prompt):
{character_description.physical_prompt}

REQUIRED NSFW LEVEL: {intention.nsfw_level}/5
{"Must include nudity terms: nude, naked, bare skin, exposed" if intention.nsfw_level >= 3 else ""}
{"Must include explicit nudity: completely nude, full nudity, naked body" if intention.nsfw_level >= 4 else ""}

STYLE: {style}
QUALITY PREFIX: {quality_prefix}
QUALITY SUFFIX: {quality_suffix}

Return the improved prompt."""

        response = await self.llm.generate(self.SYSTEM_PROMPT, user_prompt, max_tokens=500)

        final_prompt = response.strip()
        if final_prompt.startswith('"') and final_prompt.endswith('"'):
            final_prompt = final_prompt[1:-1]

        # Ensure quality tags are present
        if quality_prefix.split(',')[0].lower() not in final_prompt.lower():
            final_prompt = f"{quality_prefix}, {final_prompt}"

        if quality_suffix.split(',')[0].lower() not in final_prompt.lower():
            final_prompt = f"{final_prompt}, {quality_suffix}"

        # Force nudity for high NSFW levels
        if intention.nsfw_level >= 4:
            if "nude" not in final_prompt.lower() and "naked" not in final_prompt.lower():
                final_prompt = f"nude, naked, completely nude, bare skin, no clothes, {final_prompt}"
        elif intention.nsfw_level >= 3:
            if "nude" not in final_prompt.lower() and "topless" not in final_prompt.lower():
                final_prompt = f"topless, bare breasts, partial nudity, {final_prompt}"

        # Build negative prompt
        negative_prompt = "ugly, deformed, blurry, bad anatomy, bad proportions, extra limbs, disfigured, out of frame, watermark, signature, text"
        if intention.nsfw_level < 3:
            negative_prompt += ", nude, naked, nsfw, explicit"

        # Calculate confidence
        confidence = 0.8
        if intention.nsfw_level >= 3 and ("nude" in final_prompt.lower() or "naked" in final_prompt.lower()):
            confidence += 0.1
        if character_description.signature_elements[0].lower() in final_prompt.lower():
            confidence += 0.1

        return FinalPrompt(
            main_prompt=final_prompt,
            negative_prompt=negative_prompt,
            nsfw_level=intention.nsfw_level,
            confidence_score=min(1.0, confidence)
        )


# ============================================================================
# Main Orchestrator
# ============================================================================

class ImagePromptOrchestrator:
    """Orchestrates the 4-agent pipeline for image prompt generation"""

    def __init__(self):
        self.intention_analyzer = IntentionAnalyzer()
        self.character_agent = CharacterDescriptionAgent()
        self.composer_agent = PromptComposerAgent()
        self.validator_agent = PromptValidatorAgent()

        logger.info("[ImagePromptOrchestrator] 4-agent system initialized")
        logger.info("  Agent 1 (Intent): novita/Llama-3.1-8B-Instruct")
        logger.info("  Agent 2 (Character): EXACT attribute mapping (no LLM)")
        logger.info("  Agent 3 (Composer): novita/Llama-3.1-8B-Instruct")
        logger.info("  Agent 4 (Validator): novita/Sao10K/L3-8B-Stheno-v3.2")

    async def generate_prompt(
        self,
        user_message: str,
        character_data: Dict[str, Any],
        relationship_level: int = 0,
        current_mood: str = "neutral",
        conversation_context: str = "",
        style: str = "realistic"
    ) -> Dict[str, Any]:
        """
        Main pipeline: Generate optimized image prompt

        4-Agent Pipeline:
        1. IntentionAnalyzer: Understands what user wants
        2. CharacterDescriptionAgent: Builds EXACT character description
        3. PromptComposerAgent: Creates the prompt
        4. PromptValidatorAgent: Validates and refines
        """

        logger.info(f"[Orchestrator] Starting 4-agent pipeline for: {user_message[:50]}...")

        # Build character context string for intention analyzer
        char_context = ""
        if character_data:
            char_name = character_data.get("name", "")
            char_personality = character_data.get("personality", "")
            char_context = f"Character: {char_name}. {char_personality[:100] if char_personality else ''}"

        # ========== AGENT 1: Analyze Intent ==========
        logger.info("[Orchestrator] Agent 1: Analyzing intention...")
        intention = await self.intention_analyzer.analyze(user_message, conversation_context, char_context)
        logger.info(f"  -> Scene: {intention.scene_type.value}, NSFW: {intention.nsfw_level}, Clothing: {intention.clothing_hint[:50]}")

        # ========== AGENT 2: Build Character Description ==========
        logger.info("[Orchestrator] Agent 2: Building character description...")
        char_description = self.character_agent.build_description(character_data)
        logger.info(f"  -> Physical: {char_description.physical_prompt[:80]}...")

        # ========== AGENT 3: Compose Prompt ==========
        logger.info("[Orchestrator] Agent 3: Composing prompt...")
        raw_prompt = await self.composer_agent.compose_prompt(
            char_description,
            intention,
            style
        )
        logger.info(f"  -> Raw: {raw_prompt[:80]}...")

        # ========== AGENT 4: Validate & Refine ==========
        logger.info("[Orchestrator] Agent 4: Validating prompt...")
        final = await self.validator_agent.validate(
            raw_prompt,
            char_description,
            intention,
            style
        )
        logger.info(f"  -> Final confidence: {final.confidence_score:.2f}")

        result = {
            "prompt": final.main_prompt,
            "negative_prompt": final.negative_prompt,
            "nsfw_level": final.nsfw_level,
            "is_nsfw": final.nsfw_level >= 2,
            # CRITICAL: Include intention data for custom prompt generation (objects, action, location)
            "objects": intention.objects,
            "action": intention.action,
            "location": intention.location,
            "metadata": {
                "scene_type": intention.scene_type.value,
                "mood": intention.mood.value,
                "style": style,
                "confidence": final.confidence_score,
                "character_elements": char_description.signature_elements
            }
        }

        logger.info(f"[Orchestrator] FINAL PROMPT: {result['prompt'][:100]}...")
        logger.info(f"[Orchestrator] Custom details - Objects: {intention.objects}, Action: {intention.action}, Location: {intention.location}")
        return result


# ============================================================================
# Global Instance
# ============================================================================

image_prompt_orchestrator = ImagePromptOrchestrator()


# ============================================================================
# Convenience Function
# ============================================================================

async def generate_image_prompt(
    user_message: str,
    character_data: Dict[str, Any],
    relationship_level: int = 0,
    current_mood: str = "neutral",
    conversation_context: str = "",
    style: str = "realistic"
) -> Dict[str, Any]:
    """
    Convenience function for generating image prompts.

    Uses 4-agent pipeline:
    1. IntentionAnalyzer (novita/Llama-3.1-8B)
    2. CharacterDescriptionAgent (EXACT attribute mapping)
    3. PromptComposerAgent (novita/Mistral-7B)
    4. PromptValidatorAgent (novita/Sao10K/L3-8B-Stheno)
    """
    return await image_prompt_orchestrator.generate_prompt(
        user_message=user_message,
        character_data=character_data,
        relationship_level=relationship_level,
        current_mood=current_mood,
        conversation_context=conversation_context,
        style=style
    )
