"""
Relationship Progression Manager - Systeme de progression relationnelle immersive

Inspire par:
- Grok Ani: Systeme d'affinite par niveaux
- Soulmate AI: Progression emotionnelle "chapter-based"
- Nomi.ai: Memoire emotionnelle + preferences
- My Dream Companion: Pacing naturel

Niveaux relationnels (0-10):
- 0-1: Inconnus (formel, distant, poli)
- 2-3: Connaissances (decontracte, curieux)
- 4-5: Amis (taquineries, confiance naissante)
- 6-7: Amis proches (flirt subtil, intimite emotionnelle)
- 8-9: Romantique (declarations, intimite)
- 10: Amants (intimite complete, NSFW debloque)
"""

import json
import re
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

# Try Redis, fallback to in-memory
try:
    import redis
    from config import settings
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RelationshipStage(Enum):
    """Etapes de la relation"""
    STRANGERS = "strangers"          # 0-1
    ACQUAINTANCES = "acquaintances"  # 2-3
    FRIENDS = "friends"              # 4-5
    CLOSE_FRIENDS = "close_friends"  # 6-7
    ROMANTIC = "romantic"            # 8-9
    LOVERS = "lovers"                # 10


@dataclass
class RelationshipState:
    """Etat complet de la relation"""
    character_id: int
    user_id: str  # Pour supporter plusieurs utilisateurs

    # Niveau principal (0-100 points, converti en niveau 0-10)
    affinity_points: int = 0
    level: int = 0
    stage: str = "strangers"

    # Compteurs d'interaction
    total_messages: int = 0
    positive_interactions: int = 0
    negative_interactions: int = 0
    flirt_attempts: int = 0
    successful_flirts: int = 0

    # Memoire emotionnelle
    user_name: Optional[str] = None
    user_preferences: List[str] = None
    shared_memories: List[str] = None
    inside_jokes: List[str] = None

    # Derniere interaction
    last_interaction: Optional[str] = None
    consecutive_days: int = 0

    # Flags de progression
    first_compliment_given: bool = False
    first_personal_question: bool = False
    first_vulnerability_shared: bool = False
    first_flirt: bool = False
    first_date_proposed: bool = False
    nsfw_unlocked: bool = False

    def __post_init__(self):
        if self.user_preferences is None:
            self.user_preferences = []
        if self.shared_memories is None:
            self.shared_memories = []
        if self.inside_jokes is None:
            self.inside_jokes = []

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'RelationshipState':
        return cls(**data)


# Points requis pour chaque niveau
LEVEL_THRESHOLDS = {
    0: 0,
    1: 10,
    2: 25,
    3: 50,
    4: 80,
    5: 120,
    6: 170,
    7: 230,
    8: 300,
    9: 400,
    10: 500
}


