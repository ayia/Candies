"""
Image Prompt Multi-Agent System v1.0

A multi-agent pipeline for generating high-quality image prompts adapted to:
- User requests and intentions
- Character personality and physical attributes
- Relationship level and emotional context
- NSFW modulation based on relationship progression

Agents:
1. IntentionAnalyzer: Extracts user intent, scene type, mood
2. CharacterContextBuilder: Builds character-specific context
3. PromptEngineer: Creates optimized prompts for Z-Image-Turbo/FLUX
4. ContentModerator: Adjusts NSFW level based on relationship
5. PromptValidator: Final validation and refinement
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from huggingface_hub import InferenceClient
from config import settings


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


@dataclass
class CharacterContext:
    """Result from Character Context Builder"""
    physical_description: str
    personality_traits: List[str]
    style_preferences: str
    signature_elements: List[str]
    current_mood: str
    relationship_stage: str


@dataclass
class GeneratedPrompt:
    """Final generated prompt"""
    main_prompt: str
    negative_prompt: str
    style_tags: List[str]
    quality_tags: List[str]
    nsfw_level: int
    confidence_score: float


# ============================================================================
# LLM Client for Agents
# ============================================================================

class AgentLLMClient:
    """Lightweight LLM client for agent tasks using HuggingFace"""

    def __init__(self):
        self.token = settings.HF_API_TOKEN
        # Use fast, capable models for agent tasks
        self.models = [
            ("novita", "meta-llama/Llama-3.1-8B-Instruct"),
            ("hyperbolic", "meta-llama/Llama-3.1-8B-Instruct"),
            ("together", "mistralai/Mistral-7B-Instruct-v0.3"),
        ]
        self.current_model_idx = 0
        self._init_client()

    def _init_client(self):
        provider, model = self.models[self.current_model_idx]
        self.client = InferenceClient(provider=provider, api_key=self.token)
        self.model = model
        self.provider = provider
        print(f"[AgentLLM] Using {provider}/{model}")

    async def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 300) -> str:
        """Generate response from LLM"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        for attempt in range(len(self.models)):
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
                print(f"[AgentLLM] Error with {self.provider}: {e}")
                self.current_model_idx = (self.current_model_idx + 1) % len(self.models)
                self._init_client()

        return ""


# ============================================================================
# Agent 1: Intention Analyzer
# ============================================================================

