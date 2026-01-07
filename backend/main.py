"""FastAPI Main Application - Candy AI Clone"""
import os
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import get_db, init_db
from models import Character, Conversation, Message, GeneratedImage
from schemas import (
    CharacterCreate, CharacterUpdate, CharacterResponse,
    ConversationCreate, ConversationResponse, ConversationDetailResponse,
    ChatRequest, ChatResponse,
    ImageGenerateRequest, ImageResponse, GalleryResponse,
    NewConversationResponse, MessageResponse
)
from chat_service import chat_service
from image_service import image_service
from prompt_builder import build_system_prompt, extract_character_dict, generate_greeting
from config import settings

# Import agent-based chat service if enabled
if settings.USE_AGENTS:
    from chat_service_agents import agent_chat_service
    active_chat_service = agent_chat_service
    print("Multi-Agent System: ENABLED")
else:
    active_chat_service = chat_service
    print("Multi-Agent System: DISABLED (using standard service)")

# Import V2 API routes
try:
    from api_v2 import include_v2_routes
    V2_AVAILABLE = True
    print("V2 Features: AVAILABLE")
except ImportError as e:
    V2_AVAILABLE = False
    print(f"V2 Features: NOT AVAILABLE ({e})")

# Import V3 API routes (Immersive Chat with Relationship Progression)
try:
    from api_v3 import include_v3_routes
    V3_AVAILABLE = True
    print("V3 Features (Immersive Chat): AVAILABLE")
except ImportError as e:
    V3_AVAILABLE = False
    print(f"V3 Features: NOT AVAILABLE ({e})")

