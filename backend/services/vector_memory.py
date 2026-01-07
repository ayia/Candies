"""
Vector Memory Service - Long-term Semantic Memory
Inspired by Candy.ai's memory system and Character.AI's approach

This service provides:
1. Semantic search for relevant memories
2. Multi-tier memory (facts, preferences, intimate details)
3. Automatic fact extraction and deduplication
4. Importance-based recall
"""

import json
import hashlib
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("[VectorMemory] sentence-transformers not installed - using keyword fallback")

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    print("[VectorMemory] chromadb not installed - using in-memory fallback")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


@dataclass
class MemoryFact:
    """A single memory fact with metadata"""
    content: str
    fact_type: str  # personal, preference, intimate, emotional, event
    importance: int  # 1-5
    timestamp: str
    source: str = "conversation"  # conversation, explicit, inferred

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "MemoryFact":
        return cls(**data)


class VectorMemoryService:
    """
    Advanced vector-based memory system with semantic search

    Memory Tiers:
    - Tier 1 (Critical): Name, age, location - always recalled
    - Tier 2 (Important): Preferences, fantasies, relationship details
    - Tier 3 (Context): Events, emotions, casual mentions
    """

    # Embedding model - multilingual for French/English support
    EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

    # Fact type importance weights
    IMPORTANCE_WEIGHTS = {
        "personal": 5,      # Name, age, job, location
        "intimate": 5,      # Sexual preferences, fantasies, boundaries
        "preference": 4,    # Likes, dislikes, hobbies
        "relationship": 4,  # Relationship status, feelings about user
        "emotional": 3,     # Moods, feelings expressed
        "event": 2,         # Things that happened
        "casual": 1         # Minor details
    }

    def __init__(self, redis_url: str = "redis://localhost:6379", persist_dir: str = "./vector_db"):
        self.persist_dir = persist_dir
        self.redis_url = redis_url

        # Initialize embedding model
        self.embedder = None
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embedder = SentenceTransformer(self.EMBEDDING_MODEL)
                print(f"[VectorMemory] Loaded embedding model: {self.EMBEDDING_MODEL}")
            except Exception as e:
                print(f"[VectorMemory] Failed to load embedder: {e}")

        # Initialize ChromaDB for vector storage
        self.chroma_client = None
        self.collections: Dict[int, Any] = {}  # character_id -> collection

        if CHROMA_AVAILABLE:
            try:
                self.chroma_client = chromadb.Client(ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                ))
                print("[VectorMemory] ChromaDB initialized (in-memory mode)")
            except Exception as e:
                print(f"[VectorMemory] ChromaDB init failed: {e}")

        # Redis for fast cache and backup
        self.redis_client = None
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                print("[VectorMemory] Redis connected")
            except Exception as e:
                print(f"[VectorMemory] Redis connection failed: {e}")

        # In-memory fallback
        self.memory_cache: Dict[int, List[MemoryFact]] = {}

        print("[VectorMemory] Service initialized")

    def _get_collection(self, character_id: int):
        """Get or create a ChromaDB collection for a character"""
        if not self.chroma_client:
            return None

        if character_id not in self.collections:
            collection_name = f"character_{character_id}_memory"
            try:
                self.collections[character_id] = self.chroma_client.get_or_create_collection(
                    name=collection_name,
                    metadata={"character_id": character_id}
                )
            except Exception as e:
                print(f"[VectorMemory] Collection creation failed: {e}")
                return None

        return self.collections[character_id]

    def _compute_embedding(self, text: str) -> Optional[List[float]]:
        """Compute embedding for text"""
        if not self.embedder:
            return None

        try:
            embedding = self.embedder.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            print(f"[VectorMemory] Embedding error: {e}")
            return None

    def _hash_content(self, content: str) -> str:
        """Generate hash for deduplication"""
        normalized = content.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()

    async def store_fact(
        self,
        character_id: int,
        content: str,
        fact_type: str = "casual",
        importance: Optional[int] = None,
        source: str = "conversation"
    ) -> bool:
        """
        Store a fact in vector memory

        Args:
            character_id: The character this fact is associated with
            content: The fact content
            fact_type: Type of fact (personal, preference, intimate, etc.)
            importance: Override importance (1-5), or use default for type
            source: Where this fact came from

        Returns:
            True if stored, False if duplicate or error
        """
        # Calculate importance
        if importance is None:
            importance = self.IMPORTANCE_WEIGHTS.get(fact_type, 2)

        # Create fact object
        fact = MemoryFact(
            content=content,
            fact_type=fact_type,
            importance=importance,
            timestamp=datetime.now(timezone.utc).isoformat(),
            source=source
        )

        # Check for duplicates
        content_hash = self._hash_content(content)

        # Try to store in ChromaDB
        collection = self._get_collection(character_id)
        if collection:
            try:
                # Check if exists
                existing = collection.get(ids=[content_hash])
                if existing and existing['ids']:
                    # Update if new importance is higher
                    old_importance = existing['metadatas'][0].get('importance', 0)
                    if importance > old_importance:
                        collection.update(
                            ids=[content_hash],
                            metadatas=[fact.to_dict()]
                        )
                    return False  # Already exists

                # Compute embedding
                embedding = self._compute_embedding(content)

                # Store new fact
                collection.add(
                    ids=[content_hash],
                    embeddings=[embedding] if embedding else None,
                    documents=[content],
                    metadatas=[fact.to_dict()]
                )
                print(f"[VectorMemory] Stored fact for char {character_id}: {content[:50]}...")
                return True

            except Exception as e:
                print(f"[VectorMemory] ChromaDB store error: {e}")

        # Fallback to in-memory + Redis
        return await self._store_fallback(character_id, fact, content_hash)

    async def _store_fallback(self, character_id: int, fact: MemoryFact, content_hash: str) -> bool:
        """Fallback storage using Redis/memory"""
        # In-memory storage
        if character_id not in self.memory_cache:
            self.memory_cache[character_id] = []

        # Check duplicates
        existing_hashes = {self._hash_content(f.content) for f in self.memory_cache[character_id]}
        if content_hash in existing_hashes:
            return False

        self.memory_cache[character_id].append(fact)

        # Keep sorted by importance and limit to 200 facts
        self.memory_cache[character_id].sort(key=lambda x: x.importance, reverse=True)
        self.memory_cache[character_id] = self.memory_cache[character_id][:200]

        # Also store in Redis if available
        if self.redis_client:
            try:
                key = f"casdy:vmem:{character_id}"
                data = json.dumps([f.to_dict() for f in self.memory_cache[character_id]])
                self.redis_client.set(key, data, ex=86400 * 30)  # 30 days TTL
            except Exception as e:
                print(f"[VectorMemory] Redis fallback error: {e}")

        return True

    async def store_facts_batch(
        self,
        character_id: int,
        facts: List[Dict[str, Any]]
    ) -> int:
        """Store multiple facts at once"""
        stored_count = 0
        for fact_data in facts:
            success = await self.store_fact(
                character_id=character_id,
                content=fact_data.get("content", ""),
                fact_type=fact_data.get("type", "casual"),
                importance=fact_data.get("importance"),
                source=fact_data.get("source", "conversation")
            )
            if success:
                stored_count += 1

        return stored_count

    async def recall_relevant(
        self,
        character_id: int,
        query: str,
        limit: int = 5,
        min_importance: int = 1
    ) -> List[MemoryFact]:
        """
        Recall facts relevant to the query using semantic search

        Args:
            character_id: Character to recall memories for
            query: The query to match against
            limit: Maximum number of facts to return
            min_importance: Minimum importance threshold

        Returns:
            List of relevant MemoryFact objects
        """
        # Try ChromaDB semantic search
        collection = self._get_collection(character_id)
        if collection and self.embedder:
            try:
                query_embedding = self._compute_embedding(query)

                results = collection.query(
                    query_embeddings=[query_embedding] if query_embedding else None,
                    query_texts=[query] if not query_embedding else None,
                    n_results=limit * 2,  # Get more, then filter
                    where={"importance": {"$gte": min_importance}} if min_importance > 1 else None
                )

                facts = []
                if results and results['metadatas']:
                    for metadata in results['metadatas'][0]:
                        if metadata.get('importance', 0) >= min_importance:
                            facts.append(MemoryFact.from_dict(metadata))

                # Sort by importance and limit
                facts.sort(key=lambda x: x.importance, reverse=True)
                return facts[:limit]

            except Exception as e:
                print(f"[VectorMemory] ChromaDB query error: {e}")

        # Fallback to keyword matching
        return await self._recall_fallback(character_id, query, limit, min_importance)

    async def _recall_fallback(
        self,
        character_id: int,
        query: str,
        limit: int,
        min_importance: int
    ) -> List[MemoryFact]:
        """Fallback recall using keyword matching"""
        # Load from cache or Redis
        facts = self.memory_cache.get(character_id, [])

        if not facts and self.redis_client:
            try:
                key = f"casdy:vmem:{character_id}"
                data = self.redis_client.get(key)
                if data:
                    facts = [MemoryFact.from_dict(d) for d in json.loads(data)]
                    self.memory_cache[character_id] = facts
            except Exception:
                pass

        if not facts:
            return []

        # Filter by importance
        facts = [f for f in facts if f.importance >= min_importance]

        # Simple keyword matching
        query_words = set(query.lower().split())

        def relevance_score(fact: MemoryFact) -> float:
            fact_words = set(fact.content.lower().split())
            overlap = len(query_words & fact_words)
            return overlap * fact.importance

        # Sort by relevance
        facts.sort(key=relevance_score, reverse=True)

        return facts[:limit]

    async def recall_critical(self, character_id: int) -> List[MemoryFact]:
        """
        Recall critical facts (importance >= 4) that should always be included
        These are things like user's name, key preferences, etc.
        """
        collection = self._get_collection(character_id)
        if collection:
            try:
                results = collection.get(
                    where={"importance": {"$gte": 4}},
                    limit=10
                )

                facts = []
                if results and results['metadatas']:
                    for metadata in results['metadatas']:
                        facts.append(MemoryFact.from_dict(metadata))

                return facts

            except Exception as e:
                print(f"[VectorMemory] Critical recall error: {e}")

        # Fallback
        all_facts = self.memory_cache.get(character_id, [])
        return [f for f in all_facts if f.importance >= 4][:10]

    async def get_user_name(self, character_id: int) -> Optional[str]:
        """Get the user's name if stored"""
        critical_facts = await self.recall_critical(character_id)

        for fact in critical_facts:
            if fact.fact_type == "personal":
                content_lower = fact.content.lower()
                # Look for name patterns
                name_patterns = [
                    "name is", "s'appelle", "called", "je suis", "i am",
                    "mon nom", "my name", "prénom"
                ]
                for pattern in name_patterns:
                    if pattern in content_lower:
                        # Extract the name (word after pattern)
                        idx = content_lower.find(pattern) + len(pattern)
                        rest = fact.content[idx:].strip()
                        name = rest.split()[0] if rest else None
                        if name:
                            return name.strip(".,!?")

        return None

    async def build_context_string(
        self,
        character_id: int,
        query: str,
        max_facts: int = 7
    ) -> str:
        """
        Build a context string for the LLM from relevant memories

        Returns a formatted string ready to inject into the system prompt
        """
        # Get critical facts (always included)
        critical = await self.recall_critical(character_id)

        # Get query-relevant facts
        relevant = await self.recall_relevant(character_id, query, limit=max_facts)

        # Combine and deduplicate
        all_facts = []
        seen_hashes = set()

        for fact in critical + relevant:
            fact_hash = self._hash_content(fact.content)
            if fact_hash not in seen_hashes:
                all_facts.append(fact)
                seen_hashes.add(fact_hash)

        if not all_facts:
            return ""

        # Format by type
        formatted_parts = []

        # Group by type
        by_type: Dict[str, List[str]] = {}
        for fact in all_facts:
            if fact.fact_type not in by_type:
                by_type[fact.fact_type] = []
            by_type[fact.fact_type].append(fact.content)

        # Format each type
        type_labels = {
            "personal": "INFO PERSONNELLE",
            "intimate": "PREFERENCES INTIMES",
            "preference": "PREFERENCES",
            "relationship": "RELATION",
            "emotional": "EMOTIONS",
            "event": "EVENEMENTS",
            "casual": "DIVERS"
        }

        for fact_type, contents in by_type.items():
            label = type_labels.get(fact_type, fact_type.upper())
            formatted_parts.append(f"[{label}]")
            for content in contents[:3]:  # Max 3 per type
                formatted_parts.append(f"- {content}")

        return "\n".join(formatted_parts)

    async def clear_character_memory(self, character_id: int) -> bool:
        """Clear all memory for a character"""
        # Clear ChromaDB
        if self.chroma_client and character_id in self.collections:
            try:
                collection_name = f"character_{character_id}_memory"
                self.chroma_client.delete_collection(collection_name)
                del self.collections[character_id]
            except Exception as e:
                print(f"[VectorMemory] Clear error: {e}")

        # Clear cache
        if character_id in self.memory_cache:
            del self.memory_cache[character_id]

        # Clear Redis
        if self.redis_client:
            try:
                self.redis_client.delete(f"casdy:vmem:{character_id}")
            except Exception:
                pass

        return True

    async def get_memory_stats(self, character_id: int) -> Dict[str, Any]:
        """Get statistics about stored memories"""
        collection = self._get_collection(character_id)

        stats = {
            "total_facts": 0,
            "by_type": {},
            "by_importance": {i: 0 for i in range(1, 6)},
            "storage_backend": "unknown"
        }

        if collection:
            try:
                all_data = collection.get()
                stats["total_facts"] = len(all_data['ids']) if all_data['ids'] else 0
                stats["storage_backend"] = "chromadb"

                for metadata in all_data.get('metadatas', []):
                    fact_type = metadata.get('fact_type', 'unknown')
                    importance = metadata.get('importance', 1)

                    stats["by_type"][fact_type] = stats["by_type"].get(fact_type, 0) + 1
                    stats["by_importance"][importance] = stats["by_importance"].get(importance, 0) + 1

            except Exception:
                pass
        else:
            facts = self.memory_cache.get(character_id, [])
            stats["total_facts"] = len(facts)
            stats["storage_backend"] = "memory" if not self.redis_client else "redis"

            for fact in facts:
                stats["by_type"][fact.fact_type] = stats["by_type"].get(fact.fact_type, 0) + 1
                stats["by_importance"][fact.importance] = stats["by_importance"].get(fact.importance, 0) + 1

        return stats


# Global instance
vector_memory = VectorMemoryService()