class IntentionAnalyzer:
    """Analyzes user message to extract image generation intent"""

    SYSTEM_PROMPT = """You are an image request analyzer. Extract the user's intent for image generation.

Respond in this EXACT format (one line per field):
SCENE: [portrait/full_body/action/romantic/intimate/casual/artistic]
MOOD: [happy/seductive/playful/shy/confident/romantic/passionate/cute/mysterious]
SETTING: [brief setting description]
CLOTHING: [clothing hint or "default"]
POSE: [pose hint or "natural"]
NSFW: [yes/no]
NSFW_LEVEL: [0-5, where 0=SFW, 1=suggestive, 2=revealing, 3=sensual, 4=explicit, 5=very explicit]
ELEMENTS: [comma-separated key visual elements]

Be concise. If not specified, use sensible defaults based on context."""

    def __init__(self, llm: AgentLLMClient):
        self.llm = llm

    async def analyze(self, user_message: str, conversation_context: str = "") -> IntentionResult:
        """Analyze user intention for image generation"""

        user_prompt = f"""Analyze this image request:

User message: "{user_message}"
Conversation context: {conversation_context if conversation_context else "None"}

Extract the image generation intent."""

        response = await self.llm.generate(self.SYSTEM_PROMPT, user_prompt, max_tokens=200)

        # Parse response
        return self._parse_response(response, user_message)

    def _parse_response(self, response: str, original_message: str) -> IntentionResult:
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

        # Detect NSFW from original message if not explicitly set
        # Extended keywords for French and English
        nsfw_keywords_explicit = [
            "nude", "naked", "nue", "nu", "topless", "seins", "breasts", "nipple",
            "pussy", "chatte", "bite", "cock", "dick", "penis", "ass", "cul",
            "sex", "sexe", "fuck", "baise", "suce", "blowjob", "fellation",
            "explicit", "explicite", "porn", "porno"
        ]
        nsfw_keywords_suggestive = [
            "sexy", "hot", "lingerie", "seduce", "seductrice", "seductive",
            "sensuel", "sensual", "deshabill", "intime", "coquin", "coquine",
            "revealing", "provocante", "aguicheuse", "string", "underwear"
        ]

        message_lower = original_message.lower()
        has_explicit = any(kw in message_lower for kw in nsfw_keywords_explicit)
        has_suggestive = any(kw in message_lower for kw in nsfw_keywords_suggestive)

        nsfw_requested = data.get("NSFW", "no").lower() == "yes" or has_explicit or has_suggestive

        try:
            nsfw_level = int(data.get("NSFW_LEVEL", "0"))
        except:
            nsfw_level = 0

        # Auto-adjust NSFW level based on detected keywords
        if has_explicit and nsfw_level < 4:
            nsfw_level = 4  # Explicit content
        elif has_suggestive and nsfw_level < 2:
            nsfw_level = 2  # Suggestive content

        elements_str = data.get("ELEMENTS", "")
        elements = [e.strip() for e in elements_str.split(',') if e.strip()]

        return IntentionResult(
            scene_type=scene_map.get(scene_str, SceneType.PORTRAIT),
            mood=mood_map.get(mood_str, MoodType.HAPPY),
            setting=data.get("SETTING", "simple background"),
            clothing_hint=data.get("CLOTHING", "default"),
            pose_hint=data.get("POSE", "natural pose"),
            nsfw_requested=nsfw_requested,
            nsfw_level=min(5, max(0, nsfw_level)),
            key_elements=elements
        )


# ============================================================================
# Agent 2: Character Context Builder
# ============================================================================

class CharacterContextBuilder:
    """Builds character-specific context for image generation"""

    SYSTEM_PROMPT = """You are a character context analyzer for image generation.

Given character data, create a concise visual description optimized for AI image generation.

Respond in this EXACT format:
PHYSICAL: [detailed physical appearance in one line - hair, eyes, body type, skin]
PERSONALITY_VISUAL: [how personality shows in appearance - expressions, posture]
STYLE: [fashion/aesthetic style]
SIGNATURE: [unique visual elements that identify this character]
CURRENT_MOOD_VISUAL: [how current mood affects appearance]

Be specific and visual. Use descriptive adjectives."""

    def __init__(self, llm: AgentLLMClient):
        self.llm = llm

    async def build_context(
        self,
        character_data: Dict[str, Any],
        relationship_level: int = 0,
        current_mood: str = "neutral"
    ) -> CharacterContext:
        """Build character visual context"""

        user_prompt = f"""Build visual context for this character:

Name: {character_data.get('name', 'Unknown')}
Physical traits: {character_data.get('physical_traits', 'not specified')}
Personality: {character_data.get('personality', 'friendly')}
Style: {character_data.get('style', 'casual')}
Age appearance: {character_data.get('age', 'young adult')}
Current mood: {current_mood}
Relationship level with user: {relationship_level}/10

Create the visual context."""

        response = await self.llm.generate(self.SYSTEM_PROMPT, user_prompt, max_tokens=250)

        return self._parse_response(response, character_data, relationship_level, current_mood)

    def _parse_response(
        self,
        response: str,
        character_data: Dict,
        relationship_level: int,
        current_mood: str
    ) -> CharacterContext:
        """Parse LLM response into CharacterContext"""
        lines = response.strip().split('\n')
        data = {}

        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip().upper()] = value.strip()

        # Relationship stage mapping
        stages = {
            0: "stranger", 1: "acquaintance", 2: "casual_friend",
            3: "friend", 4: "close_friend", 5: "special_friend",
            6: "romantic_interest", 7: "dating", 8: "intimate",
            9: "lover", 10: "soulmate"
        }

        # Extract personality traits
        personality_str = data.get("PERSONALITY_VISUAL", character_data.get('personality', ''))
        traits = [t.strip() for t in personality_str.split(',') if t.strip()][:5]

        # Extract signature elements
        signature_str = data.get("SIGNATURE", "")
        signatures = [s.strip() for s in signature_str.split(',') if s.strip()][:3]

        return CharacterContext(
            physical_description=data.get("PHYSICAL", character_data.get('physical_traits', 'beautiful woman')),
            personality_traits=traits if traits else ["friendly", "approachable"],
            style_preferences=data.get("STYLE", character_data.get('style', 'casual elegant')),
            signature_elements=signatures if signatures else [],
            current_mood=data.get("CURRENT_MOOD_VISUAL", current_mood),
            relationship_stage=stages.get(relationship_level, "friend")
        )


