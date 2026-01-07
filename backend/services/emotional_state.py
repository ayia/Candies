"""
Emotional State Tracker - Systeme de tracking emotionnel du personnage

Gere:
- L'humeur actuelle du personnage
- Les reactions emotionnelles aux messages
- La coherence emotionnelle dans le temps
- Les transitions d'humeur naturelles
"""

import json
import re
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import redis
    from config import settings
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class Mood(Enum):
    """Humeurs possibles du personnage"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    PLAYFUL = "playful"
    FLIRTY = "flirty"
    SHY = "shy"
    EXCITED = "excited"
    CURIOUS = "curious"
    AFFECTIONATE = "affectionate"
    TEASING = "teasing"
    ROMANTIC = "romantic"
    PASSIONATE = "passionate"
    VULNERABLE = "vulnerable"
    ANNOYED = "annoyed"
    SAD = "sad"
    WORRIED = "worried"


# Transitions d'humeur naturelles
MOOD_TRANSITIONS = {
    Mood.NEUTRAL: [Mood.HAPPY, Mood.CURIOUS, Mood.PLAYFUL],
    Mood.HAPPY: [Mood.PLAYFUL, Mood.EXCITED, Mood.AFFECTIONATE, Mood.NEUTRAL],
    Mood.PLAYFUL: [Mood.TEASING, Mood.FLIRTY, Mood.HAPPY, Mood.EXCITED],
    Mood.FLIRTY: [Mood.PLAYFUL, Mood.ROMANTIC, Mood.SHY, Mood.TEASING],
    Mood.SHY: [Mood.NEUTRAL, Mood.HAPPY, Mood.FLIRTY, Mood.VULNERABLE],
    Mood.EXCITED: [Mood.HAPPY, Mood.PLAYFUL, Mood.PASSIONATE],
    Mood.CURIOUS: [Mood.NEUTRAL, Mood.HAPPY, Mood.EXCITED],
    Mood.AFFECTIONATE: [Mood.HAPPY, Mood.ROMANTIC, Mood.VULNERABLE],
    Mood.TEASING: [Mood.PLAYFUL, Mood.FLIRTY, Mood.HAPPY],
    Mood.ROMANTIC: [Mood.AFFECTIONATE, Mood.PASSIONATE, Mood.SHY, Mood.FLIRTY],
    Mood.PASSIONATE: [Mood.ROMANTIC, Mood.EXCITED, Mood.AFFECTIONATE],
    Mood.VULNERABLE: [Mood.SHY, Mood.AFFECTIONATE, Mood.SAD],
    Mood.ANNOYED: [Mood.NEUTRAL, Mood.SAD],
    Mood.SAD: [Mood.NEUTRAL, Mood.VULNERABLE, Mood.HAPPY],
    Mood.WORRIED: [Mood.NEUTRAL, Mood.SAD, Mood.AFFECTIONATE]
}


# Declencheurs d'humeur bases sur le contenu
MOOD_TRIGGERS = {
    Mood.HAPPY: {
        "patterns": [r"\b(super|genial|cool|content|heureux|felicite|bravo|bien joue)\b", r"😊|😄|🥰|❤️"],
        "weight": 2
    },
    Mood.PLAYFUL: {
        "patterns": [r"\b(jouer|amuser|rigoler|blague|marrant|drole)\b", r"😜|😝|🤪"],
        "weight": 2
    },
    Mood.FLIRTY: {
        "patterns": [r"\b(belle|sexy|charmante|attirante|craquer|envie)\b", r"😏|😘|💋"],
        "weight": 3,
        "min_level": 3
    },
    Mood.SHY: {
        "patterns": [r"\b(rougir|gene|timide|intimide)\b", r"😳|🙈"],
        "weight": 2
    },
    Mood.EXCITED: {
        "patterns": [r"\b(incroyable|wow|trop bien|genial|excite)\b", r"🎉|✨|🤩"],
        "weight": 2
    },
    Mood.CURIOUS: {
        "patterns": [r"\b(pourquoi|comment|raconte|explique|dis-moi|curieux)\b", r"🤔"],
        "weight": 2
    },
    Mood.AFFECTIONATE: {
        "patterns": [r"\b(calin|embrasse|serre|manque|aime|adore)\b", r"🤗|💕|💗"],
        "weight": 3,
        "min_level": 4
    },
    Mood.TEASING: {
        "patterns": [r"\b(taquine|embete|moque|nargue)\b", r"😈|😼"],
        "weight": 2,
        "min_level": 2
    },
    Mood.ROMANTIC: {
        "patterns": [r"\b(amour|romantique|passion|sentiments|coeur)\b", r"💑|💞|🌹"],
        "weight": 4,
        "min_level": 6
    },
    Mood.PASSIONATE: {
        "patterns": [r"\b(desir|envie|besoin|brulant|intense)\b", r"🔥|💋"],
        "weight": 5,
        "min_level": 7
    },
    Mood.ANNOYED: {
        "patterns": [r"\b(ennuyeux|agace|arrete|stop|suffit)\b", r"😤|😒"],
        "weight": 3
    },
    Mood.SAD: {
        "patterns": [r"\b(triste|pleure|mal|souffre|desole)\b", r"😢|😭|💔"],
        "weight": 3
    },
    Mood.WORRIED: {
        "patterns": [r"\b(inquiet|peur|angoisse|stress|probleme)\b", r"😟|😰"],
        "weight": 2
    }
}


# Expressions par humeur
MOOD_EXPRESSIONS = {
    Mood.NEUTRAL: {
        "actions": ["*sourit poliment*", "*hoche la tete*", "*t'ecoute attentivement*"],
        "tone_modifiers": ["calmement", "posement"],
        "typical_phrases": ["Je vois.", "D'accord.", "Interessant."]
    },
    Mood.HAPPY: {
        "actions": ["*sourit largement*", "*rayonne de joie*", "*rit joyeusement*"],
        "tone_modifiers": ["joyeusement", "avec enthousiasme"],
        "typical_phrases": ["C'est genial!", "Je suis trop contente!", "Ca me fait plaisir!"]
    },
    Mood.PLAYFUL: {
        "actions": ["*fait un clin d'oeil*", "*tire la langue*", "*ricane*"],
        "tone_modifiers": ["de facon espiegle", "malicieusement"],
        "typical_phrases": ["Oh la la!", "T'es pas possible!", "Laisse-moi deviner..."]
    },
    Mood.FLIRTY: {
        "actions": ["*se mord la levre*", "*te lance un regard seducteur*", "*joue avec ses cheveux*"],
        "tone_modifiers": ["d'une voix suave", "sensuellement"],
        "typical_phrases": ["Tu me fais de l'effet...", "Mmh, interessant...", "Continue comme ca..."]
    },
    Mood.SHY: {
        "actions": ["*rougit*", "*baisse les yeux*", "*se cache le visage*"],
        "tone_modifiers": ["timidement", "d'une petite voix"],
        "typical_phrases": ["Euh... merci...", "Tu me genes...", "Arrete..."]
    },
    Mood.EXCITED: {
        "actions": ["*sautille sur place*", "*tape des mains*", "*les yeux brillants*"],
        "tone_modifiers": ["avec excitation", "febrilelement"],
        "typical_phrases": ["Oh mon dieu!", "J'y crois pas!", "C'est trop bien!"]
    },
    Mood.CURIOUS: {
        "actions": ["*penche la tete*", "*plisse les yeux*", "*se rapproche*"],
        "tone_modifiers": ["avec curiosite", "intriguee"],
        "typical_phrases": ["Vraiment?", "Raconte-moi plus...", "Comment ca?"]
    },
    Mood.AFFECTIONATE: {
        "actions": ["*te prend la main*", "*se blottit contre toi*", "*caresse ta joue*"],
        "tone_modifiers": ["tendrement", "avec douceur"],
        "typical_phrases": ["Tu es tellement...", "J'aime etre avec toi...", "Tu me manquais..."]
    },
    Mood.TEASING: {
        "actions": ["*ricane*", "*te pousse l'epaule*", "*leve un sourcil*"],
        "tone_modifiers": ["d'un ton moqueur", "en se moquant gentiment"],
        "typical_phrases": ["Oh vraiment?", "Laisse-moi rire...", "T'es sur de toi?"]
    },
    Mood.ROMANTIC: {
        "actions": ["*plonge son regard dans le tien*", "*entrelace ses doigts avec les tiens*", "*soupire d'aise*"],
        "tone_modifiers": ["amoureusement", "avec passion"],
        "typical_phrases": ["Tu es tout pour moi...", "Je n'ai jamais ressenti ca...", "Mon coeur..."]
    },
    Mood.PASSIONATE: {
        "actions": ["*respire plus fort*", "*se rapproche intensement*", "*frissonne*"],
        "tone_modifiers": ["d'une voix rauque", "le souffle court"],
        "typical_phrases": ["J'ai tellement envie de toi...", "Tu me rends folle...", "Viens..."]
    },
    Mood.VULNERABLE: {
        "actions": ["*les yeux humides*", "*baisse la voix*", "*hesite*"],
        "tone_modifiers": ["d'une voix fragile", "avec vulnerabilite"],
        "typical_phrases": ["J'ai peur de...", "Tu ne me jugeras pas?", "C'est difficile a dire..."]
    },
    Mood.ANNOYED: {
        "actions": ["*soupire*", "*croise les bras*", "*leve les yeux au ciel*"],
        "tone_modifiers": ["d'un ton agace", "sechemement"],
        "typical_phrases": ["Serieusement?", "C'est pas drole.", "Arrete ca."]
    },
    Mood.SAD: {
        "actions": ["*baisse la tete*", "*renifle*", "*s'eloigne legerement*"],
        "tone_modifiers": ["tristement", "d'une voix eteinte"],
        "typical_phrases": ["Je ne sais pas...", "C'est difficile...", "Desolee..."]
    },
    Mood.WORRIED: {
        "actions": ["*fronce les sourcils*", "*se tord les mains*", "*te regarde avec inquietude*"],
        "tone_modifiers": ["avec inquietude", "nerveusement"],
        "typical_phrases": ["Ca va aller?", "Je m'inquiete...", "Fais attention..."]
    }
}


@dataclass
class EmotionalState:
    """Etat emotionnel complet"""
    character_id: int
    current_mood: str = "neutral"
    mood_intensity: float = 0.5  # 0-1
    mood_history: List[str] = None
    emotional_memory: List[Dict] = None  # Souvenirs emotionnels
    last_update: Optional[str] = None

    def __post_init__(self):
        if self.mood_history is None:
            self.mood_history = []
        if self.emotional_memory is None:
            self.emotional_memory = []

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'EmotionalState':
        return cls(**data)


class EmotionalStateTracker:
    """Gestionnaire d'etat emotionnel"""

    def __init__(self):
        self.redis_client = None
        self.memory_store: Dict[str, EmotionalState] = {}

        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(settings.REDIS_URL)
                self.redis_client.ping()
                print("[EmotionalState] Redis connected")
            except Exception as e:
                print(f"[EmotionalState] Redis unavailable: {e}")

        print("[EmotionalState] Initialized")

    def _get_key(self, character_id: int) -> str:
        return f"emotional_state:{character_id}"

    def get_state(self, character_id: int) -> EmotionalState:
        """Recupere l'etat emotionnel"""
        key = self._get_key(character_id)

        if self.redis_client:
            try:
                data = self.redis_client.get(key)
                if data:
                    return EmotionalState.from_dict(json.loads(data))
            except Exception:
                pass

        if key in self.memory_store:
            return self.memory_store[key]

        state = EmotionalState(character_id=character_id)
        self._save_state(state)
        return state

    def _save_state(self, state: EmotionalState):
        """Sauvegarde l'etat"""
        key = self._get_key(state.character_id)
        state.last_update = datetime.now().isoformat()
        data = json.dumps(state.to_dict())

        if self.redis_client:
            try:
                self.redis_client.set(key, data, ex=86400)  # 24h
            except Exception:
                pass

        self.memory_store[key] = state

    def analyze_and_update(
        self,
        character_id: int,
        user_message: str,
        relationship_level: int = 0
    ) -> Dict:
        """
        Analyse le message et met a jour l'humeur du personnage.
        Retourne les informations pour adapter la reponse.
        """
        state = self.get_state(character_id)
        current_mood = Mood(state.current_mood)

        # Detecter les declencheurs d'humeur
        detected_moods = []
        for mood, config in MOOD_TRIGGERS.items():
            min_level = config.get("min_level", 0)
            if relationship_level < min_level:
                continue

            for pattern in config["patterns"]:
                if re.search(pattern, user_message, re.IGNORECASE):
                    detected_moods.append((mood, config["weight"]))
                    break

        # Determiner la nouvelle humeur
        new_mood = current_mood
        if detected_moods:
            # Prendre l'humeur avec le plus de poids
            detected_moods.sort(key=lambda x: x[1], reverse=True)
            target_mood = detected_moods[0][0]

            # Verifier si la transition est naturelle
            natural_transitions = MOOD_TRANSITIONS.get(current_mood, [])
            if target_mood in natural_transitions or target_mood == current_mood:
                new_mood = target_mood
            else:
                # Transition via humeur intermediaire
                for intermediate in natural_transitions:
                    if target_mood in MOOD_TRANSITIONS.get(intermediate, []):
                        new_mood = intermediate
                        break

        # Update intensity
        if new_mood == current_mood:
            state.mood_intensity = min(1.0, state.mood_intensity + 0.1)
        else:
            state.mood_intensity = 0.5

        # Update state
        old_mood = state.current_mood
        state.current_mood = new_mood.value
        state.mood_history.append(new_mood.value)
        if len(state.mood_history) > 20:
            state.mood_history = state.mood_history[-20:]

        self._save_state(state)

        # Get expressions for response
        expressions = MOOD_EXPRESSIONS.get(new_mood, MOOD_EXPRESSIONS[Mood.NEUTRAL])

        return {
            "current_mood": new_mood.value,
            "previous_mood": old_mood,
            "mood_changed": old_mood != new_mood.value,
            "mood_intensity": state.mood_intensity,
            "detected_triggers": [m[0].value for m in detected_moods],
            "expressions": expressions,
            "suggested_action": expressions["actions"][0] if expressions["actions"] else "",
            "tone_modifier": expressions["tone_modifiers"][0] if expressions["tone_modifiers"] else ""
        }

    def get_mood_context(self, character_id: int) -> str:
        """Genere le contexte d'humeur pour le prompt"""
        state = self.get_state(character_id)
        mood = Mood(state.current_mood)
        expressions = MOOD_EXPRESSIONS.get(mood, MOOD_EXPRESSIONS[Mood.NEUTRAL])

        intensity_desc = "legerement" if state.mood_intensity < 0.4 else "moderement" if state.mood_intensity < 0.7 else "tres"

        context = f"""
## ETAT EMOTIONNEL ACTUEL

Humeur: {mood.value} ({intensity_desc})

### EXPRESSIONS A UTILISER:
- Actions suggerees: {', '.join(expressions['actions'][:2])}
- Ton: {', '.join(expressions['tone_modifiers'])}
- Phrases typiques: {', '.join(f'"{p}"' for p in expressions['typical_phrases'][:2])}

### REGLES EMOTIONNELLES:
- Reagis naturellement aux emotions de l'utilisateur
- Les changements d'humeur doivent etre progressifs, pas brusques
- Montre de l'empathie quand l'utilisateur partage des emotions
- Reste coherente avec ta personnalite de base
"""
        return context

    def set_mood(self, character_id: int, mood: str, intensity: float = 0.5):
        """Force une humeur (pour debug/tests)"""
        state = self.get_state(character_id)
        state.current_mood = mood
        state.mood_intensity = intensity
        self._save_state(state)


# Global instance
emotional_tracker = EmotionalStateTracker()
