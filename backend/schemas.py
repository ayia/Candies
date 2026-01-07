"""Pydantic Schemas for API validation"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# === CHARACTER SCHEMAS ===

class CharacterBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    style: str = Field(default="realistic", pattern="^(realistic|anime)$")
    language: str = Field(default="english")  # english, french, spanish, german, italian, etc.

    # Appearance
    ethnicity: Optional[str] = None
    age_range: Optional[str] = None
    body_type: Optional[str] = None
    breast_size: Optional[str] = None
    butt_size: Optional[str] = None
    hair_color: Optional[str] = None
    hair_length: Optional[str] = None
    eye_color: Optional[str] = None

    # Attributes
    personality_traits: List[str] = Field(default_factory=list)
    voice: Optional[str] = None
    occupation: Optional[str] = None
    hobbies: List[str] = Field(default_factory=list)
    relationship_type: Optional[str] = None
    clothing_style: Optional[str] = None

    # Text fields
    tagline: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    backstory: Optional[str] = Field(None, max_length=1000)
    unique_traits: Optional[str] = Field(None, max_length=500)
    greeting: Optional[str] = Field(None, max_length=300)
    nsfw_preferences: Optional[str] = Field(None, max_length=500)


class CharacterCreate(CharacterBase):
    pass


class CharacterUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    style: Optional[str] = Field(None, pattern="^(realistic|anime)$")
    language: Optional[str] = None

    # Appearance
    ethnicity: Optional[str] = None
    age_range: Optional[str] = None
    body_type: Optional[str] = None
    breast_size: Optional[str] = None
    butt_size: Optional[str] = None
    hair_color: Optional[str] = None
    hair_length: Optional[str] = None
    eye_color: Optional[str] = None

    # Attributes
    personality_traits: Optional[List[str]] = None
    voice: Optional[str] = None
    occupation: Optional[str] = None
    hobbies: Optional[List[str]] = None
    relationship_type: Optional[str] = None
    clothing_style: Optional[str] = None

    # Text fields
    tagline: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    backstory: Optional[str] = Field(None, max_length=1000)
    unique_traits: Optional[str] = Field(None, max_length=500)
    greeting: Optional[str] = Field(None, max_length=300)
    nsfw_preferences: Optional[str] = Field(None, max_length=500)


class CharacterResponse(CharacterBase):
    id: int
    system_prompt: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# === CONVERSATION SCHEMAS ===

class ConversationCreate(BaseModel):
    character_id: int


class ConversationResponse(BaseModel):
    id: int
    character_id: int
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_message: Optional[str] = None

    class Config:
        from_attributes = True


# === MESSAGE SCHEMAS ===

class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    image_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationDetailResponse(BaseModel):
    conversation_id: int
    character_id: int
    title: Optional[str] = None
    created_at: datetime
    messages: List[MessageResponse]


# === CHAT SCHEMAS ===

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: Optional[int] = None


class ChatResponse(BaseModel):
    response: str
    image_url: Optional[str] = None
    conversation_id: int
    message_id: int


# === IMAGE SCHEMAS ===

class ImageGenerateRequest(BaseModel):
    pose: Optional[str] = None
    location: Optional[str] = None
    outfit: Optional[str] = None
    custom: Optional[str] = None
    count: int = Field(default=1, ge=1, le=4)


class ImageResponse(BaseModel):
    id: int
    character_id: int
    conversation_id: Optional[int] = None
    prompt: Optional[str] = None
    image_path: str
    image_url: str
    created_at: datetime

    class Config:
        from_attributes = True


class GalleryResponse(BaseModel):
    images: List[ImageResponse]
    total: int


# === NEW CONVERSATION RESPONSE ===

class NewConversationResponse(BaseModel):
    conversation_id: int
    greeting: Optional[str] = None
