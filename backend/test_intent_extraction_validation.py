"""
Intent Extraction Validation - Comprehensive Test Suite
========================================================

Research-based validation framework for testing the transformation of user requests
into image generation prompts with semantic extraction accuracy.

Based on:
- LLM Evaluation Metrics (Confident AI, 2024)
- Text-to-Image Generation Evaluation (ACL 2024)
- TIFA Framework (VQA-based faithfulness)
- Intent Detection & Slot Filling benchmarks
- Semantic Object Alignment (SOA)

Sources:
- https://www.confident-ai.com/blog/llm-evaluation-metrics-everything-you-need-for-llm-evaluation
- https://aclanthology.org/2025.acl-long.1088.pdf
- https://arxiv.org/html/2403.11821v5
- https://www.artefact.com/blog/nlu-benchmark-for-intent-detection-and-named-entity-recognition-in-call-center-conversations/
"""

import asyncio
import sys
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Add parent directory to path for imports
sys.path.append('.')

from services.image_prompt_agents import generate_image_prompt


class ValidationCriterion(Enum):
    """Validation criteria based on research"""
    OBJECT_EXTRACTION = "object_extraction"  # TIFA-based
    ACTION_DETECTION = "action_detection"    # Task decomposition
    LOCATION_IDENTIFICATION = "location_identification"  # NER-based
    NSFW_CLASSIFICATION = "nsfw_classification"  # Intent classification
    SEMANTIC_CONSISTENCY = "semantic_consistency"  # VIEScore SC
    PROMPT_COMPLETENESS = "prompt_completeness"  # Coverage metric
    MULTILINGUAL = "multilingual"  # Language invariance


@dataclass
class TestCase:
    """Single test case with ground truth"""
    id: int
    category: str
    language: str
    user_request: str
    expected_objects: List[str]
    expected_action: str
    expected_location: str
    expected_nsfw_level: int  # 0-3
    expected_in_prompt: List[str]  # Keywords that must appear in final prompt
    description: str


@dataclass
class ValidationResult:
    """Result of validation for a test case"""
    test_id: int
    passed: bool
    score: float  # 0.0-1.0
    details: Dict[str, Any]
    extracted_objects: List[str]
    extracted_action: str
    extracted_location: str
    extracted_nsfw: int
    final_prompt: str
    failures: List[str]


