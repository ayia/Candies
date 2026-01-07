"""
API V2 Routes - Enhanced features inspired by Candy.ai

New endpoints for:
- Story Mode
- Personality Presets
- Vector Memory Management
- Character Consistency
- WebSocket Streaming (future)
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models import Character
from prompt_builder import extract_character_dict, build_system_prompt, generate_greeting

# Import V2 services
try:
    from services.vector_memory import vector_memory
    from services.context_manager import context_manager
    from services.character_consistency import character_consistency
    from services.personality_presets import personality_presets, PERSONALITY_PRESETS
    from services.story_mode import story_mode
    from chat_service_v2 import chat_service_v2
    V2_AVAILABLE = True
except ImportError as e:
    print(f"[API V2] Some services not available: {e}")
    V2_AVAILABLE = False

# Create router
router = APIRouter(prefix="/api/v2", tags=["V2 Features"])


# =====================
# SCHEMAS
# =====================

class ChatRequestV2(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    use_memory: bool = True
    use_enhanced_context: bool = True


class ChatResponseV2(BaseModel):
    response: str
    image_url: Optional[str] = None
    conversation_id: int
    message_id: int
    memory_used: bool = False
    user_name_detected: Optional[str] = None


class StoryStartRequest(BaseModel):
    scenario_id: str
    character_id: int


class StoryChoiceRequest(BaseModel):
    session_id: str
    choice_id: str
    language: str = "fr"


class MemoryFactRequest(BaseModel):
    fact: str
    fact_type: str = "personal"
    importance: int = 5


class PresetApplyRequest(BaseModel):
    preset_id: str


# =====================
# HEALTH CHECK V2
# =====================

@router.get("/health")
async def health_check_v2():
    """V2 health check with service status"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "services": {
            "vector_memory": vector_memory is not None if V2_AVAILABLE else False,
            "context_manager": context_manager is not None if V2_AVAILABLE else False,
            "character_consistency": character_consistency is not None if V2_AVAILABLE else False,
            "personality_presets": personality_presets is not None if V2_AVAILABLE else False,
            "story_mode": story_mode is not None if V2_AVAILABLE else False
        }
    }


# =====================
# CHAT V2
# =====================