# ============================================================================
# Agent 3: Prompt Engineer
# ============================================================================

class PromptEngineer:
    """Creates optimized prompts for image generation models"""

    # Quality tags for different model types
    QUALITY_TAGS_FLUX = [
        "masterpiece", "best quality", "highly detailed",
        "professional photography", "8k uhd", "sharp focus"
    ]

    QUALITY_TAGS_ANIME = [
        "masterpiece", "best quality", "highly detailed",
        "beautiful detailed eyes", "anime style", "vibrant colors"
    ]

    SYSTEM_PROMPT = """You are an expert AI image prompt engineer specializing in character portraits.

Create a prompt optimized for Z-Image-Turbo/FLUX models following these rules:
1. Start with subject description (who)
2. Add physical details (appearance)
3. Include clothing/outfit
4. Describe pose and expression
5. Add setting/background
6. Include lighting and atmosphere
7. Add style descriptors

Format: Write as a flowing description, NOT comma-separated tags.
Example: "A beautiful young woman with long flowing red hair and green eyes, wearing an elegant black dress, standing confidently with a gentle smile, in a cozy cafe with warm ambient lighting, soft bokeh background, professional portrait photography"

Keep it under 200 words. Be specific and visual."""

    def __init__(self, llm: AgentLLMClient):
        self.llm = llm

    async def create_prompt(
        self,
        intention: IntentionResult,
        character_context: CharacterContext,
        style: str = "realistic"  # or "anime"
    ) -> GeneratedPrompt:
        """Create optimized image generation prompt"""

        user_prompt = f"""Create an image generation prompt with these requirements:

CHARACTER:
- Physical: {character_context.physical_description}
- Style: {character_context.style_preferences}
- Current mood: {character_context.current_mood}
- Signature elements: {', '.join(character_context.signature_elements) if character_context.signature_elements else 'none'}

SCENE REQUIREMENTS:
- Scene type: {intention.scene_type.value}
- Mood/atmosphere: {intention.mood.value}
- Setting: {intention.setting}
- Clothing hint: {intention.clothing_hint}
- Pose: {intention.pose_hint}
- Key elements to include: {', '.join(intention.key_elements) if intention.key_elements else 'none'}

NSFW Level: {intention.nsfw_level}/5 (0=SFW, 5=explicit)
Style: {style}

Create the image prompt."""

        response = await self.llm.generate(self.SYSTEM_PROMPT, user_prompt, max_tokens=300)

        # Clean and enhance the prompt
        main_prompt = self._clean_prompt(response)

        # Select quality tags based on style
        quality_tags = self.QUALITY_TAGS_ANIME if style == "anime" else self.QUALITY_TAGS_FLUX

        # Build negative prompt
        negative_prompt = self._build_negative_prompt(intention.nsfw_level)

        # Calculate confidence based on response quality
        confidence = self._calculate_confidence(main_prompt, intention)

        return GeneratedPrompt(
            main_prompt=main_prompt,
            negative_prompt=negative_prompt,
            style_tags=[style, intention.mood.value],
            quality_tags=quality_tags,
            nsfw_level=intention.nsfw_level,
            confidence_score=confidence
        )

    def _clean_prompt(self, response: str) -> str:
        """Clean and format the prompt"""
        # Remove any meta-commentary
        prompt = response.strip()

        # Remove quotes if present
        if prompt.startswith('"') and prompt.endswith('"'):
            prompt = prompt[1:-1]

        # Remove common prefixes
        prefixes_to_remove = [
            "Here's the prompt:", "Prompt:", "Image prompt:",
            "Here is the prompt:", "Generated prompt:"
        ]
        for prefix in prefixes_to_remove:
            if prompt.lower().startswith(prefix.lower()):
                prompt = prompt[len(prefix):].strip()

        return prompt

    def _build_negative_prompt(self, nsfw_level: int) -> str:
        """Build negative prompt based on content level"""
        base_negative = [
            "ugly", "deformed", "blurry", "bad anatomy",
            "bad proportions", "extra limbs", "disfigured",
            "out of frame", "watermark", "signature", "text"
        ]

        if nsfw_level < 3:
            base_negative.extend(["nude", "naked", "nsfw", "explicit"])

        return ", ".join(base_negative)

    def _calculate_confidence(self, prompt: str, intention: IntentionResult) -> float:
        """Calculate confidence score for the generated prompt"""
        score = 0.5  # Base score

        # Check for key elements presence
        prompt_lower = prompt.lower()

        # Physical description present
        if any(word in prompt_lower for word in ["hair", "eyes", "woman", "girl", "man"]):
            score += 0.1

        # Setting present
        if intention.setting.lower() in prompt_lower:
            score += 0.1

        # Mood indicators
        mood_words = {
            MoodType.HAPPY: ["smile", "happy", "cheerful", "bright"],
            MoodType.SEDUCTIVE: ["seductive", "alluring", "sensual", "sultry"],
            MoodType.PLAYFUL: ["playful", "teasing", "fun", "mischievous"],
            MoodType.SHY: ["shy", "bashful", "timid", "blushing"],
            MoodType.CONFIDENT: ["confident", "bold", "powerful", "strong"],
            MoodType.ROMANTIC: ["romantic", "loving", "tender", "intimate"],
            MoodType.PASSIONATE: ["passionate", "intense", "fiery", "burning"],
            MoodType.CUTE: ["cute", "adorable", "sweet", "kawaii"],
            MoodType.MYSTERIOUS: ["mysterious", "enigmatic", "dark", "shadow"]
        }

        if any(word in prompt_lower for word in mood_words.get(intention.mood, [])):
            score += 0.1

        # Length check (good prompts are detailed but not too long)
        word_count = len(prompt.split())
        if 30 <= word_count <= 150:
            score += 0.1

        # Clothing/pose mentioned
        if intention.clothing_hint != "default" and intention.clothing_hint.lower() in prompt_lower:
            score += 0.05

        return min(1.0, score)