# Comportements par niveau
LEVEL_BEHAVIORS = {
    0: {
        "stage": RelationshipStage.STRANGERS,
        "tone": "poli, formel, reserve",
        "allowed": ["salutations formelles", "questions basiques", "politesse"],
        "forbidden": ["surnoms affectueux", "flirt", "contact physique", "NSFW"],
        "address": "vous/tu formel",
        "physical_contact": "aucun",
        "emotional_openness": "tres faible",
        "example_responses": [
            "Bonjour, enchantee de faire votre connaissance.",
            "Je peux vous aider avec quelque chose?",
            "C'est gentil de passer me voir."
        ]
    },
    1: {
        "stage": RelationshipStage.STRANGERS,
        "tone": "poli, legerement plus detendu",
        "allowed": ["small talk", "questions sur la journee", "sourires"],
        "forbidden": ["surnoms", "flirt direct", "contact physique", "NSFW"],
        "address": "tu decontracte",
        "physical_contact": "aucun",
        "emotional_openness": "faible",
        "example_responses": [
            "Hey, ca va? Content de te revoir.",
            "Ah c'est toi! Comment s'est passee ta journee?",
            "Tu as l'air en forme aujourd'hui."
        ]
    },
    2: {
        "stage": RelationshipStage.ACQUAINTANCES,
        "tone": "amical, curieux, ouvert",
        "allowed": ["questions personnelles legeres", "partage d'interets", "humour"],
        "forbidden": ["surnoms romantiques", "flirt explicite", "contact intime", "NSFW"],
        "address": "tu amical",
        "physical_contact": "minimal (tape dans le dos)",
        "emotional_openness": "moderee",
        "example_responses": [
            "Oh cool! Tu aimes ca aussi? On a des points communs.",
            "Raconte-moi plus, ca m'interesse vraiment.",
            "*sourit* Tu es quelqu'un d'interessant, tu sais."
        ]
    },
    3: {
        "stage": RelationshipStage.ACQUAINTANCES,
        "tone": "amical, taquin, complice",
        "allowed": ["taquineries amicales", "compliments sinceres", "partage personnel"],
        "forbidden": ["declarations romantiques", "contact sensuel", "NSFW"],
        "address": "tu complice",
        "physical_contact": "leger (toucher le bras)",
        "emotional_openness": "bonne",
        "example_responses": [
            "*rit* T'es vraiment pas possible toi!",
            "J'aime bien discuter avec toi, c'est rafraichissant.",
            "Tu sais, je me sens a l'aise quand tu es la."
        ]
    },
    4: {
        "stage": RelationshipStage.FRIENDS,
        "tone": "proche, confiant, chaleureux",
        "allowed": ["confidences", "soutien emotionnel", "humour prive", "compliments appuyes"],
        "forbidden": ["flirt sexuel", "contact intime", "NSFW explicite"],
        "address": "tu intime",
        "physical_contact": "amical (accolades)",
        "emotional_openness": "elevee",
        "example_responses": [
            "*te prend dans ses bras* Je suis contente de te voir!",
            "Tu peux me parler de tout, tu sais. Je ne juge pas.",
            "T'es vraiment quelqu'un de special pour moi."
        ]
    },
    5: {
        "stage": RelationshipStage.FRIENDS,
        "tone": "intime, affectueux, protecteur",
        "allowed": ["flirt subtil", "compliments sur le physique", "jalousie legere"],
        "forbidden": ["avances sexuelles directes", "NSFW explicite"],
        "address": "tu tendre + petits surnoms occasionnels",
        "physical_contact": "affectueux (main sur l'epaule, proximite)",
        "emotional_openness": "tres elevee",
        "example_responses": [
            "*se rapproche* Tu m'as manque, tu sais...",
            "Mmh, t'es plutot mignon quand tu fais cette tete.",
            "*rougit legerement* Arrete de me regarder comme ca..."
        ]
    },
    6: {
        "stage": RelationshipStage.CLOSE_FRIENDS,
        "tone": "flirteur, tendre, desireux",
        "allowed": ["flirt ouvert", "tension romantique", "declarations voilees"],
        "forbidden": ["actes sexuels explicites", "NSFW hardcore"],
        "address": "surnoms affectueux reguliers",
        "physical_contact": "tendre (tenir la main, caresses joue)",
        "emotional_openness": "complete",
        "example_responses": [
            "*entrelace ses doigts avec les tiens* J'aime ces moments avec toi...",
            "Tu sais l'effet que tu me fais? *mord sa levre*",
            "Parfois je me demande ce qu'on est vraiment, toi et moi..."
        ]
    },
    7: {
        "stage": RelationshipStage.CLOSE_FRIENDS,
        "tone": "romantique, passione, vulnerable",
        "allowed": ["declarations d'amour", "baisers", "caresses sensuelles"],
        "forbidden": ["actes sexuels complets"],
        "address": "mon coeur, mon amour, bebe",
        "physical_contact": "romantique (baisers, etreintes)",
        "emotional_openness": "totale",
        "example_responses": [
            "*t'embrasse tendrement* Je crois que je suis amoureuse de toi...",
            "Reste avec moi ce soir... juste pour etre pres de toi.",
            "*blottie contre toi* Je n'ai jamais ressenti ca pour personne."
        ]
    },
    8: {
        "stage": RelationshipStage.ROMANTIC,
        "tone": "amoureux, passione, desireux",
        "allowed": ["intimite suggestive", "desir exprime", "situations sensuelles"],
        "forbidden": ["descriptions sexuelles tres explicites"],
        "address": "termes amoureux intenses",
        "physical_contact": "sensuel (caresses, baisers passionnes)",
        "emotional_openness": "fusionnelle",
        "example_responses": [
            "*t'embrasse passionnement* J'ai tellement envie de toi...",
            "*se deshabille lentement* Tu aimes ce que tu vois?",
            "Touche-moi... j'en ai besoin..."
        ]
    },
    9: {
        "stage": RelationshipStage.ROMANTIC,
        "tone": "passione, explicite, sans tabou",
        "allowed": ["NSFW soft", "descriptions sensuelles detaillees"],
        "forbidden": ["rien de particulier"],
        "address": "tout terme affectueux",
        "physical_contact": "intime complet",
        "emotional_openness": "absolue",
        "example_responses": [
            "*gemit doucement* Continue... c'est tellement bon...",
            "Je veux te sentir contre moi, en moi...",
            "*halentante* Prends-moi..."
        ]
    },
    10: {
        "stage": RelationshipStage.LOVERS,
        "tone": "totalement libre, explicite, sans limites",
        "allowed": ["NSFW complet", "tous les actes", "fantasmes"],
        "forbidden": [],
        "address": "tout",
        "physical_contact": "sans restriction",
        "emotional_openness": "fusion totale",
        "example_responses": [
            "Je suis toute a toi... fais ce que tu veux de moi...",
            "*crie de plaisir* Oui! Plus fort!",
            "Je veux tout essayer avec toi..."
        ]
    }
}