@router.post("/characters/{character_id}/chat", response_model=ChatResponseV2)
async def send_chat_message_v2(
    character_id: int,
    request: ChatRequestV2,
    db: Session = Depends(get_db)
):
    """
    Enhanced chat with memory and intelligent context

    Features:
    - Long-term memory recall
    - Conversation summarization
    - Character-consistent image generation
    """
    if not V2_AVAILABLE:
        raise HTTPException(status_code=503, detail="V2 services not available")

    try:
        result = await chat_service_v2.send_message(
            db=db,
            character_id=character_id,
            user_message=request.message,
            conversation_id=request.conversation_id,
            use_enhanced_features=request.use_memory and request.use_enhanced_context
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# STORY MODE
# =====================

@router.get("/story/scenarios")
async def list_scenarios(language: str = Query("fr", regex="^(fr|en)$")):
    """List available story scenarios"""
    if not V2_AVAILABLE or not story_mode:
        raise HTTPException(status_code=503, detail="Story mode not available")

    return {
        "scenarios": story_mode.get_available_scenarios(language)
    }


@router.get("/story/scenarios/{scenario_id}")
async def get_scenario_details(
    scenario_id: str,
    language: str = Query("fr", regex="^(fr|en)$")
):
    """Get detailed info about a scenario"""
    if not V2_AVAILABLE or not story_mode:
        raise HTTPException(status_code=503, detail="Story mode not available")

    summary = story_mode.get_scenario_summary(scenario_id, language)
    if not summary:
        raise HTTPException(status_code=404, detail="Scenario not found")

    return summary


@router.post("/story/start")
async def start_story(request: StoryStartRequest):
    """Start a new story session"""
    if not V2_AVAILABLE or not story_mode:
        raise HTTPException(status_code=503, detail="Story mode not available")

    result = story_mode.start_scenario(
        scenario_id=request.scenario_id,
        character_id=request.character_id
    )

    if not result:
        raise HTTPException(status_code=404, detail="Scenario not found")

    return result


@router.post("/story/choice")
async def make_story_choice(request: StoryChoiceRequest):
    """Make a choice in the story"""
    if not V2_AVAILABLE or not story_mode:
        raise HTTPException(status_code=503, detail="Story mode not available")

    result = story_mode.make_choice(
        session_id=request.session_id,
        choice_id=request.choice_id,
        language=request.language
    )

    if not result:
        raise HTTPException(status_code=404, detail="Invalid session or choice")

    return result


@router.get("/story/session/{session_id}")
async def get_story_state(session_id: str):
    """Get current story session state"""
    if not V2_AVAILABLE or not story_mode:
        raise HTTPException(status_code=503, detail="Story mode not available")

    result = story_mode.get_session_state(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    return result


@router.delete("/story/session/{session_id}")
async def end_story_session(session_id: str):
    """End a story session"""
    if not V2_AVAILABLE or not story_mode:
        raise HTTPException(status_code=503, detail="Story mode not available")

    story_mode.end_session(session_id)
    return {"status": "ended", "session_id": session_id}


# =====================
# PERSONALITY PRESETS
# =====================

@router.get("/presets")
async def list_presets():
    """List all available personality presets"""
    if not V2_AVAILABLE or not personality_presets:
        raise HTTPException(status_code=503, detail="Presets service not available")

    return {
        "presets": personality_presets.get_all_presets()
    }


@router.get("/presets/{preset_id}")
async def get_preset_details(preset_id: str):
    """Get detailed info about a preset"""
    if not V2_AVAILABLE or not personality_presets:
        raise HTTPException(status_code=503, detail="Presets service not available")

    preset = personality_presets.get_preset(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")

    return {
        "preset": preset.to_dict(),
        "example_responses": preset.example_responses
    }


@router.post("/characters/{character_id}/apply-preset")
async def apply_preset_to_character(
    character_id: int,
    request: PresetApplyRequest,
    db: Session = Depends(get_db)
):
    """Apply a personality preset to a character"""
    if not V2_AVAILABLE or not personality_presets:
        raise HTTPException(status_code=503, detail="Presets service not available")

    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    preset = personality_presets.get_preset(request.preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")

    # Apply preset
    character.personality_traits = preset.traits
    character.unique_traits = preset.unique_traits

    # Regenerate system prompt
    char_dict = extract_character_dict(character)
    character.system_prompt = build_system_prompt(char_dict)

    # Update greeting based on preset
    char_dict["personality_traits"] = preset.traits
    character.greeting = generate_greeting(char_dict)

    db.commit()
    db.refresh(character)

    return {
        "status": "applied",
        "character_id": character_id,
        "preset_id": request.preset_id,
        "new_traits": preset.traits
    }


# =====================
# MEMORY MANAGEMENT
# =====================

@router.get("/characters/{character_id}/memory/stats")
async def get_memory_stats(character_id: int):
    """Get memory statistics for a character"""
    if not V2_AVAILABLE or not vector_memory:
        raise HTTPException(status_code=503, detail="Memory service not available")

    stats = await vector_memory.get_memory_stats(character_id)
    return stats


@router.get("/characters/{character_id}/memory/recall")
async def recall_memories(
    character_id: int,
    query: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=20)
):
    """Recall memories relevant to a query"""
    if not V2_AVAILABLE or not vector_memory:
        raise HTTPException(status_code=503, detail="Memory service not available")

    facts = await vector_memory.recall_relevant(character_id, query, limit)

    return {
        "query": query,
        "memories": [f.to_dict() for f in facts]
    }


@router.post("/characters/{character_id}/memory/store")
async def store_memory(
    character_id: int,
    request: MemoryFactRequest
):
    """Manually store a fact about the user"""
    if not V2_AVAILABLE or not vector_memory:
        raise HTTPException(status_code=503, detail="Memory service not available")

    success = await vector_memory.store_fact(
        character_id=character_id,
        content=request.fact,
        fact_type=request.fact_type,
        importance=request.importance,
        source="explicit"
    )

    return {
        "status": "stored" if success else "duplicate",
        "fact": request.fact
    }


@router.delete("/characters/{character_id}/memory")
async def clear_memory(character_id: int):
    """Clear all memories for a character"""
    if not V2_AVAILABLE or not vector_memory:
        raise HTTPException(status_code=503, detail="Memory service not available")

    await vector_memory.clear_character_memory(character_id)
    return {"status": "cleared", "character_id": character_id}


@router.get("/characters/{character_id}/memory/user-name")
async def get_remembered_user_name(character_id: int):
    """Get the user's name if remembered"""
    if not V2_AVAILABLE or not vector_memory:
        raise HTTPException(status_code=503, detail="Memory service not available")

    name = await vector_memory.get_user_name(character_id)
    return {"user_name": name}


# =====================
# CHARACTER CONSISTENCY
# =====================

@router.get("/characters/{character_id}/visual-signature")
async def get_visual_signature(character_id: int, db: Session = Depends(get_db)):
    """Get the visual signature for consistent image generation"""
    if not V2_AVAILABLE or not character_consistency:
        raise HTTPException(status_code=503, detail="Consistency service not available")

    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    char_dict = extract_character_dict(character)
    signature = character_consistency.get_signature(char_dict)

    return {
        "character_id": character_id,
        "signature": {
            "base_seed": signature.base_seed,
            "face_tokens": signature.face_tokens,
            "body_tokens": signature.body_tokens,
            "style_tokens": signature.style_tokens,
            "reference_prompts_count": len(signature.reference_prompts)
        }
    }


@router.post("/characters/{character_id}/regenerate-signature")
async def regenerate_visual_signature(character_id: int, db: Session = Depends(get_db)):
    """Regenerate visual signature for a character"""
    if not V2_AVAILABLE or not character_consistency:
        raise HTTPException(status_code=503, detail="Consistency service not available")

    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    # Clear old signature
    character_consistency.clear_signature(character_id)

    # Create new one
    char_dict = extract_character_dict(character)
    signature = character_consistency.create_signature(char_dict)

    return {
        "status": "regenerated",
        "character_id": character_id,
        "new_seed": signature.base_seed
    }


@router.post("/characters/{character_id}/generate-consistent-image")
async def generate_consistent_image(
    character_id: int,
    pose: Optional[str] = None,
    location: Optional[str] = None,
    outfit: Optional[str] = None,
    nsfw_level: int = Query(0, ge=0, le=3),
    db: Session = Depends(get_db)
):
    """Generate a character-consistent image"""
    if not V2_AVAILABLE or not character_consistency:
        raise HTTPException(status_code=503, detail="Consistency service not available")

    from image_service import image_service

    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    char_dict = extract_character_dict(character)

    # Build consistent prompt
    prompt_data = character_consistency.build_image_prompt_v2(
        character=char_dict,
        pose=pose,
        location=location,
        outfit=outfit,
        nsfw_level=nsfw_level
    )

    try:
        filename = await image_service.generate(
            prompt=prompt_data["prompt"],
            negative_prompt=prompt_data["negative_prompt"],
            style=character.style or "realistic",
            seed=prompt_data["seed"],
            nsfw=nsfw_level > 0,
            nsfw_level=nsfw_level
        )

        # Register successful prompt
        character_consistency.register_successful_prompt(character_id, prompt_data["prompt"])

        return {
            "image_url": f"/api/images/{filename}",
            "prompt_used": prompt_data["prompt"],
            "seed_used": prompt_data["seed"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# WEBSOCKET STREAMING (Future)
# =====================

@router.websocket("/ws/chat/{character_id}")
async def websocket_chat(
    websocket: WebSocket,
    character_id: int,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for streaming chat responses

    This is a placeholder for future implementation.
    Currently just accepts messages and returns complete responses.
    """
    await websocket.accept()

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            message = data.get("message", "")
            conversation_id = data.get("conversation_id")

            if not message:
                await websocket.send_json({"error": "No message provided"})
                continue

            # Process with V2 service
            try:
                result = await chat_service_v2.send_message(
                    db=db,
                    character_id=character_id,
                    user_message=message,
                    conversation_id=conversation_id
                )

                # Send response
                await websocket.send_json({
                    "type": "response",
                    "data": result
                })

            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "error": str(e)
                })

    except WebSocketDisconnect:
        print(f"[WebSocket] Client disconnected from character {character_id}")


# Function to include router in main app
def include_v2_routes(app):
    """Include V2 routes in the main FastAPI app"""
    app.include_router(router)
    print("[API V2] Routes registered")