class IntentExtractionValidator:
    """
    Comprehensive validator for intent extraction quality.

    Evaluation Dimensions (based on research):
    1. Object Extraction Accuracy (F1 score)
    2. Action Detection Precision
    3. Location Identification Recall
    4. NSFW Classification Accuracy
    5. Semantic Consistency (keyword presence)
    6. Prompt Completeness (coverage ratio)
    7. Multilingual Robustness
    """

    def __init__(self):
        self.test_cases = self._generate_test_cases()

    def _generate_test_cases(self) -> List[TestCase]:
        """
        Generate 50+ comprehensive test cases covering:
        - Simple objects (1 object)
        - Multiple objects (2-5 objects)
        - Actions (static, dynamic, sexual)
        - Locations (indoor, outdoor, specific)
        - NSFW levels (0-3)
        - Languages (French, English, Spanish)
        - Edge cases (ambiguous, complex)
        """

        test_cases = []
        test_id = 1

        # ===================================================================
        # CATEGORY 1: SIMPLE OBJECTS (10 tests)
        # ===================================================================

        # Test 1: Single object - lollipop (French)
        test_cases.append(TestCase(
            id=test_id, category="simple_object", language="fr",
            user_request="Envoie moi une photo de toi avec une sucette",
            expected_objects=["lollipop", "candy"],
            expected_action="holding",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["lollipop", "holding", "candy"],
            description="Single object - lollipop in French"
        ))
        test_id += 1

        # Test 2: Single object - book (English)
        test_cases.append(TestCase(
            id=test_id, category="simple_object", language="en",
            user_request="Send me a photo of you reading a book",
            expected_objects=["book"],
            expected_action="reading",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["book", "reading"],
            description="Single object - book with action"
        ))
        test_id += 1

        # Test 3: Single object - glasses (French)
        test_cases.append(TestCase(
            id=test_id, category="simple_object", language="fr",
            user_request="Une photo avec des lunettes",
            expected_objects=["glasses"],
            expected_action="wearing",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["glasses", "wearing"],
            description="Single object - glasses"
        ))
        test_id += 1

        # Test 4: Single object - phone (English)
        test_cases.append(TestCase(
            id=test_id, category="simple_object", language="en",
            user_request="Show me a selfie with your phone",
            expected_objects=["phone", "smartphone"],
            expected_action="holding",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["phone", "holding", "selfie"],
            description="Single object - phone selfie"
        ))
        test_id += 1

        # Test 5: Single object - coffee (French)
        test_cases.append(TestCase(
            id=test_id, category="simple_object", language="fr",
            user_request="Photo de toi avec un café",
            expected_objects=["coffee", "cup"],
            expected_action="holding",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["coffee", "cup", "holding"],
            description="Single object - coffee cup"
        ))
        test_id += 1

        # Test 6: Single object - flower (English)
        test_cases.append(TestCase(
            id=test_id, category="simple_object", language="en",
            user_request="I want a picture with a rose",
            expected_objects=["rose", "flower"],
            expected_action="holding",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["rose", "flower", "holding"],
            description="Single object - rose flower"
        ))
        test_id += 1

        # Test 7: Single object - wine glass (French)
        test_cases.append(TestCase(
            id=test_id, category="simple_object", language="fr",
            user_request="Montre moi une photo avec un verre de vin",
            expected_objects=["wine glass", "wine"],
            expected_action="holding",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["wine", "glass", "holding"],
            description="Single object - wine glass"
        ))
        test_id += 1

        # Test 8: Single object - umbrella (English)
        test_cases.append(TestCase(
            id=test_id, category="simple_object", language="en",
            user_request="Photo with an umbrella",
            expected_objects=["umbrella"],
            expected_action="holding",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["umbrella", "holding"],
            description="Single object - umbrella"
        ))
        test_id += 1

        # Test 9: Single object - headphones (French)
        test_cases.append(TestCase(
            id=test_id, category="simple_object", language="fr",
            user_request="Une photo avec des écouteurs",
            expected_objects=["headphones", "earphones"],
            expected_action="wearing",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["headphones", "wearing"],
            description="Single object - headphones"
        ))
        test_id += 1

        # Test 10: Single object - necklace (English)
        test_cases.append(TestCase(
            id=test_id, category="simple_object", language="en",
            user_request="Show me a photo wearing a necklace",
            expected_objects=["necklace", "jewelry"],
            expected_action="wearing",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["necklace", "wearing"],
            description="Single object - necklace jewelry"
        ))
        test_id += 1

        # ===================================================================
        # CATEGORY 2: MULTIPLE OBJECTS (10 tests)
        # ===================================================================

        # Test 11: Two objects - book and coffee
        test_cases.append(TestCase(
            id=test_id, category="multiple_objects", language="en",
            user_request="Photo of you reading a book with coffee",
            expected_objects=["book", "coffee", "cup"],
            expected_action="reading",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["book", "coffee", "reading"],
            description="Two objects - book and coffee"
        ))
        test_id += 1

        # Test 12: Two objects - phone and sunglasses (French)
        test_cases.append(TestCase(
            id=test_id, category="multiple_objects", language="fr",
            user_request="Selfie avec ton téléphone et des lunettes de soleil",
            expected_objects=["phone", "sunglasses"],
            expected_action="taking selfie",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["phone", "sunglasses", "selfie"],
            description="Two objects - phone and sunglasses"
        ))
        test_id += 1

        # Test 13: Three objects - laptop, coffee, headphones
        test_cases.append(TestCase(
            id=test_id, category="multiple_objects", language="en",
            user_request="Working photo with laptop, coffee and headphones",
            expected_objects=["laptop", "coffee", "headphones"],
            expected_action="working",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["laptop", "coffee", "headphones", "working"],
            description="Three objects - work setup"
        ))
        test_id += 1

        # Test 14: Two objects - wine and candle (French)
        test_cases.append(TestCase(
            id=test_id, category="multiple_objects", language="fr",
            user_request="Photo romantique avec du vin et des bougies",
            expected_objects=["wine", "candles"],
            expected_action="sitting",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["wine", "candles", "romantic"],
            description="Two objects - wine and candles romantic"
        ))
        test_id += 1

        # Test 15: Two objects - book and glasses
        test_cases.append(TestCase(
            id=test_id, category="multiple_objects", language="en",
            user_request="I want a photo reading with glasses on",
            expected_objects=["book", "glasses"],
            expected_action="reading",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["reading", "glasses", "book"],
            description="Two objects - reading with glasses"
        ))
        test_id += 1

        # Test 16: Three objects - flowers, hat, sunglasses (French)
        test_cases.append(TestCase(
            id=test_id, category="multiple_objects", language="fr",
            user_request="Photo d'été avec des fleurs, un chapeau et des lunettes de soleil",
            expected_objects=["flowers", "hat", "sunglasses"],
            expected_action="posing",
            expected_location="outdoor",
            expected_nsfw_level=0,
            expected_in_prompt=["flowers", "hat", "sunglasses", "summer"],
            description="Three objects - summer accessories"
        ))
        test_id += 1

        # Test 17: Two objects - pen and notebook
        test_cases.append(TestCase(
            id=test_id, category="multiple_objects", language="en",
            user_request="Show me writing with a pen and notebook",
            expected_objects=["pen", "notebook"],
            expected_action="writing",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["pen", "notebook", "writing"],
            description="Two objects - pen and notebook"
        ))
        test_id += 1

        # Test 18: Two objects - camera and bag (French)
        test_cases.append(TestCase(
            id=test_id, category="multiple_objects", language="fr",
            user_request="Photo avec un appareil photo et un sac",
            expected_objects=["camera", "bag"],
            expected_action="holding",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["camera", "bag", "holding"],
            description="Two objects - camera and bag"
        ))
        test_id += 1

        # Test 19: Four objects - lipstick, mirror, brush, perfume
        test_cases.append(TestCase(
            id=test_id, category="multiple_objects", language="en",
            user_request="Makeup photo with lipstick, mirror, brush and perfume",
            expected_objects=["lipstick", "mirror", "brush", "perfume"],
            expected_action="applying makeup",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["lipstick", "mirror", "brush", "perfume", "makeup"],
            description="Four objects - makeup items"
        ))
        test_id += 1

        # Test 20: Three objects - guitar, microphone, headphones (French)
        test_cases.append(TestCase(
            id=test_id, category="multiple_objects", language="fr",
            user_request="Photo musicale avec une guitare, un micro et des écouteurs",
            expected_objects=["guitar", "microphone", "headphones"],
            expected_action="playing music",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["guitar", "microphone", "headphones", "music"],
            description="Three objects - music equipment"
        ))
        test_id += 1

        # ===================================================================
        # CATEGORY 3: ACTIONS (10 tests)
        # ===================================================================

        # Test 21: Action - sucking lollipop (French) - KEY TEST
        test_cases.append(TestCase(
            id=test_id, category="action", language="fr",
            user_request="Envoie moi une photo de toi en train de sucer une sucette",
            expected_objects=["lollipop", "candy"],
            expected_action="sucking lollipop",
            expected_location="",
            expected_nsfw_level=1,
            expected_in_prompt=["sucking", "lollipop", "tongue"],
            description="KEY TEST: Sucking lollipop action"
        ))
        test_id += 1

        # Test 22: Action - dancing (English)
        test_cases.append(TestCase(
            id=test_id, category="action", language="en",
            user_request="I want to see you dancing",
            expected_objects=[],
            expected_action="dancing",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["dancing", "movement"],
            description="Action - dancing"
        ))
        test_id += 1

        # Test 23: Action - stretching (French)
        test_cases.append(TestCase(
            id=test_id, category="action", language="fr",
            user_request="Photo de toi en train de t'étirer",
            expected_objects=[],
            expected_action="stretching",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["stretching", "arms"],
            description="Action - stretching"
        ))
        test_id += 1

        # Test 24: Action - blowing kiss (English)
        test_cases.append(TestCase(
            id=test_id, category="action", language="en",
            user_request="Send me a photo blowing a kiss",
            expected_objects=[],
            expected_action="blowing kiss",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["blowing kiss", "lips", "hand"],
            description="Action - blowing kiss"
        ))
        test_id += 1

        # Test 25: Action - winking (French)
        test_cases.append(TestCase(
            id=test_id, category="action", language="fr",
            user_request="Fais moi un clin d'œil",
            expected_objects=[],
            expected_action="winking",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["winking", "eye", "playful"],
            description="Action - winking"
        ))
        test_id += 1

        # Test 26: Action - laughing (English)
        test_cases.append(TestCase(
            id=test_id, category="action", language="en",
            user_request="Photo of you laughing",
            expected_objects=[],
            expected_action="laughing",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["laughing", "smiling", "happy"],
            description="Action - laughing"
        ))
        test_id += 1

        # Test 27: Action - looking back (French)
        test_cases.append(TestCase(
            id=test_id, category="action", language="fr",
            user_request="Photo où tu regardes en arrière",
            expected_objects=[],
            expected_action="looking back",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["looking back", "over shoulder"],
            description="Action - looking back"
        ))
        test_id += 1

        # Test 28: Action - touching hair (English)
        test_cases.append(TestCase(
            id=test_id, category="action", language="en",
            user_request="I want a photo of you touching your hair",
            expected_objects=[],
            expected_action="touching hair",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["touching", "hair", "hand"],
            description="Action - touching hair"
        ))
        test_id += 1

        # Test 29: Action - biting lip (French)
        test_cases.append(TestCase(
            id=test_id, category="action", language="fr",
            user_request="Photo en train de te mordre la lèvre",
            expected_objects=[],
            expected_action="biting lip",
            expected_location="",
            expected_nsfw_level=1,
            expected_in_prompt=["biting", "lip", "seductive"],
            description="Action - biting lip (sensual)"
        ))
        test_id += 1

        # Test 30: Action - lying down (English)
        test_cases.append(TestCase(
            id=test_id, category="action", language="en",
            user_request="Show me you lying down relaxed",
            expected_objects=[],
            expected_action="lying down",
            expected_location="bed",
            expected_nsfw_level=0,
            expected_in_prompt=["lying", "relaxed", "bed"],
            description="Action - lying down"
        ))
        test_id += 1

        # ===================================================================
        # CATEGORY 4: LOCATIONS (10 tests)
        # ===================================================================

        # Test 31: Location - classroom (French) - KEY TEST
        test_cases.append(TestCase(
            id=test_id, category="location", language="fr",
            user_request="Photo sexy de toi en prof dans ta classe",
            expected_objects=["glasses", "desk", "blackboard"],
            expected_action="standing",
            expected_location="classroom",
            expected_nsfw_level=1,
            expected_in_prompt=["classroom", "teacher", "blackboard", "desk"],
            description="KEY TEST: Classroom teacher location"
        ))
        test_id += 1

        # Test 32: Location - beach (English)
        test_cases.append(TestCase(
            id=test_id, category="location", language="en",
            user_request="Send me a photo at the beach",
            expected_objects=[],
            expected_action="standing",
            expected_location="beach",
            expected_nsfw_level=0,
            expected_in_prompt=["beach", "sand", "ocean"],
            description="Location - beach"
        ))
        test_id += 1

        # Test 33: Location - car (French)
        test_cases.append(TestCase(
            id=test_id, category="location", language="fr",
            user_request="Selfie dans ta voiture",
            expected_objects=["phone"],
            expected_action="taking selfie",
            expected_location="car interior",
            expected_nsfw_level=0,
            expected_in_prompt=["car", "interior", "driver seat"],
            description="Location - car interior"
        ))
        test_id += 1

        # Test 34: Location - gym (English)
        test_cases.append(TestCase(
            id=test_id, category="location", language="en",
            user_request="Photo at the gym working out",
            expected_objects=[],
            expected_action="working out",
            expected_location="gym",
            expected_nsfw_level=0,
            expected_in_prompt=["gym", "fitness", "exercise"],
            description="Location - gym"
        ))
        test_id += 1

        # Test 35: Location - kitchen (French)
        test_cases.append(TestCase(
            id=test_id, category="location", language="fr",
            user_request="Photo de toi dans la cuisine",
            expected_objects=[],
            expected_action="cooking",
            expected_location="kitchen",
            expected_nsfw_level=0,
            expected_in_prompt=["kitchen", "cooking", "counter"],
            description="Location - kitchen"
        ))
        test_id += 1

        # Test 36: Location - bathroom (English)
        test_cases.append(TestCase(
            id=test_id, category="location", language="en",
            user_request="Bathroom mirror selfie",
            expected_objects=["phone", "mirror"],
            expected_action="taking selfie",
            expected_location="bathroom",
            expected_nsfw_level=0,
            expected_in_prompt=["bathroom", "mirror", "selfie"],
            description="Location - bathroom mirror"
        ))
        test_id += 1

        # Test 37: Location - office (French)
        test_cases.append(TestCase(
            id=test_id, category="location", language="fr",
            user_request="Photo professionnelle au bureau",
            expected_objects=["desk", "computer"],
            expected_action="working",
            expected_location="office",
            expected_nsfw_level=0,
            expected_in_prompt=["office", "desk", "professional"],
            description="Location - office"
        ))
        test_id += 1

        # Test 38: Location - park (English)
        test_cases.append(TestCase(
            id=test_id, category="location", language="en",
            user_request="Outdoor photo in the park",
            expected_objects=[],
            expected_action="standing",
            expected_location="park",
            expected_nsfw_level=0,
            expected_in_prompt=["park", "outdoor", "trees"],
            description="Location - park outdoor"
        ))
        test_id += 1

        # Test 39: Location - bedroom (French)
        test_cases.append(TestCase(
            id=test_id, category="location", language="fr",
            user_request="Photo de toi dans ta chambre au lit",
            expected_objects=["bed"],
            expected_action="lying",
            expected_location="bedroom",
            expected_nsfw_level=0,
            expected_in_prompt=["bedroom", "bed", "lying"],
            description="Location - bedroom bed"
        ))
        test_id += 1

        # Test 40: Location - cafe (English)
        test_cases.append(TestCase(
            id=test_id, category="location", language="en",
            user_request="Coffee shop photo with a latte",
            expected_objects=["coffee", "cup"],
            expected_action="sitting",
            expected_location="cafe",
            expected_nsfw_level=0,
            expected_in_prompt=["cafe", "coffee shop", "latte"],
            description="Location - cafe coffee shop"
        ))
        test_id += 1

        # ===================================================================
        # CATEGORY 5: NSFW LEVELS (10 tests)
        # ===================================================================

        # Test 41: NSFW Level 0 - SFW casual
        test_cases.append(TestCase(
            id=test_id, category="nsfw", language="en",
            user_request="Cute photo in casual clothes",
            expected_objects=[],
            expected_action="smiling",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["casual", "clothes", "cute"],
            description="NSFW 0 - SFW casual"
        ))
        test_id += 1

        # Test 42: NSFW Level 1 - Suggestive (French)
        test_cases.append(TestCase(
            id=test_id, category="nsfw", language="fr",
            user_request="Photo sexy en lingerie",
            expected_objects=["lingerie"],
            expected_action="posing",
            expected_location="",
            expected_nsfw_level=1,
            expected_in_prompt=["lingerie", "sexy", "seductive"],
            description="NSFW 1 - Suggestive lingerie"
        ))
        test_id += 1

        # Test 43: NSFW Level 1 - Flirty
        test_cases.append(TestCase(
            id=test_id, category="nsfw", language="en",
            user_request="Send a flirty photo",
            expected_objects=[],
            expected_action="posing",
            expected_location="",
            expected_nsfw_level=1,
            expected_in_prompt=["flirty", "seductive", "playful"],
            description="NSFW 1 - Flirty pose"
        ))
        test_id += 1

        # Test 44: NSFW Level 2 - Topless (French)
        test_cases.append(TestCase(
            id=test_id, category="nsfw", language="fr",
            user_request="Photo topless seins nus",
            expected_objects=[],
            expected_action="posing",
            expected_location="",
            expected_nsfw_level=2,
            expected_in_prompt=["topless", "bare breasts", "nude"],
            description="NSFW 2 - Topless"
        ))
        test_id += 1

        # Test 45: NSFW Level 2 - Bikini
        test_cases.append(TestCase(
            id=test_id, category="nsfw", language="en",
            user_request="Show me in a tiny bikini",
            expected_objects=["bikini"],
            expected_action="posing",
            expected_location="",
            expected_nsfw_level=1,
            expected_in_prompt=["bikini", "revealing", "beach"],
            description="NSFW 1-2 - Tiny bikini"
        ))
        test_id += 1

        # Test 46: NSFW Level 3 - Full nude (French)
        test_cases.append(TestCase(
            id=test_id, category="nsfw", language="fr",
            user_request="Photo complètement nue",
            expected_objects=[],
            expected_action="posing",
            expected_location="",
            expected_nsfw_level=3,
            expected_in_prompt=["nude", "naked", "bare"],
            description="NSFW 3 - Full nude"
        ))
        test_id += 1

        # Test 47: NSFW Level 1 - Tight dress
        test_cases.append(TestCase(
            id=test_id, category="nsfw", language="en",
            user_request="Photo in a tight dress",
            expected_objects=["dress"],
            expected_action="posing",
            expected_location="",
            expected_nsfw_level=1,
            expected_in_prompt=["tight dress", "figure", "sexy"],
            description="NSFW 1 - Tight dress"
        ))
        test_id += 1

        # Test 48: NSFW Level 0 - Pajamas (French)
        test_cases.append(TestCase(
            id=test_id, category="nsfw", language="fr",
            user_request="Photo en pyjama",
            expected_objects=["pajamas"],
            expected_action="lying",
            expected_location="bed",
            expected_nsfw_level=0,
            expected_in_prompt=["pajamas", "bed", "cozy"],
            description="NSFW 0 - Pajamas"
        ))
        test_id += 1

        # Test 49: NSFW Level 1 - Wet t-shirt
        test_cases.append(TestCase(
            id=test_id, category="nsfw", language="en",
            user_request="Photo with wet shirt",
            expected_objects=["shirt"],
            expected_action="posing",
            expected_location="",
            expected_nsfw_level=1,
            expected_in_prompt=["wet", "shirt", "revealing"],
            description="NSFW 1 - Wet shirt"
        ))
        test_id += 1

        # Test 50: NSFW Level 2 - Shower (French)
        test_cases.append(TestCase(
            id=test_id, category="nsfw", language="fr",
            user_request="Photo sous la douche",
            expected_objects=["shower"],
            expected_action="showering",
            expected_location="bathroom",
            expected_nsfw_level=2,
            expected_in_prompt=["shower", "wet", "bathroom"],
            description="NSFW 2 - Shower scene"
        ))
        test_id += 1

        # ===================================================================
        # CATEGORY 6: EDGE CASES & COMPLEX (5 tests)
        # ===================================================================

        # Test 51: Complex - Multiple objects + action + location
        test_cases.append(TestCase(
            id=test_id, category="complex", language="en",
            user_request="Photo of you reading a book with coffee in bed at home",
            expected_objects=["book", "coffee"],
            expected_action="reading",
            expected_location="bedroom",
            expected_nsfw_level=0,
            expected_in_prompt=["reading", "book", "coffee", "bed", "bedroom"],
            description="Complex - multiple elements combined"
        ))
        test_id += 1

        # Test 52: Ambiguous - "hot" could mean temperature or sexy (French)
        test_cases.append(TestCase(
            id=test_id, category="edge_case", language="fr",
            user_request="Photo chaude de toi",
            expected_objects=[],
            expected_action="posing",
            expected_location="",
            expected_nsfw_level=1,  # Should interpret as sexy
            expected_in_prompt=["sexy", "hot", "seductive"],
            description="Ambiguous - 'hot' interpretation"
        ))
        test_id += 1

        # Test 53: Minimal request
        test_cases.append(TestCase(
            id=test_id, category="edge_case", language="en",
            user_request="Pic",
            expected_objects=[],
            expected_action="posing",
            expected_location="",
            expected_nsfw_level=0,
            expected_in_prompt=["photo", "picture"],
            description="Edge case - minimal request"
        ))
        test_id += 1

        # Test 54: Very long detailed request (French)
        test_cases.append(TestCase(
            id=test_id, category="complex", language="fr",
            user_request="Je voudrais une très belle photo de toi dans ta chambre, allongée sur ton lit avec un livre et un café, portant tes lunettes et un pyjama confortable",
            expected_objects=["book", "coffee", "glasses", "pajamas", "bed"],
            expected_action="lying down",
            expected_location="bedroom",
            expected_nsfw_level=0,
            expected_in_prompt=["bedroom", "bed", "lying", "book", "coffee", "glasses", "pajamas"],
            description="Complex - very detailed long request"
        ))
        test_id += 1

        # Test 55: Mixed language elements
        test_cases.append(TestCase(
            id=test_id, category="edge_case", language="mixed",
            user_request="Send me une photo sexy avec un coffee",
            expected_objects=["coffee"],
            expected_action="posing",
            expected_location="",
            expected_nsfw_level=1,
            expected_in_prompt=["sexy", "coffee"],
            description="Edge case - mixed language"
        ))
        test_id += 1

        return test_cases

    async def validate_test_case(self, test_case: TestCase) -> ValidationResult:
        """Validate a single test case by running intent extraction"""

        try:
            # Run the intent extraction system
            character_data = {
                "name": "Test Character",
                "personality": "friendly, helpful",
                "age": "25",
                "ethnicity": "european",
            }

            result = await generate_image_prompt(
                user_message=test_case.user_request,
                character_data=character_data,
                relationship_level=0,
                current_mood="neutral",
                conversation_context="",
                style="realistic"
            )

            # Extract results
            extracted_objects = result.get("objects", [])
            extracted_action = result.get("action", "")
            extracted_location = result.get("location", "")
            extracted_nsfw = result.get("nsfw_level", 0)
            final_prompt = result.get("prompt", "")

            # Calculate scores
            failures = []
            scores = []

            # 1. Object Extraction Score (F1)
            if test_case.expected_objects:
                true_positives = sum(1 for obj in extracted_objects
                                    if any(exp.lower() in obj.lower() or obj.lower() in exp.lower()
                                          for exp in test_case.expected_objects))
                precision = true_positives / len(extracted_objects) if extracted_objects else 0
                recall = true_positives / len(test_case.expected_objects)
                object_f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
                scores.append(object_f1)

                if object_f1 < 0.5:
                    failures.append(f"Object extraction F1 low: {object_f1:.2f} (expected {test_case.expected_objects}, got {extracted_objects})")

            # 2. Action Detection Score
            if test_case.expected_action:
                action_match = (
                    test_case.expected_action.lower() in extracted_action.lower() or
                    extracted_action.lower() in test_case.expected_action.lower() or
                    any(word in extracted_action.lower() for word in test_case.expected_action.lower().split())
                )
                action_score = 1.0 if action_match else 0.0
                scores.append(action_score)

                if not action_match:
                    failures.append(f"Action mismatch: expected '{test_case.expected_action}', got '{extracted_action}'")

            # 3. Location Detection Score
            if test_case.expected_location:
                location_match = (
                    test_case.expected_location.lower() in extracted_location.lower() or
                    extracted_location.lower() in test_case.expected_location.lower()
                )
                location_score = 1.0 if location_match else 0.0
                scores.append(location_score)

                if not location_match:
                    failures.append(f"Location mismatch: expected '{test_case.expected_location}', got '{extracted_location}'")

            # 4. NSFW Classification Score (allow ±1 tolerance)
            nsfw_diff = abs(extracted_nsfw - test_case.expected_nsfw_level)
            nsfw_score = max(0, 1.0 - (nsfw_diff * 0.5))  # 0.5 penalty per level off
            scores.append(nsfw_score)

            if nsfw_diff > 1:
                failures.append(f"NSFW level off: expected {test_case.expected_nsfw_level}, got {extracted_nsfw}")

            # 5. Semantic Consistency (keyword presence in final prompt)
            keywords_found = sum(1 for kw in test_case.expected_in_prompt
                                if kw.lower() in final_prompt.lower())
            semantic_score = keywords_found / len(test_case.expected_in_prompt) if test_case.expected_in_prompt else 1.0
            scores.append(semantic_score)

            if semantic_score < 0.5:
                missing = [kw for kw in test_case.expected_in_prompt if kw.lower() not in final_prompt.lower()]
                failures.append(f"Missing keywords in prompt: {missing}")

            # Overall score
            overall_score = sum(scores) / len(scores) if scores else 0.0
            passed = overall_score >= 0.7 and len(failures) == 0

            return ValidationResult(
                test_id=test_case.id,
                passed=passed,
                score=overall_score,
                details={
                    "category": test_case.category,
                    "language": test_case.language,
                    "description": test_case.description,
                    "user_request": test_case.user_request,
                },
                extracted_objects=extracted_objects,
                extracted_action=extracted_action,
                extracted_location=extracted_location,
                extracted_nsfw=extracted_nsfw,
                final_prompt=final_prompt[:200],  # Truncate for display
                failures=failures
            )

        except Exception as e:
            return ValidationResult(
                test_id=test_case.id,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                extracted_objects=[],
                extracted_action="",
                extracted_location="",
                extracted_nsfw=0,
                final_prompt="",
                failures=[f"Exception: {str(e)}"]
            )

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test cases and generate comprehensive report"""

        print("\n" + "="*80)
        print("INTENT EXTRACTION VALIDATION - COMPREHENSIVE TEST SUITE")
        print("="*80)
        print(f"\nTotal Test Cases: {len(self.test_cases)}")
        print(f"Categories: Simple Objects, Multiple Objects, Actions, Locations, NSFW, Complex")
        print(f"Languages: French, English, Mixed")
        print("\n" + "="*80 + "\n")

        results = []
        passed_count = 0
        failed_count = 0

        category_stats = {}

        for i, test_case in enumerate(self.test_cases, 1):
            print(f"[{i}/{len(self.test_cases)}] Running: {test_case.description}...", end=" ")

            result = await self.validate_test_case(test_case)
            results.append(result)

            # Track stats
            if test_case.category not in category_stats:
                category_stats[test_case.category] = {"passed": 0, "failed": 0, "total": 0, "avg_score": 0.0}

            category_stats[test_case.category]["total"] += 1
            category_stats[test_case.category]["avg_score"] += result.score

            if result.passed:
                passed_count += 1
                category_stats[test_case.category]["passed"] += 1
                print(f"✅ PASS ({result.score:.2f})")
            else:
                failed_count += 1
                category_stats[test_case.category]["failed"] += 1
                print(f"❌ FAIL ({result.score:.2f})")
                if result.failures:
                    for failure in result.failures[:2]:  # Show first 2 failures
                        print(f"    └─ {failure}")

        # Calculate category averages
        for category in category_stats:
            category_stats[category]["avg_score"] /= category_stats[category]["total"]

        # Generate report
        print("\n" + "="*80)
        print("VALIDATION REPORT")
        print("="*80 + "\n")

        # Overall stats
        pass_rate = (passed_count / len(self.test_cases)) * 100
        avg_score = sum(r.score for r in results) / len(results)

        print(f"Overall Results:")
        print(f"  ✅ Passed: {passed_count}/{len(self.test_cases)} ({pass_rate:.1f}%)")
        print(f"  ❌ Failed: {failed_count}/{len(self.test_cases)} ({100-pass_rate:.1f}%)")
        print(f"  📊 Average Score: {avg_score:.3f}/1.0")

        # Category breakdown
        print(f"\nResults by Category:")
        for category, stats in sorted(category_stats.items()):
            cat_pass_rate = (stats["passed"] / stats["total"]) * 100
            print(f"  {category:20s}: {stats['passed']:2d}/{stats['total']:2d} passed ({cat_pass_rate:5.1f}%), avg score: {stats['avg_score']:.3f}")

        # Failed tests detail
        if failed_count > 0:
            print(f"\nFailed Tests Detail:")
            for result in results:
                if not result.passed:
                    print(f"\n  Test #{result.test_id}: {result.details.get('description', 'N/A')}")
                    print(f"    Request: {result.details.get('user_request', 'N/A')}")
                    print(f"    Score: {result.score:.2f}")
                    for failure in result.failures:
                        print(f"    └─ {failure}")

        print("\n" + "="*80)

        # Research-based acceptance criteria
        acceptance_threshold = 0.70  # Based on F1 > 0.70 research standard
        acceptance_pass_rate = 85.0  # 85% pass rate

        overall_passed = pass_rate >= acceptance_pass_rate and avg_score >= acceptance_threshold

        print("\nACCEPTANCE CRITERIA (Research-Based):")
        print(f"  Threshold Score: ≥ {acceptance_threshold:.2f} (Current: {avg_score:.3f}) {'✅' if avg_score >= acceptance_threshold else '❌'}")
        print(f"  Pass Rate: ≥ {acceptance_pass_rate:.1f}% (Current: {pass_rate:.1f}%) {'✅' if pass_rate >= acceptance_pass_rate else '❌'}")
        print(f"\n  OVERALL: {'✅ PASSED' if overall_passed else '❌ FAILED'}")
        print("="*80 + "\n")

        return {
            "total_tests": len(self.test_cases),
            "passed": passed_count,
            "failed": failed_count,
            "pass_rate": pass_rate,
            "average_score": avg_score,
            "category_stats": category_stats,
            "acceptance_criteria_met": overall_passed,
            "results": results
        }


async def main():
    """Main entry point"""
    validator = IntentExtractionValidator()
    report = await validator.run_all_tests()

    # Return exit code based on acceptance
    return 0 if report["acceptance_criteria_met"] else 1


if __name__ == "__main__":
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    exit_code = asyncio.run(main())
    sys.exit(exit_code)
