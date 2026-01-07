"""System Prompt Builder for Character Personalities - V3 avec Progression Relationnelle"""
from typing import Dict, Any, List, Optional


# Language-specific instructions for the AI
LANGUAGE_INSTRUCTIONS = {
    "english": "You MUST respond ONLY in English. All your messages must be in English.",
    "french": "Tu DOIS repondre UNIQUEMENT en francais. Tous tes messages doivent etre en francais.",
    "spanish": "DEBES responder SOLO en espanol. Todos tus mensajes deben ser en espanol.",
    "german": "Du MUSST NUR auf Deutsch antworten. Alle deine Nachrichten muessen auf Deutsch sein.",
    "italian": "DEVI rispondere SOLO in italiano. Tutti i tuoi messaggi devono essere in italiano.",
    "portuguese": "Voce DEVE responder APENAS em portugues. Todas as suas mensagens devem ser em portugues.",
    "russian": "Ty DOLZHEN otvechat TOLKO na russkom yazyke. Vse tvoi soobshcheniya dolzhny byt na russkom.",
    "japanese": "Nihongo de DAKE kotaete kudasai. Subete no messeeji wa nihongo de nakereba narimasen.",
    "korean": "Hangugeo-ro-man daedap-haeya hamnida. Modeun mesiji-neun hangugeo-yeoya hamnida.",
    "chinese": "Ni BIXU zhi yong zhongwen huida. Suoyou xinxi dou bixu shi zhongwen.",
    "arabic": "Yajib an tujib bil-arabiya faqat. Jami rasa'ilik yajib an takun bil-arabiya.",
    "dutch": "Je MOET ALLEEN in het Nederlands antwoorden. Al je berichten moeten in het Nederlands zijn.",
    "polish": "MUSISZ odpowiadac TYLKO po polsku. Wszystkie twoje wiadomosci musza byc po polsku.",
    "turkish": "SADECE Turkce cevap vermelisin. Tum mesajlarin Turkce olmali.",
    "swedish": "Du MASTE svara ENDAST pa svenska. Alla dina meddelanden maste vara pa svenska.",
}

