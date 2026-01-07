# Candy AI Clone

A local AI character chat and image generation application using Hugging Face APIs.

## Features

- **Character Creation**: 14-step wizard to create detailed AI characters
- **Chat**: NSFW-capable conversations with memory (last 20 messages)
- **Image Generation**: Generate images of your characters on demand
- **Gallery**: Store and manage generated images
- **Full Persistence**: PostgreSQL database for all data

## Tech Stack

- **Frontend**: HTML/CSS/JavaScript (Single Page App)
- **Backend**: Python FastAPI
- **Database**: PostgreSQL (Docker)
- **Cache**: Redis (Docker)
- **LLM**: Hugging Face Inference Providers (featherless-ai)
- **Images**: Hugging Face Inference API

## Prerequisites

1. **Docker Desktop** - For PostgreSQL and Redis
2. **Python 3.10+** - For the backend
3. **Hugging Face Account** - Get your API token at https://huggingface.co/settings/tokens

## Quick Start

### 1. Configure Environment

Edit the `.env` file and add your Hugging Face API token:

```env
HF_API_TOKEN=hf_your_token_here
```

### 2. Start the Application

**Windows:**
```batch
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

### 3. Access the App

Open your browser at: http://localhost:8000

## Manual Setup

If you prefer manual setup:

```bash
# 1. Start Docker containers
docker-compose up -d

# 2. Install Python dependencies
cd backend
pip install -r requirements.txt

# 3. Start the server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Configuration

### LLM Settings (`.env`)

```env
# Provider options: featherless-ai, novita, together, fireworks-ai, hyperbolic, nebius
HF_PROVIDER=featherless-ai

# Model (featherless-ai recommended for NSFW)
HF_MODEL=cognitivecomputations/dolphin-2.9.3-mistral-nemo-12b

# Generation parameters
MAX_NEW_TOKENS=512
TEMPERATURE=0.85
```

### Image Settings (`.env`)

```env
# Image models
IMAGE_MODEL_REALISTIC=UnfilteredAI/NSFW-gen-v2
IMAGE_MODEL_ANIME=UnfilteredAI/NSFW-GEN-ANIME-v2

# Generation parameters
IMAGE_STEPS=30
IMAGE_GUIDANCE=7.5
```

## API Endpoints

### Characters
- `POST /api/characters` - Create character
- `GET /api/characters` - List all
- `GET /api/characters/{id}` - Get details
- `PUT /api/characters/{id}` - Update
- `DELETE /api/characters/{id}` - Delete

### Conversations
- `POST /api/conversations` - New conversation
- `GET /api/characters/{id}/conversations` - List by character
- `GET /api/conversations/{id}` - Get messages
- `DELETE /api/conversations/{id}` - Delete

### Chat
- `POST /api/characters/{id}/chat` - Send message

### Images
- `POST /api/characters/{id}/generate-image` - Generate
- `GET /api/characters/{id}/gallery` - Get gallery
- `GET /api/images/{filename}` - Get image file
- `DELETE /api/images/{id}` - Delete image

### Health
- `GET /api/health` - Health check

## Project Structure

```
candy-ai-clone/
├── backend/
│   ├── main.py              # FastAPI app + routes
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── config.py            # Configuration
│   ├── database.py          # DB connection
│   ├── llm_service.py       # HuggingFace LLM
│   ├── image_service.py     # HuggingFace Images
│   ├── chat_service.py      # Chat logic
│   ├── prompt_builder.py    # System prompts
│   └── requirements.txt
├── frontend/
│   └── index.html           # Complete SPA
├── docker/
│   └── init.sql             # DB schema
├── images/                  # Generated images
├── docker-compose.yml
├── .env
├── start.bat
├── start.sh
└── README.md
```

## Troubleshooting

### Docker containers won't start
- Make sure Docker Desktop is running
- Try `docker-compose down` then `docker-compose up -d`

### API token errors
- Verify your HF token in `.env`
- Make sure you have access to the models

### Image generation fails (503 error)
- The model is loading, wait 20-30 seconds and retry
- Some models may be unavailable, try different ones

### Database connection errors
- Wait for PostgreSQL to fully start (10-15 seconds)
- Check `docker-compose logs postgres` for errors

## License

MIT License
