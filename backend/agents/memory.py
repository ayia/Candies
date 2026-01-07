"""
AGENT: MEMORY (Enhanced)
Purpose: Persistent memory with Redis + intelligent recall
Model: Fast model for summarization and recall
Based on: https://convai.com/blog/long-term-memory---a-technical-overview
"""
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from .base import BaseAgent

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("[MemoryAgent] Redis not installed - using in-memory fallback")


class MemoryAgent(BaseAgent):
    """
    Enhanced Memory Agent with:
    1. Redis persistence for long-term memory
    2. Multi-tier memory (short, medium, long term)
    3. Intelligent context recall with relevance scoring
    4. Character style preservation
    """

    def __init__(self, provider: str, model: str, api_key: str, redis_url: str = "redis://localhost:6379"):
        super().__init__(provider, model, api_key)
        self.redis_client = None
        self.memory_cache: Dict[str, List[Dict]] = {}  # Fallback in-memory

        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                print("[MemoryAgent] Connected to Redis")
            except Exception as e:
                print(f"[MemoryAgent] Redis connection failed: {e} - using in-memory")
                self.redis_client = None

    def get_system_prompt(self) -> str:
        return """You are a memory extraction and recall system for an AI companion.

TASK 1 - EXTRACTION: Extract important facts from conversations.
OUTPUT FORMAT (JSON only):
{
    "facts": [
        {"type": "preference", "content": "user likes X", "importance": 1-5},
        {"type": "personal", "content": "user's name is Y", "importance": 1-5},
        {"type": "intimate", "content": "user's fantasy is Z", "importance": 1-5}
    ],
    "relationship_stage": "stranger" | "acquaintance" | "friend" | "flirty" | "romantic" | "intimate",
    "user_name": "detected name or null",
    "style_sample": "a short phrase showing the conversation style"
}

TASK 2 - RECALL: Given facts and a message, return ONLY relevant context.

FACT TYPES (by importance):
- personal (5): Name, age, job, location - ALWAYS remember
- preference (4): Likes, dislikes, hobbies
- intimate (4): Sexual preferences, fantasies, boundaries
- emotional (3): Feelings, moods expressed
- event (2): Things that happened in conversation
- casual (1): Minor details

RULES:
- Extract REAL information only, not roleplay content
- User's name is HIGH PRIORITY - extract it when mentioned
- Be concise - short fact statements only
- Output valid JSON only"""

    def _get_memory_key(self, character_id: int) -> str:
        """Generate Redis key for character memory"""
        return f"casdy:memory:{character_id}"

    def _get_style_key(self, character_id: int) -> str:
        """Generate Redis key for character style sample"""
        return f"casdy:style:{character_id}"

    async def save_facts(self, character_id: int, facts: List[Dict]) -> None:
        """Save facts to Redis or memory cache"""
        key = self._get_memory_key(character_id)

        # Deduplicate facts by content hash
        existing_facts = await self.load_facts(character_id)
        existing_hashes = {
            hashlib.md5(f.get("content", "").encode()).hexdigest()
            for f in existing_facts
        }

        new_facts = []
        for fact in facts:
            content_hash = hashlib.md5(fact.get("content", "").encode()).hexdigest()
            if content_hash not in existing_hashes:
                fact["timestamp"] = datetime.now(timezone.utc).isoformat()
                new_facts.append(fact)
                existing_hashes.add(content_hash)

        if not new_facts:
            return

        all_facts = existing_facts + new_facts

        # Keep only last 100 facts, prioritize by importance
        all_facts.sort(key=lambda x: (x.get("importance", 3), x.get("timestamp", "")), reverse=True)
        all_facts = all_facts[:100]

        if self.redis_client:
            try:
                self.redis_client.set(key, json.dumps(all_facts), ex=86400 * 30)  # 30 days TTL
            except Exception as e:
                print(f"[MemoryAgent] Redis save error: {e}")
                self.memory_cache[str(character_id)] = all_facts
        else:
            self.memory_cache[str(character_id)] = all_facts

        print(f"[MemoryAgent] Saved {len(new_facts)} new facts for character {character_id}")

    async def load_facts(self, character_id: int) -> List[Dict]:
        """Load facts from Redis or memory cache"""
        key = self._get_memory_key(character_id)

        if self.redis_client:
            try:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                print(f"[MemoryAgent] Redis load error: {e}")

        return self.memory_cache.get(str(character_id), [])

    async def save_style_sample(self, character_id: int, sample: str) -> None:
        """Save a style sample for character consistency"""
        key = self._get_style_key(character_id)

        if self.redis_client:
            try:
                self.redis_client.set(key, sample, ex=86400 * 30)
            except Exception:
                pass
        else:
            self.memory_cache[f"style_{character_id}"] = sample

    async def get_style_sample(self, character_id: int) -> Optional[str]:
        """Get the saved style sample for consistency"""
        key = self._get_style_key(character_id)

        if self.redis_client:
            try:
                return self.redis_client.get(key)
            except Exception:
                pass

        return self.memory_cache.get(f"style_{character_id}")

    async def extract_facts(self, conversation: List[Dict[str, str]]) -> Dict[str, Any]:
        """Extract important facts from a conversation"""
        if len(conversation) < 2:
            return {"facts": [], "relationship_stage": "stranger", "user_name": None}

        # Format conversation for analysis
        conv_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in conversation[-15:]  # Last 15 messages
        ])

        message = f"""CONVERSATION TO ANALYZE:
{conv_text}

Extract important facts about the USER (not the AI character).
Focus on: name, preferences, personal details, intimate preferences.
Output JSON only."""

        response = await self.call(
            message=message,
            temperature=0.1,
            max_tokens=500
        )

        try:
            clean_response = self._clean_json_response(response)
            result = json.loads(clean_response)

            # Ensure facts have importance scores
            for fact in result.get("facts", []):
                if "importance" not in fact:
                    type_importance = {
                        "personal": 5, "intimate": 4, "preference": 4,
                        "emotional": 3, "event": 2, "casual": 1
                    }
                    fact["importance"] = type_importance.get(fact.get("type", "casual"), 2)

            return result
        except json.JSONDecodeError:
            return {"facts": [], "relationship_stage": "unknown", "user_name": None}

    async def get_relevant_context(
        self,
        character_id: int,
        new_message: str,
        limit: int = 5
    ) -> str:
        """Get relevant context for a new message"""
        stored_facts = await self.load_facts(character_id)

        if not stored_facts:
            return ""

        # Get high-importance facts first
        sorted_facts = sorted(
            stored_facts,
            key=lambda x: x.get("importance", 3),
            reverse=True
        )[:20]

        facts_text = "\n".join([
            f"- [{f.get('type', 'fact')}] {f.get('content', '')}"
            for f in sorted_facts
        ])

        message = f"""STORED FACTS ABOUT USER:
{facts_text}

NEW USER MESSAGE: {new_message}

Which facts are relevant? Return a brief context summary (2-3 sentences max).
If user's name is known, always include it.
If no facts are relevant, respond with exactly: NONE"""

        response = await self.call(
            message=message,
            temperature=0.1,
            max_tokens=100
        )

        if "NONE" in response.upper() or len(response.strip()) < 5:
            # Still return user name if known
            for fact in stored_facts:
                if fact.get("type") == "personal" and "name" in fact.get("content", "").lower():
                    return f"Remember: {fact.get('content')}"
            return ""

        return response.strip()

    async def get_user_name(self, character_id: int) -> Optional[str]:
        """Get the user's name if known"""
        facts = await self.load_facts(character_id)

        for fact in facts:
            if fact.get("type") == "personal":
                content = fact.get("content", "").lower()
                if "name is" in content or "s'appelle" in content or "called" in content:
                    # Extract name from fact
                    return fact.get("content")

        return None

    async def get_relationship_level(self, character_id: int) -> int:
        """
        Get the relationship level (0-10) for a character.
        This is estimated from stored facts and relationship stage.
        """
        # Try to get from Redis first
        key = f"casdy:relationship:{character_id}"
        if self.redis_client:
            try:
                level = self.redis_client.get(key)
                if level:
                    return int(level)
            except Exception:
                pass

        # Estimate from facts
        facts = await self.load_facts(character_id)
        if not facts:
            return 0

        # Check for relationship stage in facts
        stage_levels = {
            "stranger": 0,
            "acquaintance": 1,
            "casual_friend": 2,
            "friend": 3,
            "close_friend": 4,
            "special_friend": 5,
            "romantic_interest": 6,
            "flirty": 6,
            "dating": 7,
            "romantic": 7,
            "intimate": 8,
            "lover": 9,
            "soulmate": 10
        }

        # Estimate based on fact types and count
        intimate_facts = sum(1 for f in facts if f.get("type") == "intimate")
        personal_facts = sum(1 for f in facts if f.get("type") == "personal")
        total_facts = len(facts)

        # Base level on facts
        estimated_level = 0
        if total_facts > 0:
            estimated_level = min(3, total_facts // 5)  # 1 level per 5 facts, max 3
        if personal_facts > 2:
            estimated_level = max(estimated_level, 3)
        if intimate_facts > 0:
            estimated_level = max(estimated_level, 5 + min(intimate_facts, 5))

        return min(10, estimated_level)

    async def save_relationship_level(self, character_id: int, level: int) -> None:
        """Save the relationship level for a character"""
        key = f"casdy:relationship:{character_id}"
        if self.redis_client:
            try:
                self.redis_client.set(key, str(level), ex=86400 * 30)  # 30 days TTL
            except Exception:
                pass

    async def summarize_for_context(
        self,
        conversation: List[Dict[str, str]],
        max_messages: int = 10
    ) -> str:
        """Create a compressed summary for context window management"""
        if len(conversation) <= max_messages:
            return ""

        # Summarize older messages
        old_messages = conversation[:-max_messages]
        conv_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content'][:150]}"
            for msg in old_messages[-20:]
        ])

        message = f"""EARLIER CONVERSATION:
{conv_text}

Summarize what happened in 2-3 sentences. Focus on:
- Key emotional moments
- Important revelations
- Relationship progression"""

        response = await self.call(
            message=message,
            temperature=0.2,
            max_tokens=150
        )

        return response.strip()

    def _clean_json_response(self, response: str) -> str:
        """Clean LLM response to extract JSON"""
        clean = response.strip()
        if clean.startswith("```"):
            parts = clean.split("```")
            if len(parts) >= 2:
                clean = parts[1]
                if clean.startswith("json"):
                    clean = clean[4:]
        return clean.strip()