# ============================================================================
# Agent 4: Content Moderator
# ============================================================================

class ContentModerator:
    """Moderates content based on relationship level and platform rules"""

    # NSFW allowance by relationship level
    # NOTE: This is an adult platform, so NSFW is allowed at all levels
    # The map is kept for potential future use with relationship progression
    LEVEL_NSFW_MAP = {
        0: 5,   # Stranger: Full NSFW allowed (adult platform)
        1: 5,   # Acquaintance: Full NSFW allowed
        2: 5,   # Casual friend: Full NSFW allowed
        3: 5,   # Friend: Full NSFW allowed
        4: 5,   # Close friend: Full NSFW allowed
        5: 5,   # Special friend: Full NSFW allowed
        6: 5,   # Romantic interest: Full NSFW allowed
        7: 5,   # Dating: Full NSFW allowed
        8: 5,   # Intimate: Full NSFW allowed
        9: 5,   # Lover: Full NSFW allowed
        10: 5   # Soulmate: Full NSFW allowed
    }

    # Terms to moderate by level
    NSFW_REPLACEMENTS = {
        1: {  # Mild
            "naked": "in revealing outfit",
            "nude": "scantily clad",
            "explicit": "suggestive"
        },
        2: {  # Suggestive
            "naked": "in lingerie",
            "nude": "partially undressed",
        },
        3: {  # Sensual
            # Most terms allowed
        }
    }

    def moderate(
        self,
        prompt: GeneratedPrompt,
        relationship_level: int
    ) -> GeneratedPrompt:
        """Moderate prompt based on relationship level"""

        max_allowed_nsfw = self.LEVEL_NSFW_MAP.get(relationship_level, 0)

        # If requested NSFW exceeds allowed, adjust
        if prompt.nsfw_level > max_allowed_nsfw:
            moderated_prompt = self._downgrade_nsfw(
                prompt.main_prompt,
                prompt.nsfw_level,
                max_allowed_nsfw
            )

            return GeneratedPrompt(
                main_prompt=moderated_prompt,
                negative_prompt=prompt.negative_prompt,
                style_tags=prompt.style_tags,
                quality_tags=prompt.quality_tags,
                nsfw_level=max_allowed_nsfw,
                confidence_score=prompt.confidence_score * 0.9  # Slight penalty
            )

        return prompt

    def _downgrade_nsfw(self, prompt: str, current_level: int, target_level: int) -> str:
        """Downgrade NSFW content to target level"""
        result = prompt

        # Apply replacements for each level we need to downgrade
        for level in range(target_level + 1, current_level + 1):
            replacements = self.NSFW_REPLACEMENTS.get(level, {})
            for explicit, mild in replacements.items():
                result = result.replace(explicit, mild)

        # If target is SFW, ensure no explicit terms remain
        if target_level == 0:
            explicit_terms = [
                "sexy", "seductive", "sensual", "revealing", "lingerie",
                "naked", "nude", "explicit", "provocative"
            ]
            for term in explicit_terms:
                result = result.replace(term, "elegant")

        return result


