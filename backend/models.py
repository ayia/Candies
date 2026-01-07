"""SQLAlchemy ORM Models"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    style = Column(String(20), default="realistic")
    language = Column(String(20), default="english")  # english, french, spanish, etc.

    # Appearance
    ethnicity = Column(String(30))
    age_range = Column(String(20))
    body_type = Column(String(30))
    breast_size = Column(String(20))
    butt_size = Column(String(20))
    hair_color = Column(String(30))
    hair_length = Column(String(20))
    eye_color = Column(String(20))

    # Attributes
    personality_traits = Column(JSON, default=list)
    voice = Column(String(50))
    occupation = Column(String(50))
    hobbies = Column(JSON, default=list)
    relationship_type = Column(String(50))
    clothing_style = Column(Text)

    # Text fields
    tagline = Column(String(100))
    bio = Column(Text)
    backstory = Column(Text)
    unique_traits = Column(Text)
    greeting = Column(Text)
    nsfw_preferences = Column(Text)

    # Generated system prompt
    system_prompt = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    conversations = relationship("Conversation", back_populates="character", cascade="all, delete-orphan")
    images = relationship("GeneratedImage", back_populates="character", cascade="all, delete-orphan")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id", ondelete="CASCADE"))
    title = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    character = relationship("Character", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    images = relationship("GeneratedImage", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"))
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    image_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class GeneratedImage(Base):
    __tablename__ = "generated_images"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id", ondelete="CASCADE"))
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    prompt = Column(Text)
    image_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    character = relationship("Character", back_populates="images")
    conversation = relationship("Conversation", back_populates="images")