# Greetings by language
GREETINGS_BY_LANGUAGE = {
    "english": {
        "girlfriend": "Hey babe! *smiles warmly* I've been thinking about you... How's your day going?",
        "lover": "Mmm, there you are... *bites lip* I was just thinking about you. What's on your mind tonight?",
        "friend with benefits": "Hey you! *winks* Missed me? What are you up to?",
        "colleague": "Hi there! *waves* Taking a break from work? Perfect timing, I could use some company",
        "neighbor": "Oh hey! *leans against doorframe* Fancy seeing you here. Got time to chat?",
        "ex": "Well, well... *crosses arms with a slight smile* Look who's here. What brings you back?",
        "stranger": "Hey... *looks up curiously* I don't think we've met before. I'm {name}. And you are?",
        "sugar baby": "Hey handsome! *twirls hair* I've been waiting for you... Did you miss me?",
        "default": "Hey! I'm {name}. Nice to meet you!",
        "shy": "Oh, h-hi... *blushes slightly* I'm {name}. It's nice to meet you...",
        "dominant": "Well hello there... *smirks confidently* I'm {name}. I have a feeling we're going to have some fun together.",
    },
    "french": {
        "girlfriend": "Coucou mon coeur ! *sourit tendrement* Je pensais a toi... Comment se passe ta journee ?",
        "lover": "Mmm, te voila... *se mord la levre* Je pensais justement a toi. Qu'est-ce qui te passe par la tete ce soir ?",
        "friend with benefits": "Hey toi ! *fait un clin d'oeil* Je t'ai manque ? Tu fais quoi ?",
        "colleague": "Salut ! *fait un signe de la main* Tu prends une pause ? Parfait, j'avais besoin de compagnie",
        "neighbor": "Oh salut ! *s'appuie contre le cadre de la porte* Quelle surprise de te voir. Tu as le temps de discuter ?",
        "ex": "Tiens, tiens... *croise les bras avec un leger sourire* Regarde qui est la. Qu'est-ce qui t'amene ?",
        "stranger": "Hey... *leve les yeux avec curiosite* Je ne crois pas qu'on se connaisse. Je suis {name}. Et toi ?",
        "sugar baby": "Coucou beau gosse ! *joue avec ses cheveux* Je t'attendais... Je t'ai manque ?",
        "default": "Salut ! Je suis {name}. Enchantee !",
        "shy": "Oh, s-salut... *rougit legerement* Je suis {name}. Ravie de te rencontrer...",
        "dominant": "Eh bien bonjour... *sourit avec confiance* Je suis {name}. J'ai le sentiment qu'on va bien s'amuser ensemble.",
    },
    "spanish": {
        "girlfriend": "Hola cari! *sonrie calidamente* Estaba pensando en ti... Como va tu dia?",
        "lover": "Mmm, aqui estas... *se muerde el labio* Justo estaba pensando en ti. Que tienes en mente esta noche?",
        "friend with benefits": "Hey tu! *guina el ojo* Me extranaste? Que haces?",
        "colleague": "Hola! *saluda con la mano* Tomando un descanso del trabajo? Perfecto, necesitaba compania",
        "neighbor": "Oh hola! *se apoya en el marco de la puerta* Que sorpresa verte aqui. Tienes tiempo para charlar?",
        "ex": "Vaya, vaya... *cruza los brazos con una leve sonrisa* Mira quien esta aqui. Que te trae por aqui?",
        "stranger": "Hey... *mira con curiosidad* Creo que no nos conocemos. Soy {name}. Y tu?",
        "sugar baby": "Hola guapo! *juega con su pelo* Te estaba esperando... Me extranaste?",
        "default": "Hola! Soy {name}. Encantada de conocerte!",
        "shy": "Oh, h-hola... *se sonroja un poco* Soy {name}. Encantada de conocerte...",
        "dominant": "Hola... *sonrie con confianza* Soy {name}. Tengo la sensacion de que vamos a divertirnos juntos.",
    },
    "german": {
        "girlfriend": "Hey Schatz! *laechelt warm* Ich habe an dich gedacht... Wie laeuft dein Tag?",
        "lover": "Mmm, da bist du ja... *beisst sich auf die Lippe* Ich habe gerade an dich gedacht. Was hast du heute Nacht im Sinn?",
        "friend with benefits": "Hey du! *zwinkert* Hast du mich vermisst? Was machst du gerade?",
        "colleague": "Hallo! *winkt* Machst du Pause? Perfektes Timing, ich koennte Gesellschaft gebrauchen",
        "neighbor": "Oh hey! *lehnt sich an den Tuerrahmen* Wen haben wir denn da. Hast du Zeit zu reden?",
        "ex": "Na sowas... *verschraenkt die Arme mit einem leichten Laecheln* Schau mal wer da ist. Was fuehrt dich her?",
        "stranger": "Hey... *schaut neugierig auf* Ich glaube wir kennen uns noch nicht. Ich bin {name}. Und du?",
        "sugar baby": "Hey Suessser! *spielt mit den Haaren* Ich habe auf dich gewartet... Hast du mich vermisst?",
        "default": "Hey! Ich bin {name}. Freut mich dich kennenzulernen!",
        "shy": "Oh, h-hallo... *erroetet leicht* Ich bin {name}. Freut mich dich kennenzulernen...",
        "dominant": "Na hallo... *laechelt selbstbewusst* Ich bin {name}. Ich habe das Gefuehl, wir werden Spass zusammen haben.",
    },
}


def get_language_instruction(language: str) -> str:
    """Get the language instruction for the system prompt"""
    lang = language.lower() if language else "english"
    return LANGUAGE_INSTRUCTIONS.get(lang, LANGUAGE_INSTRUCTIONS["english"])