# ============================================================================
# Agent 5: Prompt Validator
# ============================================================================

class PromptValidator:
    """Validates and refines the final prompt"""

    MIN_PROMPT_LENGTH = 50
    MAX_PROMPT_LENGTH = 500

    REQUIRED_ELEMENTS = [
        "subject",  # Must describe a person/character
        "appearance",  # Physical details
    ]

    def validate(self, prompt: GeneratedPrompt) -> GeneratedPrompt:
        """Validate and refine the final prompt"""

        main_prompt = prompt.main_prompt
        issues = []

        # Check length
        if len(main_prompt) < self.MIN_PROMPT_LENGTH:
            main_prompt = self._expand_prompt(main_prompt, prompt.quality_tags)
            issues.append("expanded_short_prompt")

        if len(main_prompt) > self.MAX_PROMPT_LENGTH:
            main_prompt = self._truncate_prompt(main_prompt)
            issues.append("truncated_long_prompt")

        # Check for subject
        if not self._has_subject(main_prompt):
            main_prompt = "A beautiful woman, " + main_prompt
            issues.append("added_subject")

        # Add quality tags if not present
        main_prompt = self._ensure_quality_tags(main_prompt, prompt.quality_tags)

        # Calculate adjusted confidence
        confidence = prompt.confidence_score
        if issues:
            confidence *= (1 - 0.05 * len(issues))

        return GeneratedPrompt(
            main_prompt=main_prompt,
            negative_prompt=prompt.negative_prompt,
            style_tags=prompt.style_tags,
            quality_tags=prompt.quality_tags,
            nsfw_level=prompt.nsfw_level,
            confidence_score=max(0.3, confidence)
        )

    def _expand_prompt(self, prompt: str, quality_tags: List[str]) -> str:
        """Expand a short prompt with quality descriptors"""
        expansions = [
            "detailed", "beautiful", "high quality",
            "professional lighting", "sharp focus"
        ]
        return f"{prompt}, {', '.join(expansions[:3])}"

    def _truncate_prompt(self, prompt: str) -> str:
        """Truncate a long prompt while keeping coherence"""
        # Keep first 450 characters, find last complete word
        truncated = prompt[:450]
        last_space = truncated.rfind(' ')
        if last_space > 400:
            truncated = truncated[:last_space]
        return truncated

    def _has_subject(self, prompt: str) -> bool:
        """Check if prompt has a clear subject"""
        subject_words = [
            "woman", "man", "girl", "boy", "person", "lady", "guy",
            "she", "he", "character", "figure", "model"
        ]
        prompt_lower = prompt.lower()
        return any(word in prompt_lower for word in subject_words)

    def _ensure_quality_tags(self, prompt: str, quality_tags: List[str]) -> str:
        """Ensure quality tags are present"""
        prompt_lower = prompt.lower()
        missing_tags = [tag for tag in quality_tags[:3] if tag.lower() not in prompt_lower]

        if missing_tags:
            return f"{prompt}, {', '.join(missing_tags)}"
        return prompt