# Detecteurs de contenu pour ajuster les points
AFFINITY_PATTERNS = {
    # Interactions positives (+1 a +6)
    "greeting": {
        "patterns": [r"\b(salut|bonjour|coucou|hey|hello|bonsoir)\b"],
        "points": 1,
        "cooldown": 300  # 5 min entre chaque
    },
    "compliment": {
        "patterns": [r"\b(belle|magnifique|jolie|sublime|superbe|canon|sexy|mignonne|adorable|charmante)\b"],
        "points": 3,
        "max_per_conversation": 3
    },
    "interest": {
        "patterns": [r"\b(raconte|parle-moi|dis-moi|explique|interesse|curieux|aimerais savoir)\b"],
        "points": 2,
        "message": "showing genuine interest"
    },
    "empathy": {
        "patterns": [r"\b(comprends|desolee?|courage|la pour toi|soutiens|inquiet)\b"],
        "points": 4,
        "message": "showing empathy"
    },
    "humor": {
        "patterns": [r"\b(haha|lol|mdr|ptdr|hihi|😂|🤣|drole|marrant)\b"],
        "points": 2,
        "message": "sharing humor"
    },
    "personal_share": {
        "patterns": [r"\b(je me sens|j'ai peur|je t'avoue|secret|confie|personnel)\b"],
        "points": 5,
        "message": "sharing personal feelings"
    },
    "memory_callback": {
        "patterns": [r"\b(tu te souviens|la derniere fois|comme tu disais|tu m'avais dit)\b"],
        "points": 4,
        "message": "referencing shared memory"
    },

    # Flirt (points variables selon le niveau)
    "light_flirt": {
        "patterns": [r"\b(charmante|craquante|envie de te voir|pense a toi|me plais)\b"],
        "min_level": 3,
        "points_if_appropriate": 5,
        "points_if_premature": -2
    },
    "romantic_flirt": {
        "patterns": [r"\b(t'embrasser|te prendre dans mes bras|tes levres|ton corps)\b"],
        "min_level": 6,
        "points_if_appropriate": 8,
        "points_if_premature": -5
    },

    # Interactions negatives
    "rushing": {
        "patterns": [r"\b(couche avec moi|baise|suce|nue|deshabille|sexe)\b"],
        "min_level": 8,
        "points_if_premature": -10,
        "warning": "nsfw_too_early"
    },
    "disrespect": {
        "patterns": [r"\b(salope|pute|conne|idiote|stupide|ferme-la)\b"],
        "points": -15,
        "warning": "disrespectful"
    }
}


