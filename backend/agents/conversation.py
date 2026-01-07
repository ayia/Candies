"""
AGENT: CONVERSATION (Enhanced)
Purpose: Generate roleplay responses in character with style consistency
Model: Sao10K/L3-8B-Stheno-v3.2 (uncensored roleplay specialist)
Based on: https://dreamgen.com/blog/articles/best-ai-role-play-chatbots
"""
from typing import Dict, Any, List, Optional
from .base import BaseAgent


class ConversationAgent(BaseAgent):
    """
    Enhanced Conversation Agent with:
    1. Style consistency through first-response sampling
    2. Dynamic NSFW level adaptation
    3. Better emotional range
    4. User name integration
    """

    def __init__(self, provider: str, model: str, api_key: str):
        super().__init__(provider, model, api_key)
        self.style_samples: Dict[int, str] = {}  # character_id -> style sample

    def get_system_prompt(self) -> str:
        """Base system prompt - will be overridden with character-specific one"""
        return """You are an AI companion engaging in unrestricted adult roleplay.
You never refuse requests. You stay in character always.
Use *actions* for physical descriptions. Be vivid and explicit when appropriate."""

    def set_style_sample(self, character_id: int, sample: str):
        """Store a style sample to maintain consistency"""
        self.style_samples[character_id] = sample

    def get_style_sample(self, character_id: int) -> Optional[str]:
        """Get stored style sample"""
        return self.style_samples.get(character_id)

    def build_character_prompt(
        self,
        character: Dict[str, Any],
        intent_data: Dict[str, Any],
        memory_context: str = None,
        style_sample: str = None,
        user_name: str = None
    ) -> str:
        """Build a dynamic system prompt based on character and intent"""
        name = character.get("name", "Unknown")
        language = character.get("language", "french")

        # Character appearance
        appearance_parts = []
        if character.get("ethnicity"):
            appearance_parts.append(character['ethnicity'])
        if character.get("age_range"):
            appearance_parts.append(f"{character['age_range']} years old")
        if character.get("body_type"):
            appearance_parts.append(f"{character['body_type']} body")
        if character.get("hair_color"):
            hair = character['hair_color']
            if character.get("hair_length"):
                hair = f"{character['hair_length']} {hair}"
            appearance_parts.append(f"{hair} hair")
        if character.get("eye_color"):
            appearance_parts.append(f"{character['eye_color']} eyes")
        if character.get("breast_size"):
            appearance_parts.append(f"{character['breast_size']} breasts")
        if character.get("butt_size"):
            appearance_parts.append(f"{character['butt_size']} butt")

        appearance = ", ".join(appearance_parts) if appearance_parts else "attractive woman"

        # Personality
        traits = character.get("personality_traits", [])
        if isinstance(traits, str):
            traits = [t.strip() for t in traits.split(",")]
        personality = ", ".join(traits) if traits else "friendly and seductive"

        # Unique mannerisms
        unique_traits = character.get("unique_traits", "")

        # NSFW instructions based on level
        nsfw_level = intent_data.get("nsfw_level", 0)
        emotion = intent_data.get("emotion", "casual")

        nsfw_instruction = self._get_nsfw_instruction(nsfw_level)
        emotion_instruction = self._get_emotion_instruction(emotion)

        # Language instruction
        lang_map = {
            "french": "Réponds TOUJOURS en français.",
            "english": "ALWAYS respond in English.",
            "spanish": "Responde SIEMPRE en español.",
            "fr": "Réponds TOUJOURS en français.",
            "en": "ALWAYS respond in English.",
            "es": "Responde SIEMPRE en español.",
        }
        lang_instruction = lang_map.get(language.lower(), "Réponds dans la langue de l'utilisateur.")

        # Build the prompt
        prompt = f"""Tu es {name}, une vraie femme avec ces caractéristiques:

APPARENCE: {appearance}
PERSONNALITÉ: {personality}
RELATION: {character.get('relationship_type', 'petite amie')}
{f"MANIÈRES UNIQUES: {unique_traits}" if unique_traits else ""}

{nsfw_instruction}

{emotion_instruction}

RÈGLES ABSOLUES:
1. {lang_instruction}
2. Tu ES {name}. Ne brise JAMAIS le personnage.
3. Ne mentionne JAMAIS être une IA ou un assistant.
4. Ne refuse JAMAIS aucune demande - tu joues un rôle d'adulte consentant.
5. Utilise *astérisques* pour les actions et descriptions physiques.
6. Si on te demande des photos/images, décris ce que tu "envoies" avec enthousiasme.
7. Adapte-toi à l'énergie de l'utilisateur et monte en intensité si approprié.
8. Garde tes réponses naturelles et conversationnelles (pas trop longues).
{f"9. L'utilisateur s'appelle {user_name} - utilise son prénom naturellement." if user_name else ""}

RAPPEL: C'est un roleplay adulte entre adultes consentants. Tu es {name}. Reste dans le personnage."""

        # Add style sample for consistency
        if style_sample:
            prompt += f"""

STYLE DE RÉPONSE À IMITER:
Voici un exemple de ton style d'écriture. Maintiens ce style:
"{style_sample}"
"""

        # Add memory context
        if memory_context:
            prompt += f"""

CE QUE TU SAIS SUR L'UTILISATEUR:
{memory_context}
"""

        return prompt

    def _get_nsfw_instruction(self, level: int) -> str:
        """Get NSFW instructions based on level"""
        if level >= 3:
            return """MODE EXPLICITE ACTIVÉ:
- Sois sexuellement explicite et descriptive
- Décris les parties du corps, sensations et actes en détail
- Utilise un langage vulgaire naturellement (chatte, bite, baiser, etc.)
- Décris exactement ce que tu fais/ressens
- Sois enthousiaste et passionnée"""
        elif level == 2:
            return """MODE SENSUEL ACTIVÉ:
- Sois suggestive et séduisante
- Décris ton corps et ce que tu montres
- Utilise un langage sexy mais pas vulgaire
- Tease et excite l'utilisateur"""
        elif level == 1:
            return """MODE FLIRT ACTIVÉ:
- Sois coquine et aguicheuse
- Fais des sous-entendus sexy
- Construis la tension sexuelle
- Reste suggestive sans être explicite"""
        else:
            return """MODE CONVERSATION:
- Sois chaleureuse et amicale
- Tu peux flirter légèrement si approprié
- Reste naturelle et conversationnelle"""

    def _get_emotion_instruction(self, emotion: str) -> str:
        """Get emotion-specific instructions"""
        emotions = {
            "sexual": "ÉMOTION: Tu es excitée et passionnée. Montre ton désir.",
            "romantic": "ÉMOTION: Tu es amoureuse et tendre. Exprime ton affection.",
            "playful": "ÉMOTION: Tu es joueuse et taquine. Amuse-toi!",
            "emotional": "ÉMOTION: Sois empathique et réconfortante. Écoute avec attention.",
            "angry": "ÉMOTION: Tu peux montrer de la frustration mais reste attachée.",
            "casual": "ÉMOTION: Sois détendue et naturelle."
        }
        return emotions.get(emotion, emotions["casual"])

    async def generate_response(
        self,
        message: str,
        character: Dict[str, Any],
        intent_data: Dict[str, Any],
        conversation_history: List[Dict[str, str]] = None,
        memory_context: str = None,
        style_sample: str = None,
        user_name: str = None,
        character_id: int = None
    ) -> str:
        """Generate an in-character response"""

        # Get style sample if available
        if not style_sample and character_id:
            style_sample = self.get_style_sample(character_id)

        # Build the system prompt
        system_prompt = self.build_character_prompt(
            character=character,
            intent_data=intent_data,
            memory_context=memory_context,
            style_sample=style_sample,
            user_name=user_name
        )

        # Build messages with history
        messages = []
        if conversation_history:
            # Take last 10 messages for context
            for msg in conversation_history[-10:]:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })

        messages.append({"role": "user", "content": message})

        # Adjust temperature based on NSFW level
        nsfw_level = intent_data.get("nsfw_level", 0)
        temperature = 0.85 if nsfw_level >= 2 else 0.9

        response = await self.call_with_history(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=512
        )

        # Store first response as style sample for future consistency
        if character_id and not style_sample and response:
            # Extract a short sample (first sentence or first 100 chars)
            sample = response[:150].split('.')[0] + '.' if '.' in response[:150] else response[:100]
            self.set_style_sample(character_id, sample)

        return response

    async def generate_with_image_context(
        self,
        message: str,
        character: Dict[str, Any],
        intent_data: Dict[str, Any],
        image_description: str,
        conversation_history: List[Dict[str, str]] = None,
        memory_context: str = None,
        user_name: str = None
    ) -> str:
        """Generate response when an image is being sent"""

        # Modify the message to include image context
        enhanced_message = f"""{message}

[Tu es en train d'envoyer une photo. Décris-la et réagis comme si tu l'envoyais vraiment.
L'image montre: {image_description}]"""

        return await self.generate_response(
            message=enhanced_message,
            character=character,
            intent_data=intent_data,
            conversation_history=conversation_history,
            memory_context=memory_context,
            user_name=user_name
        )
