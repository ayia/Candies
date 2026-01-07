"""
AGENT: ORCHESTRATOR (Enhanced)
Purpose: Understand user intent and route to appropriate agents
Model: Fast model (Llama small) for quick classification
Based on: https://www.anthropic.com/engineering/multi-agent-research-system
"""
import json
import re
from typing import Dict, Any, Optional
from .base import BaseAgent


# Keyword-based detection for robust fallback
IMAGE_KEYWORDS = {
    'fr': ['photo', 'image', 'selfie', 'pic', 'picture', 'envoie', 'montre', 'voir', 'nude', 'nue',
           'déshabille', 'strip', 'pose', 'tenue', 'lingerie', 'bikini', 'maillot'],
    'en': ['photo', 'image', 'selfie', 'pic', 'picture', 'send', 'show', 'see', 'nude', 'naked',
           'undress', 'strip', 'pose', 'outfit', 'lingerie', 'bikini', 'swimsuit'],
}

# Enhanced NSFW keywords with more sexual acts detection
NSFW_KEYWORDS = {
    'level_3': [
        # French sexual acts
        'baise', 'baiser', 'niquer', 'sucer', 'suce', 'fellation', 'levrette', 'sodomie',
        'penetr', 'jouir', 'ejacul', 'orgasm', 'chatte', 'pussy', 'bite', 'cock', 'dick',
        'queue', 'branle', 'masturb', 'doigt', 'finger', 'gode', 'dildo',
        # English sexual acts
        'fuck', 'suck', 'blowjob', 'bj', 'doggy', 'anal', 'penetrat', 'cum', 'creampie',
        'facial', 'handjob', 'titjob', 'threesome', 'orgy', 'gangbang', 'deepthroat',
        'cowgirl', 'missionary', 'spread', 'lick', 'eat out', 'ride',
        # Body parts explicit
        'clitoris', 'clit', 'anus', 'testicule', 'balls', 'shaft'
    ],
    'level_2': ['nude', 'nue', 'naked', 'sein', 'breast', 'tit', 'nichon', 'fesse', 'ass', 'butt',
                'cul', 'déshabill', 'undress', 'strip', 'nue', 'topless', 'nu ', 'nipple', 'mamelon',
                'exposed', 'bare', 'uncovered'],
    'level_1': ['sexy', 'coquin', 'naughty', 'hot', 'chaud', 'excit', 'sensuel', 'seduc',
                'flirt', 'tease', 'aguich', 'provoc', 'intimate', 'intime']
}

# Sexual acts that require special image generation handling
SEXUAL_ACTS = {
    'oral': ['sucer', 'suce', 'fellation', 'blowjob', 'bj', 'deepthroat', 'suck', 'oral'],
    'vaginal': ['baise', 'baiser', 'fuck', 'penetr', 'missionary', 'cowgirl', 'doggy', 'levrette', 'ride'],
    'anal': ['sodomie', 'anal'],
    'masturbation': ['branle', 'masturb', 'doigt', 'finger', 'touch'],
    'other': ['handjob', 'titjob', 'facial', 'cum', 'ejacul', 'creampie', 'threesome']
}

EMOTION_KEYWORDS = {
    'sexual': ['baise', 'fuck', 'sucer', 'chaud', 'excit', 'envie de toi', 'want you', 'horny'],
    'romantic': ['aime', 'love', 'amour', 'coeur', 'heart', 'miss you', 'tu me manques', 'tendresse'],
    'playful': ['haha', 'lol', 'mdr', 'hihi', 'joke', 'blague', 'rigol', 'amus'],
    'emotional': ['triste', 'sad', 'pleure', 'cry', 'seul', 'lonely', 'mal', 'hurt', 'depress'],
    'angry': ['colère', 'angry', 'énervé', 'mad', 'furieux', 'putain', 'merde']
}