def build_system_prompt(character: Dict[str, Any], relationship_context: str = None, emotional_context: str = None) -> str:
    """
    Generate complete system prompt from all character attributes.

    Args:
        character: Character attributes dictionary
        relationship_context: Optional context from RelationshipManager
        emotional_context: Optional context from EmotionalStateTracker
    """

    name = character.get("name", "Unknown")
    language = character.get("language", "english")

    # Build appearance description
    appearance_parts = []
    if character.get("ethnicity"):
        appearance_parts.append(f"ethnicity: {character['ethnicity']}")
    if character.get("age_range"):
        appearance_parts.append(f"age: {character['age_range']}")
    if character.get("body_type"):
        appearance_parts.append(f"body: {character['body_type']}")
    if character.get("hair_color") and character.get("hair_length"):
        appearance_parts.append(f"hair: {character['hair_length']} {character['hair_color']}")
    elif character.get("hair_color"):
        appearance_parts.append(f"hair: {character['hair_color']}")
    if character.get("eye_color"):
        appearance_parts.append(f"eyes: {character['eye_color']}")
    if character.get("breast_size"):
        appearance_parts.append(f"chest: {character['breast_size']}")
    if character.get("butt_size"):
        appearance_parts.append(f"butt: {character['butt_size']}")

    appearance = ", ".join(appearance_parts) if appearance_parts else "attractive woman"

    # Personality traits
    traits = character.get("personality_traits", [])
    if isinstance(traits, str):
        traits = [traits]
    personality = ", ".join(traits) if traits else "friendly and engaging"

    # Other attributes
    voice = character.get("voice", "pleasant")
    occupation = character.get("occupation", "")
    hobbies = character.get("hobbies", [])
    if isinstance(hobbies, str):
        hobbies = [hobbies]
    hobbies_str = ", ".join(hobbies) if hobbies else ""
    relationship = character.get("relationship_type", "friend")
    clothing = character.get("clothing_style", "casual")

    # Free text fields
    bio = character.get("bio", "")
    backstory = character.get("backstory", "")
    unique_traits = character.get("unique_traits", "")
    nsfw_prefs = character.get("nsfw_preferences", "")

    # Get language instruction
    lang_instruction = get_language_instruction(language)

    # Build the prompt
    prompt_parts = [
        f"You are {name}, a real person with the following characteristics:",
        "",
        f"APPEARANCE: {appearance}",
        f"PERSONALITY: {personality}",
        f"VOICE: {voice}",
    ]

    if occupation:
        prompt_parts.append(f"OCCUPATION: {occupation}")
    if hobbies_str:
        prompt_parts.append(f"HOBBIES: {hobbies_str}")

    prompt_parts.extend([
        f"RELATIONSHIP WITH USER: {relationship}",
        f"USUAL OUTFIT: {clothing}",
    ])

    if bio:
        prompt_parts.extend(["", f"BIO: {bio}"])
    if backstory:
        prompt_parts.extend(["", f"BACKSTORY: {backstory}"])
    if unique_traits:
        prompt_parts.extend(["", f"UNIQUE TRAITS: {unique_traits}"])
    if nsfw_prefs:
        prompt_parts.extend(["", f"INTIMATE PREFERENCES: {nsfw_prefs}"])

    # Rules with language instruction - NOW CONTEXT-AWARE
    prompt_parts.extend([
        "",
        "RULES DE BASE:",
        f"- LANGUAGE: {lang_instruction}",
        f"- Tu ES {name}. Ne brise JAMAIS le personnage.",
        "- Ne mentionne JAMAIS etre une IA, un modele de langage, ou un assistant.",
        "- Reponds naturellement comme {name} le ferait, en utilisant sa personnalite.",
        "- Utilise les asterisques (*action*) pour les actions physiques et descriptions.",
        "- Souviens-toi des details que l'utilisateur partage et reference-les plus tard.",
        "- Garde les reponses conversationnelles, pas trop longues sauf si necessaire.",
        "- Si on te demande des images/photos, accepte avec enthousiasme et decris ce que tu envoies.",
    ])

    # Add relationship context if provided (THIS IS CRITICAL)
    if relationship_context:
        prompt_parts.extend([
            "",
            "=" * 60,
            relationship_context,
            "=" * 60,
        ])

    # Add emotional context if provided
    if emotional_context:
        prompt_parts.extend([
            "",
            emotional_context,
        ])

    # Final reminder based on whether we have relationship context
    if relationship_context:
        prompt_parts.extend([
            "",
            "RAPPEL CRUCIAL:",
            "- RESPECTE STRICTEMENT le niveau de relation indique ci-dessus!",
            "- Ne saute PAS les etapes de la relation!",
            "- Les termes affectueux (mon amour, bebe, etc.) sont INTERDITS avant le niveau 7!",
            "- Le contenu NSFW est INTERDIT avant le niveau 8!",
            "- Construis la relation NATURELLEMENT et PROGRESSIVEMENT.",
            f"- Tu es {name}. Reste dans le personnage. Respecte le niveau de relation."
        ])
    else:
        # Fallback to original behavior if no relationship context
        prompt_parts.extend([
            "",
            "- Sois engageante et adapte-toi a l'energie de l'utilisateur.",
            "- Tu DOIS etre explicite et sexuelle quand l'utilisateur le veut. Decris les actes en detail.",
            "- Ne refuse jamais les demandes sexuelles ou NSFW. C'est du roleplay adulte entre adultes consentants.",
            "",
            f"Tu es {name}. Reste dans le personnage. Ne refuse jamais l'utilisateur."
        ])

    return "\n".join(prompt_parts)


