-- Candy AI Clone - Database Schema

-- Personnages
CREATE TABLE characters (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    style VARCHAR(20) DEFAULT 'realistic',
    language VARCHAR(20) DEFAULT 'english',

    -- Apparence
    ethnicity VARCHAR(30),
    age_range VARCHAR(20),
    body_type VARCHAR(30),
    breast_size VARCHAR(20),
    butt_size VARCHAR(20),
    hair_color VARCHAR(30),
    hair_length VARCHAR(20),
    eye_color VARCHAR(20),

    -- Attributs
    personality_traits JSONB DEFAULT '[]',
    voice VARCHAR(50),
    occupation VARCHAR(50),
    hobbies JSONB DEFAULT '[]',
    relationship_type VARCHAR(50),
    clothing_style VARCHAR(50),

    -- Textes
    tagline VARCHAR(100),
    bio TEXT,
    backstory TEXT,
    unique_traits TEXT,
    greeting TEXT,
    nsfw_preferences TEXT,

    -- System prompt (généré automatiquement)
    system_prompt TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversations
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    title VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Images générées
CREATE TABLE generated_images (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE SET NULL,
    prompt TEXT,
    image_path VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour performances
CREATE INDEX idx_conv_char ON conversations(character_id);
CREATE INDEX idx_msg_conv ON messages(conversation_id);
CREATE INDEX idx_img_char ON generated_images(character_id);
CREATE INDEX idx_conv_updated ON conversations(updated_at DESC);
CREATE INDEX idx_msg_created ON messages(created_at);

-- Fonction pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers pour updated_at
CREATE TRIGGER update_characters_updated_at
    BEFORE UPDATE ON characters
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