class OrchestratorAgent(BaseAgent):
    """
    Enhanced Orchestrator with:
    1. Robust JSON parsing with multiple fallback strategies
    2. Keyword-based intent detection as backup
    3. Multi-language support (FR/EN)
    4. Detailed image request parsing
    """

    def get_system_prompt(self) -> str:
        return """You are an intent classifier for an AI companion chatbot. Analyze messages and output JSON.

TASK: Classify the user's intent and extract key information.

OUTPUT FORMAT (JSON only, no explanation):
{
    "intent": "chat_only" | "image_request" | "chat_with_image",
    "nsfw_level": 0-3,
    "emotion": "romantic" | "playful" | "sexual" | "casual" | "emotional" | "angry",
    "image_details": {
        "requested": true/false,
        "type": "selfie" | "full_body" | "pose" | "outfit" | "nude" | "sexual",
        "outfit": "description or null",
        "pose": "description or null",
        "setting": "description or null"
    },
    "language": "fr" | "en" | "es"
}

NSFW LEVELS:
0 = SFW (casual conversation)
1 = Suggestive (flirty, teasing, lingerie)
2 = Explicit (nudity, exposed body parts)
3 = Hardcore (sexual acts, explicit descriptions)

INTENT TYPES:
- chat_only: Just conversation, no image wanted
- image_request: Primarily wants a photo/image
- chat_with_image: Wants conversation AND an image

IMAGE TYPES:
- selfie: Face/upper body shot
- full_body: Full body visible
- pose: Specific pose requested
- outfit: Specific clothing requested
- nude: Nudity requested
- sexual: Sexual pose/act requested

Output ONLY valid JSON. No markdown, no explanation."""

    async def analyze(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze the user message with robust fallback"""
        # First, try LLM analysis
        llm_result = await self._llm_analyze(message, context)

        # Validate and enhance with keyword detection
        keyword_result = self._keyword_analyze(message)

        # Merge results, preferring LLM but using keywords as validation/fallback
        final_result = self._merge_results(llm_result, keyword_result)

        return final_result

    async def _llm_analyze(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Try to analyze with LLM"""
        try:
            response = await self.call(
                message=f"Analyze this message: \"{message}\"",
                context=context,
                temperature=0.1,
                max_tokens=300
            )

            parsed = self._parse_json_response(response)
            if parsed:
                return parsed
        except Exception as e:
            print(f"[Orchestrator] LLM analysis error: {e}")

        return {}

    def _keyword_analyze(self, message: str) -> Dict[str, Any]:
        """Fallback keyword-based analysis with enhanced sexual act detection"""
        msg_lower = message.lower()

        # Detect language
        fr_indicators = ['je', 'tu', 'moi', 'toi', 'une', 'est', 'les', 'des', 'pour', 'avec']
        fr_count = sum(1 for word in fr_indicators if f' {word} ' in f' {msg_lower} ')
        language = 'fr' if fr_count >= 2 else 'en'

        # Detect image request
        all_image_keywords = IMAGE_KEYWORDS['fr'] + IMAGE_KEYWORDS['en']
        wants_image = any(kw in msg_lower for kw in all_image_keywords)

        # Detect sexual acts - this also triggers image request
        detected_sexual_act = None
        for act_type, keywords in SEXUAL_ACTS.items():
            for kw in keywords:
                if kw in msg_lower:
                    detected_sexual_act = act_type
                    wants_image = True  # Sexual acts imply wanting an image
                    break
            if detected_sexual_act:
                break

        # Detect NSFW level
        nsfw_level = 0
        if detected_sexual_act or any(kw in msg_lower for kw in NSFW_KEYWORDS['level_3']):
            nsfw_level = 3
        elif any(kw in msg_lower for kw in NSFW_KEYWORDS['level_2']):
            nsfw_level = 2
        elif any(kw in msg_lower for kw in NSFW_KEYWORDS['level_1']):
            nsfw_level = 1

        # Detect emotion
        emotion = 'casual'
        if detected_sexual_act or nsfw_level >= 2:
            emotion = 'sexual'
        else:
            for emo, keywords in EMOTION_KEYWORDS.items():
                if any(kw in msg_lower for kw in keywords):
                    emotion = emo
                    break

        # Determine image type
        image_type = None
        if wants_image:
            if detected_sexual_act:
                image_type = 'sexual'
            elif nsfw_level >= 3:
                image_type = 'sexual'
            elif nsfw_level >= 2:
                image_type = 'nude'
            elif 'lingerie' in msg_lower or 'bikini' in msg_lower:
                image_type = 'outfit'
            elif 'pose' in msg_lower:
                image_type = 'pose'
            elif 'corps' in msg_lower or 'body' in msg_lower or 'full' in msg_lower:
                image_type = 'full_body'
            else:
                image_type = 'selfie'

        # Determine intent
        if wants_image:
            # Check if there's substantial conversation content
            word_count = len(message.split())
            if word_count > 15:
                intent = 'chat_with_image'
            else:
                intent = 'image_request'
        else:
            intent = 'chat_only'

        # Extract outfit/pose details from message
        outfit = self._extract_detail(msg_lower, ['lingerie', 'bikini', 'robe', 'dress', 'jupe', 'skirt',
                                                   'maillot', 'swimsuit', 'nu', 'naked', 'topless'])
        pose = self._extract_detail(msg_lower, ['allongée', 'lying', 'debout', 'standing', 'assise',
                                                 'sitting', 'genoux', 'knees', 'dos', 'back', 'face',
                                                 'levrette', 'doggy', 'quatre pattes', 'all fours'])
        setting = self._extract_detail(msg_lower, ['lit', 'bed', 'douche', 'shower', 'plage', 'beach',
                                                    'chambre', 'bedroom', 'dehors', 'outside', 'ruelle',
                                                    'alley', 'voiture', 'car', 'public'])

        return {
            'intent': intent,
            'nsfw_level': nsfw_level,
            'emotion': emotion,
            'image_details': {
                'requested': wants_image,
                'type': image_type,
                'outfit': outfit,
                'pose': pose,
                'setting': setting,
                'sexual_act': detected_sexual_act  # New field for sexual act type
            },
            'language': language,
            '_source': 'keywords'
        }

    def _extract_detail(self, text: str, keywords: list) -> Optional[str]:
        """Extract a detail from text based on keywords"""
        for kw in keywords:
            if kw in text:
                return kw
        return None

    def _merge_results(self, llm_result: Dict, keyword_result: Dict) -> Dict[str, Any]:
        """Merge LLM and keyword results intelligently"""
        # If LLM failed completely, use keywords
        if not llm_result:
            keyword_result['_source'] = 'keywords_only'
            return keyword_result

        # Start with LLM result
        merged = llm_result.copy()
        merged['_source'] = 'llm'

        # Validate/correct with keyword detection
        kw_wants_image = keyword_result.get('image_details', {}).get('requested', False)
        llm_wants_image = llm_result.get('image_details', {}).get('requested', False)

        # If keywords detected image request but LLM missed it, correct
        if kw_wants_image and not llm_wants_image:
            merged['intent'] = keyword_result['intent']
            merged['image_details'] = keyword_result['image_details']
            merged['_source'] = 'llm_corrected'

        # Use higher NSFW level (keywords might catch things LLM missed)
        kw_nsfw = keyword_result.get('nsfw_level', 0)
        llm_nsfw = llm_result.get('nsfw_level', 0)
        if kw_nsfw > llm_nsfw:
            merged['nsfw_level'] = kw_nsfw
            merged['_source'] = 'llm_corrected'

        # Fill in missing image details from keywords
        if merged.get('image_details', {}).get('requested'):
            llm_details = merged.get('image_details', {})
            kw_details = keyword_result.get('image_details', {})

            for key in ['outfit', 'pose', 'setting']:
                if not llm_details.get(key) and kw_details.get(key):
                    llm_details[key] = kw_details[key]

            if not llm_details.get('type') and kw_details.get('type'):
                llm_details['type'] = kw_details['type']

        # Ensure language is set
        if 'language' not in merged:
            merged['language'] = keyword_result.get('language', 'fr')

        return merged

    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """Try multiple strategies to parse JSON from LLM response"""
        if not response:
            return None

        # Strategy 1: Direct parse
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract from markdown code block
        try:
            clean = response.strip()
            if '```' in clean:
                # Find JSON between code blocks
                match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', clean)
                if match:
                    return json.loads(match.group(1).strip())
        except (json.JSONDecodeError, AttributeError):
            pass

        # Strategy 3: Find JSON object pattern
        try:
            match = re.search(r'\{[\s\S]*\}', response)
            if match:
                return json.loads(match.group(0))
        except (json.JSONDecodeError, AttributeError):
            pass

        # Strategy 4: Fix common JSON issues
        try:
            fixed = response.strip()
            # Remove trailing commas
            fixed = re.sub(r',\s*}', '}', fixed)
            fixed = re.sub(r',\s*]', ']', fixed)
            # Fix unquoted keys
            fixed = re.sub(r'(\w+):', r'"\1":', fixed)
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

        return None
