"""
API V3 Routes - Chat avec Progression Relationnelle Immersive

Endpoints pour:
- Chat avec tracking de relation
- Gestion des niveaux de relation
- Reset/Boost de relation (admin)
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from chat_service_v3 import chat_service_v3


# Create router
router = APIRouter(prefix="/api/v3", tags=["V3 - Immersive Chat"])


# =====================
# SCHEMAS
# =====================

class ChatRequestV3(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    user_id: str = "default"


class RelationshipBoostRequest(BaseModel):
    points: int
    user_id: str = "default"


# =====================
# HEALTH CHECK V3
# =====================

@router.get("/health")
async def health_check_v3():
    """V3 health check"""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "features": {
            "relationship_progression": True,
            "emotional_tracking": True,
            "level_based_content": True,
            "immersive_dialogue": True
        }
    }


# =====================
# CHAT V3
# =====================

@router.post("/characters/{character_id}/chat")
async def send_chat_message_v3(
    character_id: int,
    request: ChatRequestV3,
    db: Session = Depends(get_db)
):
    """
    Chat avec progression relationnelle immersive.

    Le systeme:
    - Track le niveau de relation (0-10)
    - Adapte les reponses au niveau actuel
    - Bloque le contenu NSFW jusqu'au niveau 8
    - Genere des dialogues naturels et progressifs

    Response includes:
    - response: Le message du personnage
    - relationship: {level, stage, points, points_change, level_up}
    - emotion: {mood, mood_changed, intensity}
    """
    try:
        result = await chat_service_v3.send_message(
            db=db,
            character_id=character_id,
            user_message=request.message,
            conversation_id=request.conversation_id,
            user_id=request.user_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# RELATIONSHIP MANAGEMENT
# =====================

@router.get("/characters/{character_id}/relationship")
async def get_relationship_status(
    character_id: int,
    user_id: str = Query("default")
):
    """
    Get current relationship status with a character.

    Returns:
    - level: Current level (0-10)
    - stage: Current stage name
    - points: Total affinity points
    - total_messages: Number of messages exchanged
    - user_name: User's name if remembered
    - shared_memories: List of shared memories
    - nsfw_unlocked: Whether NSFW content is unlocked
    """
    status = chat_service_v3.get_relationship_status(character_id, user_id)
    return status


@router.post("/characters/{character_id}/relationship/reset")
async def reset_relationship(
    character_id: int,
    user_id: str = Query("default")
):
    """
    Reset relationship to level 0.

    Warning: This will erase all relationship progress!
    """
    result = chat_service_v3.reset_relationship(character_id, user_id)
    return result


@router.post("/characters/{character_id}/relationship/boost")
async def boost_relationship(
    character_id: int,
    request: RelationshipBoostRequest
):
    """
    Add points to relationship (admin/debug).

    Use this to test different relationship levels.
    Points needed per level:
    - Level 1: 10 points
    - Level 2: 25 points
    - Level 3: 50 points
    - Level 4: 80 points
    - Level 5: 120 points
    - Level 6: 170 points
    - Level 7: 230 points
    - Level 8: 300 points (NSFW unlocked)
    - Level 9: 400 points
    - Level 10: 500 points
    """
    result = chat_service_v3.boost_relationship(
        character_id,
        request.points,
        request.user_id
    )
    return result


# =====================
# LEVEL INFO
# =====================

@router.get("/relationship-levels")
async def get_relationship_levels_info():
    """
    Get information about all relationship levels.

    Returns detailed info about each level including:
    - Points required
    - Stage name
    - Allowed behaviors
    - Forbidden behaviors
    """
    from services.relationship_manager import LEVEL_THRESHOLDS, LEVEL_BEHAVIORS

    levels = []
    for level, threshold in LEVEL_THRESHOLDS.items():
        behavior = LEVEL_BEHAVIORS.get(level, {})
        levels.append({
            "level": level,
            "points_required": threshold,
            "stage": behavior.get("stage", {}).value if hasattr(behavior.get("stage", {}), "value") else str(behavior.get("stage", "")),
            "tone": behavior.get("tone", ""),
            "allowed": behavior.get("allowed", []),
            "forbidden": behavior.get("forbidden", []),
            "physical_contact": behavior.get("physical_contact", ""),
            "example_responses": behavior.get("example_responses", [])[:2]
        })

    return {"levels": levels}


# Function to include router in main app
def include_v3_routes(app):
    """Include V3 routes in the main FastAPI app"""
    app.include_router(router)
    print("[API V3] Immersive chat routes registered")
