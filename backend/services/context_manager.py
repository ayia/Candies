"""
Intelligent Context Manager
Inspired by Candy.ai and Character.AI memory systems

This service provides:
1. Multi-tier context building (summary + recent + memories)
2. Automatic conversation summarization
3. Token budget management
4. Seamless integration with vector memory
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

try:
    from .vector_memory import vector_memory, MemoryFact
except ImportError:
    vector_memory = None


class ContextManager:
    """
    Intelligent context manager that builds optimal context for LLM calls

    Context Structure:
    1. [MEMORY] - Relevant long-term memories from vector DB
    2. [SUMMARY] - Summary of older conversation (if > 20 messages)
    3. [RECENT] - Last N messages verbatim

    This approach maximizes information while minimizing token usage
    """

    # Configuration
    MAX_RECENT_MESSAGES = 10        # Messages to keep verbatim
    SUMMARY_THRESHOLD = 20          # Start summarizing after this many messages
    MAX_SUMMARY_INPUT = 30          # Max messages to include in summary
    MAX_CONTEXT_TOKENS = 3000       # Approximate token budget

    def __init__(self, llm_service=None):
        """
        Initialize context manager

        Args:
            llm_service: Optional LLM service for summarization
        """
        self.llm_service = llm_service
        self._summary_cache: Dict[int, Tuple[str, int]] = {}  # conv_id -> (summary, msg_count)
        print("[ContextManager] Initialized")

    def set_llm_service(self, llm_service):
        """Set the LLM service for summarization"""
        self.llm_service = llm_service

    async def build_context(
        self,
        db: Session,
        character_id: int,
        conversation_id: int,
        new_message: str,
        character_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Build optimized context for an LLM call

        Returns:
            Dict containing:
            - messages: List of messages for LLM
            - memory_context: String of relevant memories
            - has_summary: Whether a summary was included
            - total_messages: Total messages in conversation
        """
        from models import Message, Conversation

        # Load all messages
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).all()

        total_messages = len(messages)
        result = {
            "messages": [],
            "memory_context": "",
            "has_summary": False,
            "total_messages": total_messages,
            "user_name": None
        }

        # 1. Get memory context (parallel with other operations)
        memory_task = None
        if vector_memory:
            memory_task = asyncio.create_task(
                self._get_memory_context(character_id, new_message)
            )

        # 2. Build message context
        if total_messages <= self.MAX_RECENT_MESSAGES:
            # Few messages - include all
            result["messages"] = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
        elif total_messages <= self.SUMMARY_THRESHOLD:
            # Medium amount - include recent
            recent = messages[-self.MAX_RECENT_MESSAGES:]
            result["messages"] = [
                {"role": msg.role, "content": msg.content}
                for msg in recent
            ]
        else:
            # Many messages - summarize old + recent
            old_messages = messages[:-self.MAX_RECENT_MESSAGES]
            recent_messages = messages[-self.MAX_RECENT_MESSAGES:]

            # Get or create summary
            summary = await self._get_or_create_summary(
                conversation_id,
                old_messages,
                total_messages
            )

            if summary:
                result["has_summary"] = True
                # Add summary as system context
                result["messages"].append({
                    "role": "system",
                    "content": f"[RESUME DE LA CONVERSATION PRECEDENTE]\n{summary}"
                })

            # Add recent messages
            result["messages"].extend([
                {"role": msg.role, "content": msg.content}
                for msg in recent_messages
            ])

        # 3. Wait for memory context
        if memory_task:
            memory_result = await memory_task
            result["memory_context"] = memory_result.get("context", "")
            result["user_name"] = memory_result.get("user_name")

        return result

    async def _get_memory_context(
        self,
        character_id: int,
        query: str
    ) -> Dict[str, Any]:
        """Get relevant memory context from vector memory"""
        if not vector_memory:
            return {"context": "", "user_name": None}

        try:
            # Get context string and user name in parallel
            context_task = vector_memory.build_context_string(
                character_id, query, max_facts=7
            )
            name_task = vector_memory.get_user_name(character_id)

            context, user_name = await asyncio.gather(context_task, name_task)

            return {
                "context": context,
                "user_name": user_name
            }
        except Exception as e:
            print(f"[ContextManager] Memory error: {e}")
            return {"context": "", "user_name": None}

    async def _get_or_create_summary(
        self,
        conversation_id: int,
        old_messages: List,
        total_count: int
    ) -> Optional[str]:
        """Get cached summary or create new one"""
        # Check cache
        cached = self._summary_cache.get(conversation_id)
        if cached:
            cached_summary, cached_count = cached
            # Reuse if we haven't added too many new messages
            if total_count - cached_count < 15:
                return cached_summary

        # Create new summary
        if not self.llm_service:
            return self._create_simple_summary(old_messages)

        summary = await self._create_llm_summary(old_messages)

        # Cache it
        self._summary_cache[conversation_id] = (summary, total_count)

        return summary

    async def _create_llm_summary(self, messages: List) -> str:
        """Create summary using LLM"""
        # Take last N messages for summary
        to_summarize = messages[-self.MAX_SUMMARY_INPUT:]

        conv_text = "\n".join([
            f"{'USER' if msg.role == 'user' else 'AI'}: {msg.content[:300]}"
            for msg in to_summarize
        ])

        summary_prompt = f"""Resume cette conversation en 3-4 phrases.
Focus sur:
- Les informations personnelles partagees (nom, preferences)
- Les moments emotionnels importants
- La progression de la relation
- Les sujets/themes abordes

CONVERSATION:
{conv_text}

RESUME CONCIS:"""

        try:
            summary = await self.llm_service.chat(
                messages=[{"role": "user", "content": summary_prompt}],
                system_prompt="Tu es un assistant qui resume des conversations de maniere concise."
            )
            return summary.strip()
        except Exception as e:
            print(f"[ContextManager] Summary error: {e}")
            return self._create_simple_summary(messages)

    def _create_simple_summary(self, messages: List) -> str:
        """Create a simple summary without LLM"""
        if not messages:
            return ""

        # Extract key info
        user_messages = [m for m in messages if m.role == "user"]
        ai_messages = [m for m in messages if m.role == "assistant"]

        summary_parts = [
            f"La conversation contient {len(messages)} messages.",
        ]

        # Try to extract topics
        keywords = set()
        for msg in messages[-20:]:
            words = msg.content.lower().split()
            # Simple keyword extraction
            for word in words:
                if len(word) > 5 and word.isalpha():
                    keywords.add(word)

        if keywords:
            summary_parts.append(f"Sujets abordes: {', '.join(list(keywords)[:10])}")

        return " ".join(summary_parts)

    async def extract_and_store_facts(
        self,
        character_id: int,
        conversation: List[Dict[str, str]],
        llm_service=None
    ) -> int:
        """
        Extract facts from conversation and store in vector memory

        Returns number of facts stored
        """
        if not vector_memory:
            return 0

        llm = llm_service or self.llm_service
        if not llm:
            # No LLM - use simple extraction
            return await self._simple_fact_extraction(character_id, conversation)

        # Use LLM for intelligent extraction
        return await self._llm_fact_extraction(character_id, conversation, llm)

    async def _llm_fact_extraction(
        self,
        character_id: int,
        conversation: List[Dict[str, str]],
        llm_service
    ) -> int:
        """Extract facts using LLM"""
        # Only analyze recent messages
        recent = conversation[-15:] if len(conversation) > 15 else conversation

        conv_text = "\n".join([
            f"{'USER' if msg['role'] == 'user' else 'AI'}: {msg['content']}"
            for msg in recent
        ])

        extraction_prompt = f"""Analyse cette conversation et extrait les FAITS IMPORTANTS sur l'UTILISATEUR (pas l'IA).

CONVERSATION:
{conv_text}

Extrait les faits dans ce format JSON:
{{
    "facts": [
        {{"type": "personal", "content": "fait sur l'utilisateur", "importance": 5}},
        {{"type": "preference", "content": "ce que l'utilisateur aime", "importance": 4}},
        {{"type": "intimate", "content": "preference intime", "importance": 4}}
    ]
}}

TYPES DE FAITS:
- personal (5): Nom, age, metier, lieu - TOUJOURS extraire
- intimate (5): Preferences sexuelles, fantasmes, limites
- preference (4): Gouts, hobbies, ce qu'il aime/n'aime pas
- emotional (3): Humeur, sentiments exprimes
- event (2): Evenements mentionnes

REGLES:
- Extrais UNIQUEMENT les vrais faits, pas le roleplay
- Le nom de l'utilisateur est PRIORITAIRE
- Sois concis dans les descriptions
- Output JSON uniquement"""

        try:
            response = await llm_service.chat(
                messages=[{"role": "user", "content": extraction_prompt}],
                system_prompt="Tu extrais des faits de conversations. Output JSON uniquement."
            )

            # Parse JSON
            import json
            clean = response.strip()
            if "```" in clean:
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
                clean = clean.strip()

            data = json.loads(clean)
            facts = data.get("facts", [])

            # Store facts
            stored = await vector_memory.store_facts_batch(character_id, facts)
            print(f"[ContextManager] Extracted and stored {stored} facts")
            return stored

        except Exception as e:
            print(f"[ContextManager] Extraction error: {e}")
            return await self._simple_fact_extraction(character_id, conversation)

    async def _simple_fact_extraction(
        self,
        character_id: int,
        conversation: List[Dict[str, str]]
    ) -> int:
        """Simple pattern-based fact extraction"""
        stored = 0

        # Name patterns
        name_patterns = [
            (r"je m'appelle (\w+)", "personal", 5),
            (r"mon nom est (\w+)", "personal", 5),
            (r"my name is (\w+)", "personal", 5),
            (r"i'm (\w+)", "personal", 5),
            (r"call me (\w+)", "personal", 5),
        ]

        # Preference patterns
        pref_patterns = [
            (r"j'aime (.+)", "preference", 4),
            (r"je deteste (.+)", "preference", 4),
            (r"i like (.+)", "preference", 4),
            (r"i love (.+)", "preference", 4),
            (r"i hate (.+)", "preference", 4),
        ]

        import re

        for msg in conversation:
            if msg["role"] != "user":
                continue

            content = msg["content"].lower()

            # Check name patterns
            for pattern, fact_type, importance in name_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    name = match.group(1)
                    success = await vector_memory.store_fact(
                        character_id,
                        f"L'utilisateur s'appelle {name}",
                        fact_type,
                        importance
                    )
                    if success:
                        stored += 1

            # Check preference patterns
            for pattern, fact_type, importance in pref_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    pref = match.group(1)[:100]  # Limit length
                    success = await vector_memory.store_fact(
                        character_id,
                        f"L'utilisateur: {pref}",
                        fact_type,
                        importance
                    )
                    if success:
                        stored += 1

        return stored

    def clear_summary_cache(self, conversation_id: Optional[int] = None):
        """Clear summary cache"""
        if conversation_id:
            self._summary_cache.pop(conversation_id, None)
        else:
            self._summary_cache.clear()

    async def get_context_stats(
        self,
        db: Session,
        character_id: int,
        conversation_id: int
    ) -> Dict[str, Any]:
        """Get statistics about context for debugging"""
        from models import Message

        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).all()

        stats = {
            "total_messages": len(messages),
            "would_summarize": len(messages) > self.SUMMARY_THRESHOLD,
            "recent_window": self.MAX_RECENT_MESSAGES,
            "has_cached_summary": conversation_id in self._summary_cache,
            "memory_stats": {}
        }

        if vector_memory:
            stats["memory_stats"] = await vector_memory.get_memory_stats(character_id)

        return stats


# Global instance
context_manager = ContextManager()