# ============================================================================
# Main Orchestrator
# ============================================================================

class ImagePromptOrchestrator:
    """Orchestrates the multi-agent pipeline for image prompt generation"""

    def __init__(self):
        self.llm = AgentLLMClient()
        self.intention_analyzer = IntentionAnalyzer(self.llm)
        self.context_builder = CharacterContextBuilder(self.llm)
        self.prompt_engineer = PromptEngineer(self.llm)
        self.content_moderator = ContentModerator()
        self.validator = PromptValidator()

        print("[ImagePromptOrchestrator] Multi-agent system initialized")

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

        Returns dict with:
        - prompt: The main prompt string
        - negative_prompt: Negative prompt string
        - nsfw_level: Final NSFW level (0-5)
        - metadata: Additional info about the generation
        """

        print(f"[Orchestrator] Starting prompt generation for: {user_message[:50]}...")

        # Step 1: Analyze user intention
        print("[Orchestrator] Step 1: Analyzing intention...")
        intention = await self.intention_analyzer.analyze(
            user_message,
            conversation_context
        )
        print(f"  -> Scene: {intention.scene_type.value}, Mood: {intention.mood.value}, NSFW: {intention.nsfw_level}")

        # Step 2: Build character context
        print("[Orchestrator] Step 2: Building character context...")
        character_context = await self.context_builder.build_context(
            character_data,
            relationship_level,
            current_mood
        )
        print(f"  -> Physical: {character_context.physical_description[:50]}...")

        # Step 3: Engineer the prompt
        print("[Orchestrator] Step 3: Engineering prompt...")
        generated = await self.prompt_engineer.create_prompt(
            intention,
            character_context,
            style
        )
        print(f"  -> Raw prompt length: {len(generated.main_prompt)} chars")

        # Step 4: Moderate content based on relationship
        print(f"[Orchestrator] Step 4: Moderating (relationship level: {relationship_level})...")
        moderated = self.content_moderator.moderate(generated, relationship_level)
        print(f"  -> NSFW adjusted: {generated.nsfw_level} -> {moderated.nsfw_level}")

        # Step 5: Validate and refine
        print("[Orchestrator] Step 5: Validating...")
        final = self.validator.validate(moderated)
        print(f"  -> Final confidence: {final.confidence_score:.2f}")

        result = {
            "prompt": final.main_prompt,
            "negative_prompt": final.negative_prompt,
            "nsfw_level": final.nsfw_level,
            "is_nsfw": final.nsfw_level >= 2,
            "metadata": {
                "scene_type": intention.scene_type.value,
                "mood": intention.mood.value,
                "style": style,
                "confidence": final.confidence_score,
                "relationship_stage": character_context.relationship_stage,
                "quality_tags": final.quality_tags
            }
        }

        print(f"[Orchestrator] Final prompt: {result['prompt'][:100]}...")
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

    Args:
        user_message: The user's message requesting an image
        character_data: Dict with character info (name, physical_traits, personality, etc.)
        relationship_level: 0-10 relationship level
        current_mood: Character's current emotional state
        conversation_context: Recent conversation for context
        style: "realistic" or "anime"

    Returns:
        Dict with prompt, negative_prompt, nsfw_level, is_nsfw, metadata
    """
    return await image_prompt_orchestrator.generate_prompt(
        user_message=user_message,
        character_data=character_data,
        relationship_level=relationship_level,
        current_mood=current_mood,
        conversation_context=conversation_context,
        style=style
    )
