"""Chat Service with Context Management"""
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from models import Conversation, Message, Character, GeneratedImage
from llm_service import llm_service
from image_service import image_service
from prompt_builder import build_system_prompt, extract_character_dict
from config import settings


class ChatService:
    def __init__(self):
        self.context_window = settings.CONTEXT_WINDOW

    async def send_message(
        self,
        db: Session,
        character_id: int,
        user_message: str,
        conversation_id: Optional[int] = None
    ) -> dict:
        """Send a message and handle all context"""

        # 1. Get the character
        character = db.query(Character).filter(Character.id == character_id).first()
        if not character:
            raise ValueError("Character not found")

        # 2. Get or create conversation
        if conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.character_id == character_id
            ).first()
            if not conversation:
                raise ValueError("Conversation not found")
        else:
            # New conversation
            conversation = Conversation(
                character_id=character_id,
                title=user_message[:50] + "..." if len(user_message) > 50 else user_message
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

            # Add greeting as first message if defined
            if character.greeting:
                greeting_msg = Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=character.greeting
                )
                db.add(greeting_msg)
                db.commit()

        # 3. Load conversation history (last N messages)
        history = self._load_context(db, conversation.id, self.context_window)

        # 4. Process roleplay actions (text in quotes)
        roleplay_actions = self._extract_roleplay_actions(user_message)

        # Build message for LLM - include roleplay context
        message_for_llm = user_message
        if roleplay_actions:
            # Format roleplay actions as narrative context
            actions_text = " ".join([f"*{action}*" for action in roleplay_actions])
            # Keep original message but ensure LLM understands the roleplay
            message_for_llm = user_message

        messages_for_llm = history + [{"role": "user", "content": message_for_llm}]

        # 5. Detect if this is an image request
        image_url = None
        if self._detect_image_request(user_message):
            # Generate an image
            image_context = self._extract_image_context(user_message)
            char_dict = extract_character_dict(character)
            prompt = image_service.build_prompt(
                char_dict,
                pose=image_context.get("pose"),
                location=image_context.get("location"),
                outfit=image_context.get("outfit"),
                custom=image_context.get("custom")
            )

            try:
                # Use consistent seed for this character
                character_seed = image_service.get_character_seed(character_id)
                filename = await image_service.generate(
                    prompt=prompt,
                    style=character.style or "realistic",
                    seed=character_seed
                )
                image_url = f"/api/images/{filename}"

                # Save to gallery
                gen_image = GeneratedImage(
                    character_id=character_id,
                    conversation_id=conversation.id,
                    prompt=prompt,
                    image_path=filename
                )
                db.add(gen_image)
            except Exception as e:
                print(f"Image generation error: {e}")

        # 6. Get LLM response
        system_prompt = character.system_prompt or build_system_prompt(extract_character_dict(character))
        response_text = await llm_service.chat(messages_for_llm, system_prompt)

        # 7. Save messages to database
        # User message
        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            content=user_message
        )
        db.add(user_msg)

        # Assistant message (with image if generated)
        assistant_msg = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=response_text,
            image_url=image_url
        )
        db.add(assistant_msg)

        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(assistant_msg)

        return {
            "response": response_text,
            "image_url": image_url,
            "conversation_id": conversation.id,
            "message_id": assistant_msg.id
        }

    def _load_context(self, db: Session, conversation_id: int, limit: int) -> List[Dict]:
        """Load last N messages from a conversation"""
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            Message.created_at.desc()
        ).limit(limit).all()

        # Reverse for chronological order
        messages = list(reversed(messages))

        # Convert to LLM format
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

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
        """Get the last message from a conversation"""
        msg = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).first()

        if msg:
            content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            return content
        return None

    def _extract_roleplay_actions(self, message: str) -> list:
        """Extract roleplay actions from text between quotes"""
        # Match text between different quote styles: "text", «text», "text"
        patterns = [
            r'"([^"]+)"',      # "text"
            r'«([^»]+)»',      # «text»
            r'"([^"]+)"',      # "text" (curly quotes)
            r'\*([^*]+)\*',    # *text* (asterisk style roleplay)
        ]

        actions = []
        for pattern in patterns:
            matches = re.findall(pattern, message)
            actions.extend(matches)

        return actions

    def _detect_image_request(self, message: str) -> bool:
        """Detect if message is requesting an image"""
        message_lower = message.lower()

        # Check for "envoie-moi" at the start (situation image request)
        situation_triggers = [
            "envoie-moi", "envoie moi", "envoi-moi", "envoi moi",
            "send me"
        ]

        # If message starts with situation trigger, it's an image request
        for trigger in situation_triggers:
            if message_lower.strip().startswith(trigger):
                return True

        # Standard image request triggers
        triggers = [
            # French
            "montre-moi", "montre moi",
            "une photo", "un selfie", "une image", "te voir",
            "photo de toi", "pic de toi", "image de toi",
            # English
            "show me", "a photo", "a picture", "a selfie",
            "pic of you", "see you", "nudes", "nude", "photo of you",
            "picture of you", "image of you",
            # Common requests
            "send pic", "send photo", "want to see you", "wanna see you"
        ]
        return any(trigger in message_lower for trigger in triggers)

    def _extract_situation_description(self, message: str) -> Optional[str]:
        """Extract situation description from message starting with 'envoie-moi'"""
        message_lower = message.lower()

        situation_triggers = [
            ("envoie-moi", 9), ("envoie moi", 10),
            ("envoi-moi", 9), ("envoi moi", 9),
            ("send me", 7)
        ]

        for trigger, length in situation_triggers:
            if message_lower.strip().startswith(trigger):
                # Extract what comes after the trigger
                rest = message.strip()[length:].strip()
                # Remove common articles/words
                rest = re.sub(r'^(une?|la|le|les|a|an|the)\s+', '', rest, flags=re.IGNORECASE)
                rest = re.sub(r'^(photo|image|pic|picture)\s+(de|of|où|where)?\s*', '', rest, flags=re.IGNORECASE)
                return rest.strip() if rest.strip() else None

        return None

    def _extract_image_context(self, message: str) -> dict:
        """Extract context for image generation from message"""
        message_lower = message.lower()
        context = {"outfit": None, "pose": None, "location": None, "custom": None}

        # First check for situation description (envoie-moi style)
        situation = self._extract_situation_description(message)
        if situation:
            context["custom"] = situation

        # Outfit detection - prioritize explicit NSFW
        outfit_keywords = {
            "completely nude, naked body, no clothes": ["nue", "naked", "nude", "nothing", "rien", "toute nue", "sans vetement", "déshabillée"],
            "topless, bare breasts": ["topless", "seins nus", "sans haut", "poitrine nue"],
            "lingerie, lace underwear": ["lingerie", "sous-vêtements", "underwear", "bra", "panties", "string", "culotte"],
            "bikini": ["bikini", "maillot", "swimsuit", "swimwear"],
            "revealing sexy outfit": ["sexy", "hot", "revealing", "provocante", "aguicheuse"],
            "dress": ["robe", "dress"],
            "casual": ["casual", "decontracte", "normal"],
        }

        for outfit, keywords in outfit_keywords.items():
            if any(kw in message_lower for kw in keywords):
                context["outfit"] = outfit
                break

        # Location/pose detection - more explicit poses
        location_keywords = {
            ("lying seductively on bed, legs spread", "bedroom"): ["lit", "bed", "allongée", "lying", "couche", "ecarte"],
            ("bent over, from behind", None): ["penchée", "bent over", "from behind", "derriere"],
            ("on all fours", "bedroom"): ["a quatre pattes", "on all fours", "doggy"],
            ("in shower, wet body", "shower"): ["douche", "shower", "mouillée"],
            ("mirror selfie", None): ["selfie", "miroir", "mirror"],
            ("sitting with legs open", "couch"): ["canapé", "couch", "assise", "sitting", "jambes"],
            ("standing provocatively", "bedroom"): ["debout", "standing"],
            ("in kitchen", "kitchen"): ["cuisine", "kitchen"],
            ("on beach", "beach"): ["plage", "beach", "dehors", "outside"],
        }

        for (pose, location), keywords in location_keywords.items():
            if any(kw in message_lower for kw in keywords):
                if pose:
                    context["pose"] = pose
                if location:
                    context["location"] = location
                break

        return context


# Global instance
chat_service = ChatService()