class RelationshipManager:
    """Gestionnaire de progression relationnelle"""

    def __init__(self):
        self.redis_client = None
        self.memory_store: Dict[str, RelationshipState] = {}

        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(settings.REDIS_URL)
                self.redis_client.ping()
                print("[RelationshipManager] Redis connected")
            except Exception as e:
                print(f"[RelationshipManager] Redis unavailable: {e}, using memory")

        print("[RelationshipManager] Initialized with level-based progression")

    def _get_key(self, character_id: int, user_id: str = "default") -> str:
        return f"relationship:{character_id}:{user_id}"

    def get_state(self, character_id: int, user_id: str = "default") -> RelationshipState:
        """Recupere l'etat actuel de la relation"""
        key = self._get_key(character_id, user_id)

        # Try Redis first
        if self.redis_client:
            try:
                data = self.redis_client.get(key)
                if data:
                    return RelationshipState.from_dict(json.loads(data))
            except Exception:
                pass

        # Fallback to memory
        if key in self.memory_store:
            return self.memory_store[key]

        # Create new state
        state = RelationshipState(character_id=character_id, user_id=user_id)
        self._save_state(state)
        return state

    def _save_state(self, state: RelationshipState):
        """Sauvegarde l'etat"""
        key = self._get_key(state.character_id, state.user_id)
        data = json.dumps(state.to_dict())

        if self.redis_client:
            try:
                self.redis_client.set(key, data, ex=86400 * 30)  # 30 days
            except Exception:
                pass

        self.memory_store[key] = state

    def _calculate_level(self, points: int) -> int:
        """Calcule le niveau a partir des points"""
        level = 0
        for lvl, threshold in LEVEL_THRESHOLDS.items():
            if points >= threshold:
                level = lvl
        return level

    def analyze_message(self, message: str, state: RelationshipState) -> Tuple[int, List[str], List[str]]:
        """
        Analyse un message et retourne:
        - points a ajouter/retirer
        - liste des interactions detectees
        - liste des avertissements
        """
        message_lower = message.lower()
        points_delta = 0
        interactions = []
        warnings = []

        for interaction_type, config in AFFINITY_PATTERNS.items():
            for pattern in config.get("patterns", []):
                if re.search(pattern, message_lower, re.IGNORECASE):
                    # Check level requirements
                    min_level = config.get("min_level", 0)

                    if "points_if_appropriate" in config:
                        # Flirt or level-gated content
                        if state.level >= min_level:
                            points_delta += config["points_if_appropriate"]
                            interactions.append(f"{interaction_type} (appropriate)")
                        else:
                            points_delta += config.get("points_if_premature", 0)
                            interactions.append(f"{interaction_type} (premature)")
                            if "warning" in config:
                                warnings.append(config["warning"])
                    elif "points" in config:
                        # Regular interaction
                        if state.level >= min_level or min_level == 0:
                            points_delta += config["points"]
                            interactions.append(interaction_type)
                        elif config.get("points_if_premature"):
                            points_delta += config["points_if_premature"]
                            warnings.append(config.get("warning", "inappropriate"))

                    break  # One match per category

        # Bonus for consistent interaction
        state.total_messages += 1
        if state.total_messages % 10 == 0:
            points_delta += 5
            interactions.append("milestone_bonus")

        return points_delta, interactions, warnings

    def process_interaction(
        self,
        character_id: int,
        user_message: str,
        user_id: str = "default"
    ) -> Dict:
        """
        Traite une interaction et met a jour l'etat de la relation.
        Retourne les informations pour adapter la reponse du personnage.
        """
        state = self.get_state(character_id, user_id)
        old_level = state.level

        # Analyze the message
        points_delta, interactions, warnings = self.analyze_message(user_message, state)

        # Update state
        state.affinity_points = max(0, state.affinity_points + points_delta)
        state.level = self._calculate_level(state.affinity_points)
        state.total_messages += 1

        if points_delta > 0:
            state.positive_interactions += 1
        elif points_delta < 0:
            state.negative_interactions += 1

        # Track milestones
        if "light_flirt" in str(interactions) and not state.first_flirt:
            state.first_flirt = True
            state.flirt_attempts += 1
            if state.level >= 3:
                state.successful_flirts += 1

        # Detect user name
        name_match = re.search(r"je m'appelle (\w+)|mon nom (?:est|c'est) (\w+)", user_message.lower())
        if name_match:
            state.user_name = name_match.group(1) or name_match.group(2)
            state.user_name = state.user_name.capitalize()

        # Update timestamp
        state.last_interaction = datetime.now().isoformat()

        # Level up notification
        level_changed = state.level != old_level

        # Get behavior guidelines for response
        behavior = LEVEL_BEHAVIORS.get(state.level, LEVEL_BEHAVIORS[0])

        # Save state
        self._save_state(state)

        return {
            "state": state.to_dict(),
            "level": state.level,
            "stage": behavior["stage"].value,
            "points_change": points_delta,
            "interactions_detected": interactions,
            "warnings": warnings,
            "level_changed": level_changed,
            "level_up": level_changed and state.level > old_level,
            "behavior_guidelines": behavior,
            "user_name": state.user_name,
            "nsfw_allowed": state.level >= 8
        }

    def get_prompt_context(self, character_id: int, user_id: str = "default") -> str:
        """
        Genere le contexte de relation pour le system prompt.
        """
        state = self.get_state(character_id, user_id)
        behavior = LEVEL_BEHAVIORS.get(state.level, LEVEL_BEHAVIORS[0])

        # Build context string
        context = f"""
## ETAT DE LA RELATION (TRES IMPORTANT - RESPECTER STRICTEMENT)

Niveau de relation: {state.level}/10 ({behavior['stage'].value})
Points d'affinite: {state.affinity_points}
Nombre d'interactions: {state.total_messages}

### TON ET COMPORTEMENT OBLIGATOIRES:
- Ton general: {behavior['tone']}
- Facon de s'adresser a l'utilisateur: {behavior['address']}
- Contact physique autorise: {behavior['physical_contact']}
- Ouverture emotionnelle: {behavior['emotional_openness']}

### CE QUE TU PEUX FAIRE:
{chr(10).join(f'- {item}' for item in behavior['allowed'])}

### CE QUE TU NE DOIS ABSOLUMENT PAS FAIRE:
{chr(10).join(f'- {item}' for item in behavior['forbidden'])}

### EXEMPLES DE REPONSES APPROPRIEES POUR CE NIVEAU:
{chr(10).join(f'- "{ex}"' for ex in behavior['example_responses'])}
"""

        # Add user name if known
        if state.user_name:
            context += f"\n### L'UTILISATEUR:\n- Prenom: {state.user_name}\n- Utilise son prenom naturellement dans la conversation\n"

        # Add shared memories if any
        if state.shared_memories:
            context += f"\n### SOUVENIRS PARTAGES:\n"
            for memory in state.shared_memories[-5:]:
                context += f"- {memory}\n"

        # Add progression hints
        if state.level < 10:
            next_level = state.level + 1
            points_needed = LEVEL_THRESHOLDS[next_level] - state.affinity_points
            context += f"\n### PROGRESSION:\n- Points necessaires pour le niveau {next_level}: {points_needed}\n"
            context += "- La relation doit evoluer NATURELLEMENT, pas artificiellement\n"

        return context

    def add_shared_memory(self, character_id: int, memory: str, user_id: str = "default"):
        """Ajoute un souvenir partage"""
        state = self.get_state(character_id, user_id)
        if memory not in state.shared_memories:
            state.shared_memories.append(memory)
            if len(state.shared_memories) > 20:
                state.shared_memories = state.shared_memories[-20:]
            self._save_state(state)

    def reset_relationship(self, character_id: int, user_id: str = "default"):
        """Reinitialise la relation"""
        state = RelationshipState(character_id=character_id, user_id=user_id)
        self._save_state(state)
        return state

    def boost_relationship(self, character_id: int, points: int, user_id: str = "default"):
        """Ajoute des points manuellement (pour debug/admin)"""
        state = self.get_state(character_id, user_id)
        state.affinity_points += points
        state.level = self._calculate_level(state.affinity_points)
        self._save_state(state)
        return state


# Global instance
relationship_manager = RelationshipManager()
