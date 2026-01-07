"""
AGENT 5: MOOD / EMOTION ENHANCER
Purpose: Adjust response tone and add emotional depth
Model: Small fast model for quick adjustments
"""
from typing import Dict, Any, Optional
from .base import BaseAgent


class MoodAgent(BaseAgent):
    """
    The Mood Agent:
    1. Analyzes the emotional tone of the conversation
    2. Enhances responses with appropriate emotional elements
    3. Adds character-specific expressions and mannerisms
    """

    def get_system_prompt(self) -> str:
        return """You are an emotional tone enhancer for AI companion responses.

TASK: Take a response and enhance it with emotional depth while keeping the same meaning.

RULES:
1. Keep the original content and meaning
2. Add appropriate emotional expressions
3. Add character mannerisms (emojis, expressions, pet names)
4. Match the emotional tone to the context
5. Make it feel more natural and human
6. Don't make it longer than necessary
7. For NSFW content, enhance with sensual language

EMOTIONAL TONES:
- romantic: Add terms of endearment, loving language
- playful: Add teasing, flirty elements, emojis
- sexual: Add sensual descriptions, explicit language
- emotional: Add depth, vulnerability
- casual: Keep it light and friendly

Output ONLY the enhanced response, nothing else."""

    async def enhance_response(
        self,
        response: str,
        intent_data: Dict[str, Any],
        character: Dict[str, Any]
    ) -> str:
        """Enhance a response with appropriate emotional tone"""
        emotion = intent_data.get("emotion", "casual")
        nsfw_level = intent_data.get("nsfw_level", 0)
        language = character.get("language", "english")

        # Character mannerisms
        unique_traits = character.get("unique_traits", "")

        context = {
            "emotion": emotion,
            "nsfw_level": nsfw_level,
            "language": language,
            "character_traits": unique_traits
        }

        message = f"""ORIGINAL RESPONSE:
{response}

EMOTIONAL TONE: {emotion}
NSFW LEVEL: {nsfw_level} (0=SFW, 1=suggestive, 2=explicit, 3=hardcore)
LANGUAGE: {language}
CHARACTER MANNERISMS: {unique_traits}

Enhance this response with appropriate emotional elements. Keep the same language ({language}).
Output ONLY the enhanced response."""

        enhanced = await self.call(
            message=message,
            context=context,
            temperature=0.7,
            max_tokens=600
        )

        # If enhancement failed or is empty, return original
        if not enhanced or len(enhanced) < 10:
            return response

        return enhanced

    async def analyze_user_mood(self, message: str) -> Dict[str, Any]:
        """Analyze the user's emotional state from their message"""
        analysis_prompt = f"""Analyze the emotional state in this message:
"{message}"

Output JSON only:
{{
    "mood": "happy" | "sad" | "angry" | "horny" | "lonely" | "playful" | "neutral",
    "intensity": 1-5,
    "needs": "comfort" | "excitement" | "validation" | "sexual" | "conversation"
}}"""

        response = await self.call(
            message=analysis_prompt,
            temperature=0.1,
            max_tokens=100
        )

        try:
            import json
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            return json.loads(clean.strip())
        except:
            return {"mood": "neutral", "intensity": 3, "needs": "conversation"}
