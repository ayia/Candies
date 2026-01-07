"""
Chat Service V3 - Service de chat avec progression relationnelle immersive

Integre:
- RelationshipManager: Progression par niveaux (0-10)
- EmotionalStateTracker: Tracking d'humeur du personnage
- Contexte dynamique adapte au niveau de relation
- Generation de prompts contextualises
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from models import Character, Conversation, Message
from llm_service import llm_service
from prompt_builder import build_system_prompt, extract_character_dict, generate_greeting_for_level
from services.relationship_manager import relationship_manager
from services.emotional_state import emotional_tracker


class ChatServiceV3:
    """Service de chat avec progression relationnelle"""

    def __init__(self):
        self.relationship_manager = relationship_manager
        self.emotional_tracker = emotional_tracker
        print("[ChatServiceV3] Initialized with relationship progression")

    async def send_message(
        self,
        db: Session,
        character_id: int,
        user_message: str,
        conversation_id: Optional[int] = None,
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Envoie un message et genere une reponse contextuelle.

        Le systeme:
        1. Analyse le message utilisateur pour ajuster l'affinite
        2. Met a jour l'etat emotionnel du personnage
        3. Genere un prompt systeme adapte au niveau de relation
        4. Genere une reponse appropriee
        """

        # Get character
        character = db.query(Character).filter(Character.id == character_id).first()
        if not character:
            raise ValueError(f"Character {character_id} not found")

        # 1. Process relationship interaction
        relationship_result = self.relationship_manager.process_interaction(
            character_id=character_id,
            user_message=user_message,
            user_id=user_id
        )

        # 2. Update emotional state
        emotional_result = self.emotional_tracker.analyze_and_update(
            character_id=character_id,
            user_message=user_message,
            relationship_level=relationship_result["level"]
        )

        # 3. Get or create conversation
        if conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
        else:
            # Create new conversation
            conversation = Conversation(
                character_id=character_id,
                title=f"Conversation niveau {relationship_result['level']}"
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

            # Add greeting message for new conversation
            greeting = generate_greeting_for_level(
                extract_character_dict(character),
                level=relationship_result["level"]
            )
            greeting_msg = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=greeting
            )
            db.add(greeting_msg)
            db.commit()

        # 4. Save user message
        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            content=user_message
        )
        db.add(user_msg)
        db.commit()

        # 5. Build context-aware system prompt
        char_dict = extract_character_dict(character)
        relationship_context = self.relationship_manager.get_prompt_context(character_id, user_id)
        emotional_context = self.emotional_tracker.get_mood_context(character_id)

        system_prompt = build_system_prompt(
            character=char_dict,
            relationship_context=relationship_context,
            emotional_context=emotional_context
        )

        # 6. Get conversation history (limited)
        messages = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at.desc()).limit(20).all()

        messages = list(reversed(messages))

        # Build message history for LLM
        chat_messages = []
        for msg in messages:
            chat_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # 7. Generate response
        response_text = await llm_service.chat(
            messages=chat_messages,
            system_prompt=system_prompt
        )

        # 8. Post-process response based on level
        response_text = self._enforce_level_restrictions(
            response_text,
            relationship_result["level"],
            relationship_result["behavior_guidelines"]
        )

        # 9. Save assistant response
        assistant_msg = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=response_text
        )
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)

        # 10. Check for memorable content to store
        self._extract_and_store_memories(
            character_id=character_id,
            user_message=user_message,
            user_id=user_id
        )

        # Build response
        response = {
            "response": response_text,
            "conversation_id": conversation.id,
            "message_id": assistant_msg.id,
            "image_url": None,
            # Relationship info
            "relationship": {
                "level": relationship_result["level"],
                "stage": relationship_result["stage"],
                "points": relationship_result["state"]["affinity_points"],
                "points_change": relationship_result["points_change"],
                "level_up": relationship_result.get("level_up", False),
                "nsfw_allowed": relationship_result["nsfw_allowed"]
            },
            # Emotional info
            "emotion": {
                "mood": emotional_result["current_mood"],
                "mood_changed": emotional_result["mood_changed"],
                "intensity": emotional_result["mood_intensity"]
            }
        }

        # Add level up notification if applicable
        if relationship_result.get("level_up"):
            response["level_up_message"] = self._get_level_up_message(
                relationship_result["level"],
                character.language or "french"
            )

        return response

    def _enforce_level_restrictions(
        self,
        response: str,
        level: int,
        guidelines: Dict
    ) -> str:
        """
        Verifie et corrige la reponse pour respecter le niveau.
        Remplace les elements inappropries si necessaire.
        """
        import re

        # Terms to restrict by level
        if level < 7:
            # Remove romantic terms
            romantic_terms = [
                r"\bmon amour\b", r"\bmon coeur\b", r"\bma cherie\b",
                r"\bbebe\b", r"\bmy love\b", r"\bdarling\b", r"\bsweetheart\b"
            ]
            for term in romantic_terms:
                response = re.sub(term, "", response, flags=re.IGNORECASE)

        if level < 5:
            # Remove flirty physical contact
            flirty_actions = [
                r"\*t'embrasse\*", r"\*te caresse\*", r"\*se blottit\*",
                r"\*kisses you\*", r"\*caresses\*", r"\*snuggles\*"
            ]
            for action in flirty_actions:
                response = re.sub(action, "*sourit*", response, flags=re.IGNORECASE)

        if level < 8:
            # Remove explicit content
            explicit_patterns = [
                r"\*gemit\*", r"\*moan\*", r"envie de toi",
                r"want you", r"desir", r"excite"
            ]
            for pattern in explicit_patterns:
                response = re.sub(pattern, "", response, flags=re.IGNORECASE)

        # Clean up multiple spaces
        response = re.sub(r'\s+', ' ', response).strip()

        return response

    def _extract_and_store_memories(
        self,
        character_id: int,
        user_message: str,
        user_id: str
    ):
        """Extrait et stocke les informations memorables"""
        import re

        # Detect personal information
        patterns = {
            "name": r"je m'appelle (\w+)|mon nom (?:est|c'est) (\w+)",
            "hobby": r"j'aime (?:bien |beaucoup )?(\w+)|je fais (?:du|de la|de l') (\w+)",
            "job": r"je (?:suis|travaille comme) (\w+)",
            "location": r"j'habite (?:a|en) (\w+)|je vis (?:a|en) (\w+)"
        }

        for memory_type, pattern in patterns.items():
            match = re.search(pattern, user_message.lower())
            if match:
                value = match.group(1) or match.group(2) if match.lastindex > 1 else match.group(1)
                if value:
                    memory = f"{memory_type}: {value}"
                    self.relationship_manager.add_shared_memory(
                        character_id, memory, user_id
                    )

    def _get_level_up_message(self, new_level: int, language: str) -> str:
        """Message de notification de niveau"""
        messages = {
            "french": {
                1: "Vous commencez a vous connaitre...",
                2: "Une complicite se cree entre vous.",
                3: "Vous devenez de vrais amis!",
                4: "Une amitie profonde se developpe.",
                5: "Il y a une connexion speciale entre vous...",
                6: "Les sentiments deviennent plus intenses...",
                7: "Une romance s'installe entre vous.",
                8: "La passion s'eveille...",
                9: "Votre intimite s'approfondit.",
                10: "Vous ne faites plus qu'un."
            },
            "english": {
                1: "You're starting to get to know each other...",
                2: "A bond is forming between you.",
                3: "You're becoming real friends!",
                4: "A deep friendship is developing.",
                5: "There's a special connection between you...",
                6: "Feelings are becoming more intense...",
                7: "Romance is blossoming between you.",
                8: "Passion is awakening...",
                9: "Your intimacy deepens.",
                10: "You've become one."
            }
        }

        lang_messages = messages.get(language, messages["english"])
        return lang_messages.get(new_level, f"Niveau {new_level} atteint!")

    def get_relationship_status(
        self,
        character_id: int,
        user_id: str = "default"
    ) -> Dict:
        """Retourne le statut complet de la relation"""
        from services.relationship_manager import LEVEL_BEHAVIORS
        state = self.relationship_manager.get_state(character_id, user_id)
        behavior = LEVEL_BEHAVIORS.get(state.level, LEVEL_BEHAVIORS[0])
        return {
            "level": state.level,
            "stage": behavior["stage"].value,
            "points": state.affinity_points,
            "total_messages": state.total_messages,
            "user_name": state.user_name,
            "shared_memories": state.shared_memories,
            "nsfw_unlocked": state.level >= 8
        }

    def reset_relationship(
        self,
        character_id: int,
        user_id: str = "default"
    ) -> Dict:
        """Reinitialise la relation"""
        state = self.relationship_manager.reset_relationship(character_id, user_id)
        return {"status": "reset", "new_level": state.level}

    def boost_relationship(
        self,
        character_id: int,
        points: int,
        user_id: str = "default"
    ) -> Dict:
        """Ajoute des points (debug/admin)"""
        state = self.relationship_manager.boost_relationship(character_id, points, user_id)
        return {
            "status": "boosted",
            "new_level": state.level,
            "new_points": state.affinity_points
        }


# Global instance
chat_service_v3 = ChatServiceV3()
