"""
Services Module - Enhanced AI Companion Features
Inspired by Candy.ai architecture
"""

from .vector_memory import VectorMemoryService, vector_memory
from .context_manager import ContextManager, context_manager
from .character_consistency import CharacterConsistencyService, character_consistency
from .personality_presets import PersonalityPresets, PERSONALITY_PRESETS
from .story_mode import StoryModeService, story_mode

__all__ = [
    "VectorMemoryService",
    "vector_memory",
    "ContextManager",
    "context_manager",
    "CharacterConsistencyService",
    "character_consistency",
    "PersonalityPresets",
    "PERSONALITY_PRESETS",
    "StoryModeService",
    "story_mode"
]
