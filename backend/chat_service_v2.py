"""
Chat Service V2 - Enhanced with Candy.ai-inspired features

New Features:
1. Intelligent context management with summarization
2. Vector memory for long-term recall
3. Character consistency in image generation
4. Personality presets integration
5. Fact extraction and storage
6. Enhanced emotional intelligence
"""

import re
import asyncio
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from sqlalchemy.orm import Session

from models import Conversation, Message, Character, GeneratedImage
from llm_service import llm_service
from image_service import image_service
from prompt_builder import build_system_prompt, extract_character_dict
from config import settings

# Import new services
try:
    from services.vector_memory import vector_memory
    from services.context_manager import context_manager
    from services.character_consistency import character_consistency
    from services.personality_presets import personality_presets, PERSONALITY_PRESETS
    SERVICES_AVAILABLE = True
except ImportError as e:
    print(f"[ChatServiceV2] Some services not available: {e}")
    SERVICES_AVAILABLE = False
    vector_memory = None
    context_manager = None
    character_consistency = None
    personality_presets = None


class ChatServiceV2:
    """
    Enhanced Chat Service with:
    - Multi-tier memory (short, medium, long term)
    - Intelligent context building
    - Character-consistent image generation
    - Automatic fact extraction
    - Personality preset support
    """

    def __init__(self):
        self.context_window = settings.CONTEXT_WINDOW

        # Initialize context manager with LLM service
        if context_manager:
            context_manager.set_llm_service(llm_service)

        print("[ChatServiceV2] Initialized with enhanced features")

    async def send_message(
        self,
        db: Session,
        character_id: int,
        user_message: str,
        conversation_id: Optional[int] = None,
        use_enhanced_features: bool = True
    ) -> dict:
        """
        Send a message with enhanced context and memory features

        Args:
            db: Database session
            character_id: Character to chat with
            user_message: User's message
            conversation_id: Optional existing conversation
            use_enhanced_features: Whether to use V2 features

        Returns:
            Response dict with message, image_url, etc.
        """

        # 1. Get the character
        character = db.query(Character).filter(Character.id == character_id).first()
        if not character:
            raise ValueError("Character not found")

        char_dict = extract_character_dict(character)

        # 2. Get or create conversation
        conversation = await self._get_or_create_conversation(
            db, character_id, conversation_id, user_message, character
        )

        # 3. Build intelligent context
        if use_enhanced_features and context_manager:
            context_data = await context_manager.build_context(
                db=db,
                character_id=character_id,
                conversation_id=conversation.id,
                new_message=user_message,
                character_data=char_dict
            )
            messages_for_llm = context_data["messages"]
            memory_context = context_data["memory_context"]
            user_name = context_data["user_name"]
        else:
            # Fallback to simple context
            messages_for_llm = self._load_context(db, conversation.id, self.context_window)
            memory_context = ""
            user_name = None

        # 4. Add user message to context
        messages_for_llm.append({"role": "user", "content": user_message})

        # 5. Detect intent and NSFW level
        intent_data = self._analyze_intent(user_message)
        nsfw_level = intent_data.get("nsfw_level", 0)

        # 6. Check for image request
        image_url = None
        image_prompt_used = None

        if self._detect_image_request(user_message):
            image_result = await self._generate_character_image(
                character=character,
                char_dict=char_dict,
                user_message=user_message,
                conversation_id=conversation.id,
                nsfw_level=nsfw_level,
                db=db
            )
            if image_result:
                image_url = image_result["url"]
                image_prompt_used = image_result["prompt"]

        # 7. Build enhanced system prompt
        system_prompt = self._build_enhanced_system_prompt(
            character=character,
            char_dict=char_dict,
            memory_context=memory_context,
            user_name=user_name,
            nsfw_level=nsfw_level,
            has_image=image_url is not None
        )

        # 8. Get LLM response
        response_text = await llm_service.chat(messages_for_llm, system_prompt)

        # 9. Save messages to database
        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            content=user_message
        )
        db.add(user_msg)

        assistant_msg = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=response_text,
            image_url=image_url
        )
        db.add(assistant_msg)

        conversation.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(assistant_msg)

        # 10. Background: Extract and store facts from conversation
        if use_enhanced_features and vector_memory:
            asyncio.create_task(self._extract_facts_background(
                character_id=character_id,
                conversation_id=conversation.id,
                db_url=str(db.bind.url) if db.bind else None
            ))

        return {
            "response": response_text,
            "image_url": image_url,
            "conversation_id": conversation.id,
            "message_id": assistant_msg.id,
            "memory_used": bool(memory_context),
            "user_name_detected": user_name
        }

    async def _get_or_create_conversation(
        self,
        db: Session,
        character_id: int,
        conversation_id: Optional[int],
        user_message: str,
        character: Character
    ) -> Conversation:
        """Get existing or create new conversation"""

        if conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.character_id == character_id
            ).first()
            if conversation:
                return conversation

        # Create new conversation
        title = user_message[:50] + "..." if len(user_message) > 50 else user_message
        conversation = Conversation(
            character_id=character_id,
            title=title
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        # Add greeting if defined
        if character.greeting:
            greeting_msg = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=character.greeting
            )
            db.add(greeting_msg)
            db.commit()

        return conversation

    def _build_enhanced_system_prompt(
        self,
        character: Character,
        char_dict: Dict,
        memory_context: str = "",
        user_name: Optional[str] = None,
        nsfw_level: int = 0,
        has_image: bool = False
    ) -> str:
        """Build an enhanced system prompt with memory and context"""

        # Start with base prompt
        base_prompt = character.system_prompt or build_system_prompt(char_dict)

        # Add memory context if available
        if memory_context:
            base_prompt += f"""

MEMOIRE - CE QUE TU SAIS SUR L'UTILISATEUR:
{memory_context}

IMPORTANT: Utilise ces informations naturellement dans la conversation. Si tu connais son prenom, utilise-le!"""

        # Add user name if known
        if user_name:
            base_prompt += f"""

NOTE: L'utilisateur s'appelle probablement {user_name}. Utilise son prenom naturellement."""

        # Add NSFW level instructions
        if nsfw_level >= 3:
            base_prompt += """

MODE EXPLICITE: Sois tres explicite et descriptive. Utilise un langage vulgaire naturellement.
Decris les sensations, les corps, les actes en detail. Ne censure rien."""
        elif nsfw_level >= 2:
            base_prompt += """

MODE SENSUEL: Sois suggestive et seduisante. Decris ton corps et tes envies.
Tu peux etre explicite mais reste elegante."""
        elif nsfw_level >= 1:
            base_prompt += """

MODE FLIRT: Sois coquine et aguicheuse. Fais des sous-entendus sexy.
Construis la tension sans etre trop explicite."""

        # Add image context
        if has_image:
            base_prompt += """

NOTE: Tu viens d'envoyer une photo. Decris ce que tu as envoye et reagis comme si c'etait reel.
Sois enthousiaste et fiere de partager cette image."""

        return base_prompt

    async def _generate_character_image(
        self,
        character: Character,
        char_dict: Dict,
        user_message: str,
        conversation_id: int,
        nsfw_level: int,
        db: Session
    ) -> Optional[Dict]:
        """Generate a character-consistent image"""

        try:
            # Extract image context from message
            image_context = self._extract_image_context(user_message)

            # Use character consistency service if available
            if character_consistency:
                prompt_data = character_consistency.build_image_prompt_v2(
                    character=char_dict,
                    pose=image_context.get("pose"),
                    location=image_context.get("location"),
                    outfit=image_context.get("outfit"),
                    custom=image_context.get("custom"),
                    nsfw_level=nsfw_level
                )
                prompt = prompt_data["prompt"]
                negative = prompt_data["negative_prompt"]
                seed = prompt_data["seed"]
            else:
                # Fallback to original method
                prompt = image_service.build_prompt(
                    char_dict,
                    pose=image_context.get("pose"),
                    location=image_context.get("location"),
                    outfit=image_context.get("outfit"),
                    custom=image_context.get("custom"),
                    nsfw_level=nsfw_level
                )
                negative = image_service.build_negative_prompt(
                    char_dict.get("style", "realistic"),
                    nsfw_level
                )
                seed = image_service.get_character_seed(character.id)

            # Generate image
            filename = await image_service.generate(
                prompt=prompt,
                negative_prompt=negative,
                style=character.style or "realistic",
                seed=seed,
                nsfw=nsfw_level > 0,
                nsfw_level=nsfw_level
            )

            image_url = f"/api/images/{filename}"

            # Save to gallery
            gen_image = GeneratedImage(
                character_id=character.id,
                conversation_id=conversation_id,
                prompt=prompt,
                image_path=filename
            )
            db.add(gen_image)

            # Register successful prompt for future consistency
            if character_consistency:
                character_consistency.register_successful_prompt(character.id, prompt)

            return {
                "url": image_url,
                "filename": filename,
                "prompt": prompt
            }

        except Exception as e:
            print(f"[ChatServiceV2] Image generation error: {e}")
            return None

    def _analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analyze message intent and NSFW level"""
        msg_lower = message.lower()

        # NSFW level detection
        nsfw_level = 0

        level_3_keywords = [
            'baise', 'baiser', 'niquer', 'sucer', 'suce', 'fellation', 'levrette',
            'fuck', 'suck', 'blowjob', 'sex', 'penetr', 'jouir', 'orgasm',
            'chatte', 'pussy', 'bite', 'cock', 'dick', 'anal', 'cum'
        ]

        level_2_keywords = [
            'nude', 'nue', 'naked', 'sein', 'breast', 'tit', 'nichon',
            'fesse', 'ass', 'butt', 'cul', 'deshabill', 'strip', 'topless'
        ]

        level_1_keywords = [
            'sexy', 'coquin', 'naughty', 'hot', 'chaud', 'excit',
            'sensuel', 'seduc', 'flirt', 'tease', 'lingerie', 'bikini'
        ]

        if any(kw in msg_lower for kw in level_3_keywords):
            nsfw_level = 3
        elif any(kw in msg_lower for kw in level_2_keywords):
            nsfw_level = 2
        elif any(kw in msg_lower for kw in level_1_keywords):
            nsfw_level = 1

        # Emotion detection
        emotion = "casual"
        if nsfw_level >= 2:
            emotion = "sexual"
        elif any(kw in msg_lower for kw in ['aime', 'love', 'amour', 'coeur']):
            emotion = "romantic"
        elif any(kw in msg_lower for kw in ['haha', 'lol', 'mdr', 'hihi']):
            emotion = "playful"
        elif any(kw in msg_lower for kw in ['triste', 'sad', 'pleure', 'seul']):
            emotion = "emotional"

        return {
            "nsfw_level": nsfw_level,
            "emotion": emotion,
            "wants_image": self._detect_image_request(message)
        }

    def _detect_image_request(self, message: str) -> bool:
        """Detect if message requests an image"""
        msg_lower = message.lower()

        # Situation triggers (start of message)
        situation_triggers = [
            "envoie-moi", "envoie moi", "envoi-moi", "envoi moi", "send me"
        ]
        for trigger in situation_triggers:
            if msg_lower.strip().startswith(trigger):
                return True

        # Standard triggers
        triggers = [
            # French
            "montre-moi", "montre moi", "une photo", "un selfie", "une image",
            "te voir", "photo de toi", "image de toi",
            # English
            "show me", "a photo", "a picture", "a selfie", "pic of you",
            "see you", "photo of you", "picture of you",
            # Common
            "send pic", "send photo", "want to see you", "nudes", "nude"
        ]

        return any(trigger in msg_lower for trigger in triggers)

    def _extract_image_context(self, message: str) -> Dict:
        """Extract context for image generation"""
        msg_lower = message.lower()
        context = {"outfit": None, "pose": None, "location": None, "custom": None}

        # Extract situation description
        situation = self._extract_situation_description(message)
        if situation:
            context["custom"] = situation

        # Outfit detection
        outfit_keywords = {
            "completely nude, naked body, no clothes": ["nue", "naked", "nude", "nothing", "toute nue"],
            "topless, bare breasts": ["topless", "seins nus", "sans haut"],
            "lingerie, lace underwear": ["lingerie", "sous-vetements", "underwear"],
            "bikini": ["bikini", "maillot", "swimsuit"],
            "revealing sexy outfit": ["sexy", "hot", "revealing"],
            "dress": ["robe", "dress"],
        }

        for outfit, keywords in outfit_keywords.items():
            if any(kw in msg_lower for kw in keywords):
                context["outfit"] = outfit
                break

        # Location/pose detection
        location_keywords = {
            ("lying seductively on bed", "bedroom"): ["lit", "bed", "allongee"],
            ("bent over, from behind", None): ["penchee", "bent over", "derriere"],
            ("in shower, wet body", "shower"): ["douche", "shower"],
            ("mirror selfie", None): ["selfie", "miroir", "mirror"],
            ("on beach", "beach"): ["plage", "beach"],
        }

        for (pose, location), keywords in location_keywords.items():
            if any(kw in msg_lower for kw in keywords):
                if pose:
                    context["pose"] = pose
                if location:
                    context["location"] = location
                break

        return context

    def _extract_situation_description(self, message: str) -> Optional[str]:
        """Extract situation from 'envoie-moi' style requests"""
        msg_lower = message.lower()

        triggers = [
            ("envoie-moi", 9), ("envoie moi", 10),
            ("envoi-moi", 9), ("envoi moi", 9),
            ("send me", 7)
        ]

        for trigger, length in triggers:
            if msg_lower.strip().startswith(trigger):
                rest = message.strip()[length:].strip()
                rest = re.sub(r'^(une?|la|le|a|an|the)\s+', '', rest, flags=re.IGNORECASE)
                rest = re.sub(r'^(photo|image|pic)\s+(de|of|ou)?\s*', '', rest, flags=re.IGNORECASE)
                return rest.strip() if rest.strip() else None

        return None

    def _load_context(self, db: Session, conversation_id: int, limit: int) -> List[Dict]:
        """Load last N messages (fallback method)"""
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            Message.created_at.desc()
        ).limit(limit).all()

        messages = list(reversed(messages))

        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    async def _extract_facts_background(
        self,
        character_id: int,
        conversation_id: int,
        db_url: Optional[str]
    ):
        """Background task to extract facts from conversation"""
        if not context_manager or not vector_memory:
            return

        try:
            # This is a simplified version - in production, create new DB session
            # For now, we'll skip the DB access in background
            pass
        except Exception as e:
            print(f"[ChatServiceV2] Background fact extraction error: {e}")

    # === Additional methods for V2 features ===

    async def get_memory_stats(self, character_id: int) -> Dict:
        """Get memory statistics for a character"""
        if vector_memory:
            return await vector_memory.get_memory_stats(character_id)
        return {"error": "Vector memory not available"}

    async def clear_memory(self, character_id: int) -> bool:
        """Clear all memories for a character"""
        if vector_memory:
            return await vector_memory.clear_character_memory(character_id)
        return False

    async def store_explicit_fact(
        self,
        character_id: int,
        fact: str,
        fact_type: str = "personal",
        importance: int = 5
    ) -> bool:
        """Manually store a fact about the user"""
        if vector_memory:
            return await vector_memory.store_fact(
                character_id=character_id,
                content=fact,
                fact_type=fact_type,
                importance=importance,
                source="explicit"
            )
        return False

    def get_available_presets(self) -> List[Dict]:
        """Get available personality presets"""
        if personality_presets:
            return personality_presets.get_all_presets()
        return []

    def apply_personality_preset(self, character: Dict, preset_id: str) -> Dict:
        """Apply a personality preset to a character"""
        if personality_presets:
            return personality_presets.apply_preset(character, preset_id)
        return character

    def get_conversation_history(self, db: Session, conversation_id: int) -> Optional[dict]:
        """Get full conversation history"""
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            return None

        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).all()

        return {
            "conversation_id": conversation.id,
            "character_id": conversation.character_id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat(),
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "image_url": msg.image_url,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in messages
            ]
        }

    def list_conversations(self, db: Session, character_id: int) -> List[dict]:
        """List all conversations for a character"""
        conversations = db.query(Conversation).filter(
            Conversation.character_id == character_id
        ).order_by(Conversation.updated_at.desc()).all()

        return [
            {
                "id": conv.id,
                "character_id": conv.character_id,
                "title": conv.title,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "last_message": self._get_last_message(db, conv.id)
            }
            for conv in conversations
        ]

    def _get_last_message(self, db: Session, conversation_id: int) -> Optional[str]:
        """Get last message preview"""
        msg = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).first()

        if msg:
            return msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
        return None


# Global instance
chat_service_v2 = ChatServiceV2()