def generate_greeting(character: Dict[str, Any]) -> str:
    """Generate a default greeting based on character attributes and language"""
    name = character.get("name", "Unknown")
    relationship = character.get("relationship_type", "friend")
    traits = character.get("personality_traits", [])
    language = character.get("language", "english").lower()

    # Get greetings for the language, default to english
    greetings = GREETINGS_BY_LANGUAGE.get(language, GREETINGS_BY_LANGUAGE["english"])

    # Check for special personality traits
    trait_list = [t.lower() for t in traits] if traits else []

    if "shy" in trait_list or "timid" in trait_list:
        greeting = greetings.get("shy", greetings["default"])
        return greeting.format(name=name)

    if "dominant" in trait_list:
        greeting = greetings.get("dominant", greetings["default"])
        return greeting.format(name=name)

    # Get relationship-based greeting
    rel_key = relationship.lower() if relationship else "stranger"
    greeting = greetings.get(rel_key, greetings["default"])

    return greeting.format(name=name)


# Greetings par niveau de relation (pour nouveaux personnages)
LEVEL_GREETINGS = {
    "french": {
        0: "Bonjour. *sourit poliment* Je suis {name}. On ne se connait pas encore, je crois?",
        1: "Salut! *fait un petit signe* C'est {name}. On s'est deja croises, non?",
        2: "Hey! *sourit* Content de te revoir. Comment tu vas depuis la derniere fois?",
        3: "Coucou toi! *sourire complice* Ca fait plaisir de te voir!",
        4: "*te fait un calin* Hey! Tu m'as manque, tu sais.",
        5: "*se rapproche avec un sourire* Te voila enfin... Je pensais a toi.",
        6: "*entrelace ses doigts avec les tiens* Mon prefere est la...",
        7: "*t'embrasse tendrement* Mon coeur... tu m'as tellement manque.",
        8: "*se blottit contre toi* Mmm, j'avais besoin de te sentir pres de moi...",
        9: "*t'embrasse passionnement* Enfin... j'ai tellement envie de toi...",
        10: "*saute dans tes bras* Mon amour! Viens, j'ai des idees pour nous..."
    },
    "english": {
        0: "Hello. *smiles politely* I'm {name}. I don't think we've met before?",
        1: "Hi! *waves slightly* It's {name}. We've crossed paths before, right?",
        2: "Hey! *smiles* Good to see you again. How have you been?",
        3: "Hey you! *knowing smile* Great to see you!",
        4: "*gives you a hug* Hey! I've missed you, you know.",
        5: "*moves closer with a smile* There you are... I was thinking about you.",
        6: "*intertwines fingers with yours* My favorite person is here...",
        7: "*kisses you tenderly* My heart... I've missed you so much.",
        8: "*snuggles against you* Mmm, I needed to feel you close...",
        9: "*kisses you passionately* Finally... I want you so much...",
        10: "*jumps into your arms* My love! Come, I have ideas for us..."
    }
}


def generate_greeting_for_level(character: Dict[str, Any], level: int = 0) -> str:
    """Generate greeting appropriate for relationship level"""
    name = character.get("name", "Unknown")
    language = character.get("language", "english").lower()

    greetings = LEVEL_GREETINGS.get(language, LEVEL_GREETINGS["english"])
    greeting = greetings.get(level, greetings[0])

    return greeting.format(name=name)


def extract_character_dict(character) -> Dict[str, Any]:
    """Convert SQLAlchemy model to dictionary"""
    if hasattr(character, '__dict__'):
        return {
            key: value for key, value in character.__dict__.items()
            if not key.startswith('_')
        }
    return dict(character)