app = FastAPI(
    title="Candy AI Clone",
    description="AI Character Chat & Image Generation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure images directory exists
os.makedirs(settings.IMAGES_DIR, exist_ok=True)


# =====================
# HEALTH CHECK
# =====================

@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    response = {
        "status": "healthy",
        "version": "2.0.0",
        "provider": settings.HF_PROVIDER,
        "model": settings.HF_MODEL,
        "multi_agent_system": settings.USE_AGENTS
    }
    if settings.USE_AGENTS:
        response["agents"] = active_chat_service.agent_system.get_agent_status()
    return response


@app.get("/api/debug/traces")
def get_debug_traces(limit: int = Query(10, ge=1, le=50)):
    """Get recent agent processing traces for debugging"""
    if not settings.USE_AGENTS:
        raise HTTPException(status_code=400, detail="Multi-agent system not enabled")
    return {
        "traces": active_chat_service.agent_system.get_recent_traces(limit)
    }


# =====================
# CHARACTERS
# =====================

@app.post("/api/characters", response_model=CharacterResponse)
def create_character(character: CharacterCreate, db: Session = Depends(get_db)):
    """Create a new character"""
    db_character = Character(**character.model_dump())

    # Generate system prompt
    char_dict = character.model_dump()
    db_character.system_prompt = build_system_prompt(char_dict)

    # Generate greeting if not provided
    if not db_character.greeting:
        db_character.greeting = generate_greeting(char_dict)

    db.add(db_character)
    db.commit()
    db.refresh(db_character)
    return db_character


@app.get("/api/characters", response_model=List[CharacterResponse])
def list_characters(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all characters"""
    characters = db.query(Character).order_by(
        Character.updated_at.desc()
    ).offset(skip).limit(limit).all()
    return characters


@app.get("/api/characters/{character_id}", response_model=CharacterResponse)
def get_character(character_id: int, db: Session = Depends(get_db)):
    """Get a specific character"""
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


@app.put("/api/characters/{character_id}", response_model=CharacterResponse)
def update_character(
    character_id: int,
    character: CharacterUpdate,
    db: Session = Depends(get_db)
):
    """Update a character"""
    db_character = db.query(Character).filter(Character.id == character_id).first()
    if not db_character:
        raise HTTPException(status_code=404, detail="Character not found")

    # Update fields
    update_data = character.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_character, key, value)

    # Regenerate system prompt
    char_dict = extract_character_dict(db_character)
    db_character.system_prompt = build_system_prompt(char_dict)

    db.commit()
    db.refresh(db_character)
    return db_character


@app.delete("/api/characters/{character_id}")
def delete_character(character_id: int, db: Session = Depends(get_db)):
    """Delete a character"""
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    db.delete(character)
    db.commit()
    return {"status": "deleted", "id": character_id}


# =====================
# CONVERSATIONS
# =====================

@app.post("/api/conversations", response_model=NewConversationResponse)
def create_conversation(request: ConversationCreate, db: Session = Depends(get_db)):
    """Create a new conversation with greeting"""
    character = db.query(Character).filter(
        Character.id == request.character_id
    ).first()

    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    # Create conversation
    conversation = Conversation(
        character_id=character.id,
        title="New conversation"
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    # Add greeting if defined
    greeting = None
    if character.greeting:
        greeting_msg = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=character.greeting
        )
        db.add(greeting_msg)
        db.commit()
        greeting = character.greeting

    return {
        "conversation_id": conversation.id,
        "greeting": greeting
    }


@app.get("/api/characters/{character_id}/conversations", response_model=List[ConversationResponse])
def list_character_conversations(character_id: int, db: Session = Depends(get_db)):
    """List all conversations for a character"""
    conversations = chat_service.list_conversations(db, character_id)
    return conversations


@app.get("/api/conversations/{conversation_id}")
def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """Get full conversation history"""
    result = chat_service.get_conversation_history(db, conversation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result


@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """Delete a conversation and all its messages"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db.delete(conversation)
    db.commit()
    return {"status": "deleted", "id": conversation_id}


# =====================
# CHAT
# =====================

@app.post("/api/characters/{character_id}/chat", response_model=ChatResponse)
async def send_chat_message(
    character_id: int,
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Send a message and receive a response (uses multi-agent system if enabled)"""
    try:
        result = await active_chat_service.send_message(
            db=db,
            character_id=character_id,
            user_message=request.message,
            conversation_id=request.conversation_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# IMAGE GENERATION
# =====================

@app.post("/api/characters/{character_id}/generate-image", response_model=List[ImageResponse])
async def generate_character_image(
    character_id: int,
    request: ImageGenerateRequest,
    db: Session = Depends(get_db)
):
    """Generate image(s) for a character"""
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    char_dict = extract_character_dict(character)
    prompt = image_service.build_prompt(
        char_dict,
        pose=request.pose,
        location=request.location,
        outfit=request.outfit,
        custom=request.custom
    )

    # Get consistent seed for this character
    character_seed = image_service.get_character_seed(character_id)

    try:
        filenames = await image_service.generate_multiple(
            prompt=prompt,
            count=request.count,
            style=character.style or "realistic",
            seed=character_seed
        )

        results = []
        for filename in filenames:
            if isinstance(filename, Exception):
                print(f"Image generation failed: {filename}")
                continue

            # Save to database
            gen_image = GeneratedImage(
                character_id=character_id,
                prompt=prompt,
                image_path=filename
            )
            db.add(gen_image)
            db.commit()
            db.refresh(gen_image)

            results.append({
                "id": gen_image.id,
                "character_id": character_id,
                "conversation_id": None,
                "prompt": prompt,
                "image_path": filename,
                "image_url": f"/api/images/{filename}",
                "created_at": gen_image.created_at
            })

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/characters/{character_id}/gallery", response_model=GalleryResponse)
def get_character_gallery(
    character_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all images for a character"""
    images = db.query(GeneratedImage).filter(
        GeneratedImage.character_id == character_id
    ).order_by(
        GeneratedImage.created_at.desc()
    ).offset(skip).limit(limit).all()

    total = db.query(GeneratedImage).filter(
        GeneratedImage.character_id == character_id
    ).count()

    return {
        "images": [
            {
                "id": img.id,
                "character_id": img.character_id,
                "conversation_id": img.conversation_id,
                "prompt": img.prompt,
                "image_path": img.image_path,
                "image_url": f"/api/images/{img.image_path}",
                "created_at": img.created_at
            }
            for img in images
        ],
        "total": total
    }


@app.get("/api/images/{filename}")
def get_image(filename: str):
    """Serve an image file with correct media type"""
    filepath = image_service.get_image_path(filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Image not found")

    # Detect media type from file extension
    ext = os.path.splitext(filename)[1].lower()
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif"
    }
    media_type = media_types.get(ext, "image/png")

    return FileResponse(filepath, media_type=media_type)


@app.delete("/api/images/{image_id}")
def delete_image(image_id: int, db: Session = Depends(get_db)):
    """Delete an image"""
    image = db.query(GeneratedImage).filter(GeneratedImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Delete file
    image_service.delete_image(image.image_path)

    # Delete from database
    db.delete(image)
    db.commit()

    return {"status": "deleted", "id": image_id}


# =====================
# FRONTEND SERVING
# =====================

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")

@app.get("/")
async def serve_frontend():
    """Serve the main frontend page"""
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Frontend not found")


# =====================
# STARTUP
# =====================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("Starting Candy AI Clone...")
    print(f"LLM Provider: {settings.HF_PROVIDER}")
    print(f"LLM Model: {settings.HF_MODEL}")
    print(f"Image Model (Realistic): {settings.IMAGE_MODEL_REALISTIC}")
    print(f"Image Model (Anime): {settings.IMAGE_MODEL_ANIME}")

    # Register V2 routes if available
    if V2_AVAILABLE:
        include_v2_routes(app)
        print("V2 API routes registered at /api/v2/*")

    # Register V3 routes if available (Immersive Chat)
    if V3_AVAILABLE:
        include_v3_routes(app)
        print("V3 API routes registered at /api/v3/* (Immersive Chat)")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
