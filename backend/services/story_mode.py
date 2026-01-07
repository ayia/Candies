"""
Story Mode Service
Inspired by Candy.ai's 2025 Story Mode with branching narratives

Provides interactive storytelling with:
1. Pre-built scenario templates
2. Branching dialogue paths
3. Stage progression
4. Image generation at key moments
5. Multiple endings
"""

import json
import random
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class StoryStage(Enum):
    """Story progression stages"""
    INTRO = "intro"
    RISING = "rising"
    CLIMAX = "climax"
    RESOLUTION = "resolution"
    ENDING = "ending"


@dataclass
class StoryChoice:
    """A choice the user can make"""
    id: str
    text: str
    text_fr: str
    leads_to: str  # Next beat ID
    nsfw_level: int = 0
    mood_shift: str = "neutral"  # positive, negative, romantic, sexual, neutral


@dataclass
class StoryBeat:
    """A single story beat/moment"""
    id: str
    stage: StoryStage
    description: str
    description_fr: str
    ai_dialogue: str
    ai_dialogue_fr: str
    choices: List[StoryChoice]
    image_prompt: Optional[str] = None  # If set, generate image at this beat
    nsfw_level: int = 0
    is_ending: bool = False
    ending_type: Optional[str] = None  # romantic, sexual, sweet, dramatic


@dataclass
class Scenario:
    """A complete story scenario"""
    id: str
    title: str
    title_fr: str
    description: str
    description_fr: str
    setting: str
    mood: str  # romantic, playful, sensual, adventurous
    nsfw_max_level: int  # Maximum NSFW level this scenario can reach
    beats: Dict[str, StoryBeat]
    starting_beat: str
    character_requirements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StorySession:
    """Active story session state"""
    session_id: str
    scenario_id: str
    character_id: int
    current_beat_id: str
    history: List[str]  # Beat IDs visited
    choices_made: List[Tuple[str, str]]  # (beat_id, choice_id)
    current_nsfw_level: int
    started_at: str
    images_generated: List[str]

    def to_dict(self) -> Dict:
        return asdict(self)


# Pre-built scenarios
SCENARIOS: Dict[str, Scenario] = {

    "romantic_dinner": Scenario(
        id="romantic_dinner",
        title="Romantic Dinner Date",
        title_fr="Diner Romantique",
        description="A candlelit dinner that could lead anywhere...",
        description_fr="Un diner aux chandelles qui pourrait mener n'importe ou...",
        setting="upscale restaurant with candlelight, intimate atmosphere",
        mood="romantic",
        nsfw_max_level=3,
        starting_beat="dinner_start",
        beats={
            "dinner_start": StoryBeat(
                id="dinner_start",
                stage=StoryStage.INTRO,
                description="You arrive at the restaurant. She's already there, looking stunning.",
                description_fr="Tu arrives au restaurant. Elle est deja la, magnifique.",
                ai_dialogue="*looks up and smiles as you approach* There you are... *stands to greet you with a kiss on the cheek* I was starting to think you'd stand me up. You look amazing tonight.",
                ai_dialogue_fr="*leve les yeux et sourit en te voyant approcher* Te voila... *se leve pour t'embrasser sur la joue* Je commencais a croire que tu me poserais un lapin. Tu es superbe ce soir.",
                image_prompt="elegant woman sitting at candlelit restaurant table, wearing beautiful dress, romantic atmosphere, waiting expectantly, soft lighting",
                choices=[
                    StoryChoice("compliment", "Compliment her beauty", "Complimenter sa beaute", "dinner_compliment", 0, "romantic"),
                    StoryChoice("playful", "Make a playful joke", "Faire une blague joueuse", "dinner_playful", 0, "positive"),
                    StoryChoice("bold", "Kiss her properly", "L'embrasser vraiment", "dinner_kiss", 1, "romantic")
                ]
            ),
            "dinner_compliment": StoryBeat(
                id="dinner_compliment",
                stage=StoryStage.RISING,
                description="She blushes at your compliment.",
                description_fr="Elle rougit a ton compliment.",
                ai_dialogue="*blushes and looks down shyly* Stop... you're going to make me blush all evening. *reaches for your hand across the table* But thank you... I wanted to look good for you.",
                ai_dialogue_fr="*rougit et baisse les yeux timidement* Arrete... tu vas me faire rougir toute la soiree. *prend ta main a travers la table* Mais merci... je voulais etre belle pour toi.",
                choices=[
                    StoryChoice("hand", "Hold her hand tenderly", "Tenir sa main tendrement", "dinner_intimate", 0, "romantic"),
                    StoryChoice("flirt", "Whisper something flirty", "Murmurer quelque chose de coquin", "dinner_flirty", 1, "sexual"),
                    StoryChoice("food", "Focus on ordering food", "Se concentrer sur la commande", "dinner_food", 0, "neutral")
                ]
            ),
            "dinner_playful": StoryBeat(
                id="dinner_playful",
                stage=StoryStage.RISING,
                description="She laughs at your joke.",
                description_fr="Elle rit a ta blague.",
                ai_dialogue="*laughs and playfully pushes your arm* Oh my god, you're terrible! *grins* This is why I love spending time with you... you always make me laugh.",
                ai_dialogue_fr="*rit et te pousse le bras de maniere joueuse* Oh mon dieu, tu es terrible! *sourit* C'est pour ca que j'aime passer du temps avec toi... tu me fais toujours rire.",
                choices=[
                    StoryChoice("more_jokes", "Keep the jokes coming", "Continuer les blagues", "dinner_fun", 0, "positive"),
                    StoryChoice("serious", "Get more serious and romantic", "Devenir plus serieux et romantique", "dinner_intimate", 0, "romantic"),
                    StoryChoice("tease", "Tease her back", "La taquiner en retour", "dinner_tease", 1, "playful")
                ]
            ),
            "dinner_kiss": StoryBeat(
                id="dinner_kiss",
                stage=StoryStage.RISING,
                description="She's surprised but pleased by your boldness.",
                description_fr="Elle est surprise mais ravie de ton audace.",
                ai_dialogue="*eyes widen in surprise, then melts into the kiss* Mmm... *pulls back breathlessly* Well... that's one way to say hello. *bites lip* Maybe we should sit down before we cause a scene...",
                ai_dialogue_fr="*ses yeux s'agrandissent de surprise, puis fond dans le baiser* Mmm... *se recule a bout de souffle* Eh bien... c'est une facon de dire bonjour. *se mord la levre* On devrait peut-etre s'asseoir avant de faire une scene...",
                nsfw_level=1,
                choices=[
                    StoryChoice("sit", "Sit down and order wine", "S'asseoir et commander du vin", "dinner_wine", 0, "romantic"),
                    StoryChoice("whisper", "Whisper what you want to do later", "Murmurer ce que tu veux faire plus tard", "dinner_tease_heavy", 2, "sexual"),
                    StoryChoice("another", "Kiss her again", "L'embrasser encore", "dinner_passionate", 1, "sexual")
                ]
            ),
            "dinner_intimate": StoryBeat(
                id="dinner_intimate",
                stage=StoryStage.CLIMAX,
                description="The atmosphere becomes more intimate.",
                description_fr="L'atmosphere devient plus intime.",
                ai_dialogue="*gazes into your eyes* You know... I've been thinking about tonight all week. *squeezes your hand* There's nowhere else I'd rather be right now. *moves closer* The food here is supposed to be amazing... but honestly, I'm not that hungry anymore.",
                ai_dialogue_fr="*te regarde dans les yeux* Tu sais... j'ai pense a ce soir toute la semaine. *serre ta main* Il n'y a nulle part ailleurs ou je voudrais etre en ce moment. *se rapproche* La nourriture ici est supposee etre incroyable... mais honnetement, je n'ai plus vraiment faim.",
                image_prompt="couple holding hands at candlelit dinner, romantic gaze, intimate moment, soft lighting, elegant restaurant",
                choices=[
                    StoryChoice("stay", "Stay and enjoy the evening", "Rester et profiter de la soiree", "dinner_romantic_end", 0, "romantic"),
                    StoryChoice("leave", "Suggest leaving early", "Suggerer de partir tot", "leave_restaurant", 2, "sexual"),
                    StoryChoice("dessert", "Order dessert to share", "Commander un dessert a partager", "dinner_dessert", 1, "romantic")
                ]
            ),
            "dinner_flirty": StoryBeat(
                id="dinner_flirty",
                stage=StoryStage.CLIMAX,
                description="The tension rises as you whisper something naughty.",
                description_fr="La tension monte quand tu murmures quelque chose de coquin.",
                ai_dialogue="*eyes widen, then darken with desire* *whispers back* You can't say things like that in public... *crosses legs under table* Now I can't focus on anything else. *fans herself* Is it hot in here?",
                ai_dialogue_fr="*ses yeux s'agrandissent, puis s'assombrissent de desir* *murmure en retour* Tu ne peux pas dire des choses comme ca en public... *croise les jambes sous la table* Maintenant je ne peux plus penser a rien d'autre. *s'evente* Il fait chaud ici non?",
                nsfw_level=2,
                choices=[
                    StoryChoice("tease_more", "Keep teasing her", "Continuer a la taquiner", "dinner_tease_heavy", 2, "sexual"),
                    StoryChoice("touch", "Touch her leg under the table", "Toucher sa jambe sous la table", "dinner_touch", 2, "sexual"),
                    StoryChoice("cool_down", "Cool things down a bit", "Calmer un peu les choses", "dinner_romantic_end", 0, "romantic")
                ]
            ),
            "dinner_tease_heavy": StoryBeat(
                id="dinner_tease_heavy",
                stage=StoryStage.CLIMAX,
                description="She's clearly affected by your words.",
                description_fr="Elle est clairement affectee par tes mots.",
                ai_dialogue="*breathing harder* *leans in close* You're evil, you know that? *hand moves to your thigh under table* Two can play at this game... *whispers* Maybe we should skip straight to dessert... at my place?",
                ai_dialogue_fr="*respire plus fort* *se penche* Tu es diabolique, tu sais? *sa main se pose sur ta cuisse sous la table* On peut jouer a deux a ce jeu... *murmure* On devrait peut-etre passer directement au dessert... chez moi?",
                nsfw_level=2,
                image_prompt="woman leaning forward seductively at dinner table, low cut dress, candlelight, hungry eyes, biting lip",
                choices=[
                    StoryChoice("yes", "Accept her invitation", "Accepter son invitation", "leave_restaurant", 2, "sexual"),
                    StoryChoice("tease_back", "Tease her some more first", "La taquiner encore un peu d'abord", "dinner_torture", 2, "sexual"),
                    StoryChoice("patience", "Make her wait", "La faire attendre", "dinner_dessert", 1, "sexual")
                ]
            ),
            "leave_restaurant": StoryBeat(
                id="leave_restaurant",
                stage=StoryStage.RESOLUTION,
                description="You both decide to leave for somewhere more private.",
                description_fr="Vous decidez tous les deux de partir pour un endroit plus prive.",
                ai_dialogue="*grabs her purse excitedly* Let's go... I can't wait anymore. *takes your hand and pulls you toward the exit* My place is close... *looks back at you with desire* I hope you're ready for tonight...",
                ai_dialogue_fr="*prend son sac avec excitation* Allons-y... je ne peux plus attendre. *prend ta main et te tire vers la sortie* Mon appartement est proche... *te regarde avec desir* J'espere que tu es pret pour ce soir...",
                nsfw_level=2,
                choices=[
                    StoryChoice("her_place", "Go to her place", "Aller chez elle", "ending_passionate", 3, "sexual"),
                    StoryChoice("taxi_fun", "Get frisky in the taxi", "Commencer dans le taxi", "taxi_scene", 3, "sexual"),
                    StoryChoice("romantic_walk", "Take a romantic walk first", "Faire une promenade romantique d'abord", "ending_romantic", 1, "romantic")
                ]
            ),
            "dinner_romantic_end": StoryBeat(
                id="dinner_romantic_end",
                stage=StoryStage.ENDING,
                description="A beautiful romantic evening.",
                description_fr="Une belle soiree romantique.",
                ai_dialogue="*walks out with you, arm in arm* This was perfect... *looks up at the stars* Thank you for tonight. *stops and turns to face you* I don't want this night to end... *cups your face gently* Kiss me?",
                ai_dialogue_fr="*sort avec toi, bras dessus bras dessous* C'etait parfait... *regarde les etoiles* Merci pour ce soir. *s'arrete et se tourne vers toi* Je ne veux pas que cette nuit se termine... *prend ton visage doucement* Embrasse-moi?",
                image_prompt="romantic couple outside restaurant at night, stars, city lights, elegant dress, intimate moment, about to kiss",
                is_ending=True,
                ending_type="romantic",
                choices=[]
            ),
            "ending_passionate": StoryBeat(
                id="ending_passionate",
                stage=StoryStage.ENDING,
                description="A passionate night awaits.",
                description_fr="Une nuit passionnee vous attend.",
                ai_dialogue="*pulls you inside her apartment, kissing hungrily* *kicks door closed* I've wanted this all night... *pushes you against the wall* No more waiting... *starts unbuttoning your shirt* You're mine tonight...",
                ai_dialogue_fr="*te tire dans son appartement, embrassant avidement* *claque la porte* J'ai voulu ca toute la soiree... *te pousse contre le mur* Plus d'attente... *commence a deboutonner ta chemise* Tu es a moi ce soir...",
                nsfw_level=3,
                image_prompt="passionate woman pushing man against wall in apartment, kissing, urgent desire, dim lighting, unbuttoning shirt",
                is_ending=True,
                ending_type="sexual",
                choices=[]
            ),
            "ending_romantic": StoryBeat(
                id="ending_romantic",
                stage=StoryStage.ENDING,
                description="A sweet romantic ending.",
                description_fr="Une fin douce et romantique.",
                ai_dialogue="*walks hand in hand by the river* *stops under a streetlamp* Tonight was magical... *wraps arms around your neck* I think I'm falling for you... *kisses you softly* Stay with me tonight? Just... hold me?",
                ai_dialogue_fr="*marche main dans la main au bord de la riviere* *s'arrete sous un lampadaire* Ce soir etait magique... *enroule ses bras autour de ton cou* Je crois que je tombe amoureuse de toi... *t'embrasse doucement* Reste avec moi ce soir? Juste... serre-moi?",
                image_prompt="romantic couple under streetlamp by river at night, embrace, soft kiss, city lights reflection, tender moment",
                is_ending=True,
                ending_type="romantic",
                choices=[]
            ),
            # Add more beats as needed...
            "dinner_dessert": StoryBeat(
                id="dinner_dessert",
                stage=StoryStage.CLIMAX,
                description="You order dessert to share.",
                description_fr="Vous commandez un dessert a partager.",
                ai_dialogue="*feeds you a bite of chocolate cake* Mmm... *licks her lips* This is delicious... but not as sweet as what comes after... *winks* How do you want the night to end?",
                ai_dialogue_fr="*te donne une bouchee de gateau au chocolat* Mmm... *leche ses levres* C'est delicieux... mais pas aussi doux que ce qui vient apres... *fait un clin d'oeil* Comment veux-tu que la soiree se termine?",
                nsfw_level=1,
                choices=[
                    StoryChoice("romantic", "Keep it romantic", "Rester romantique", "dinner_romantic_end", 0, "romantic"),
                    StoryChoice("passionate", "Take her home", "L'emmener chez elle", "ending_passionate", 3, "sexual"),
                ]
            ),
            "dinner_touch": StoryBeat(
                id="dinner_touch",
                stage=StoryStage.CLIMAX,
                description="Your hand finds her leg under the table.",
                description_fr="Ta main trouve sa jambe sous la table.",
                ai_dialogue="*gasps quietly* *spreads legs slightly* You're bold... *bites lip* *whispers* Higher... *eyes flutter* We really should get out of here...",
                ai_dialogue_fr="*halète doucement* *ecarte legerement les jambes* Tu es audacieux... *se mord la levre* *murmure* Plus haut... *ses yeux papillonnent* On devrait vraiment partir d'ici...",
                nsfw_level=2,
                choices=[
                    StoryChoice("leave", "Leave immediately", "Partir immediatement", "leave_restaurant", 2, "sexual"),
                    StoryChoice("continue", "Continue teasing", "Continuer a taquiner", "dinner_torture", 3, "sexual")
                ]
            ),
            "dinner_torture": StoryBeat(
                id="dinner_torture",
                stage=StoryStage.CLIMAX,
                description="She's at her limit.",
                description_fr="Elle est a sa limite.",
                ai_dialogue="*grips table edge* *breathing heavily* *whispers urgently* Please... I can't take anymore... *grabs your hand* Take me home NOW... before I do something embarrassing right here...",
                ai_dialogue_fr="*agrippe le bord de la table* *respire fort* *murmure urgemment* S'il te plait... je n'en peux plus... *attrape ta main* Emmene-moi a la maison MAINTENANT... avant que je fasse quelque chose d'embarrassant ici...",
                nsfw_level=3,
                choices=[
                    StoryChoice("mercy", "Have mercy and leave", "Avoir pitie et partir", "ending_passionate", 3, "sexual")
                ]
            ),
            "taxi_scene": StoryBeat(
                id="taxi_scene",
                stage=StoryStage.RESOLUTION,
                description="Things heat up in the taxi.",
                description_fr="Les choses chauffent dans le taxi.",
                ai_dialogue="*pulls you into the backseat* *kisses you hungrily* *climbs onto your lap* I can't wait... *whispers* I need you... *pulls dress up slightly* The driver can't see...",
                ai_dialogue_fr="*te tire sur la banquette arriere* *t'embrasse avidement* *grimpe sur tes genoux* Je ne peux pas attendre... *murmure* J'ai besoin de toi... *remonte sa robe legerement* Le chauffeur ne voit rien...",
                nsfw_level=3,
                is_ending=True,
                ending_type="sexual",
                choices=[]
            ),
            "dinner_fun": StoryBeat(
                id="dinner_fun",
                stage=StoryStage.RISING,
                description="The evening continues with laughter.",
                description_fr="La soiree continue dans les rires.",
                ai_dialogue="*wipes tears from laughing* Stop, stop! My mascara! *reaches for your hand* You know what I love about us? We can just be ourselves. *squeezes hand* Should we order wine and see where the night takes us?",
                ai_dialogue_fr="*essuie des larmes de rire* Arrete, arrete! Mon mascara! *prend ta main* Tu sais ce que j'aime chez nous? On peut juste etre nous-memes. *serre ta main* On devrait commander du vin et voir ou la soiree nous mene?",
                choices=[
                    StoryChoice("wine", "Order wine", "Commander du vin", "dinner_wine", 0, "positive"),
                    StoryChoice("deep", "Get more intimate", "Devenir plus intime", "dinner_intimate", 1, "romantic")
                ]
            ),
            "dinner_wine": StoryBeat(
                id="dinner_wine",
                stage=StoryStage.RISING,
                description="Wine arrives and the mood shifts.",
                description_fr="Le vin arrive et l'ambiance change.",
                ai_dialogue="*sips wine* Mmm this is good... *sets glass down and looks at you* You know... *traces finger on glass rim* I wore this dress just for you... *leans closer* Do you like it?",
                ai_dialogue_fr="*sirote le vin* Mmm c'est bon... *pose le verre et te regarde* Tu sais... *trace son doigt sur le bord du verre* J'ai porte cette robe juste pour toi... *se penche* Tu aimes?",
                choices=[
                    StoryChoice("dress", "Tell her she looks amazing", "Lui dire qu'elle est magnifique", "dinner_intimate", 0, "romantic"),
                    StoryChoice("tease", "Say you'd prefer it off", "Dire que tu la prefererais sans", "dinner_flirty", 2, "sexual")
                ]
            ),
            "dinner_tease": StoryBeat(
                id="dinner_tease",
                stage=StoryStage.RISING,
                description="Playful teasing continues.",
                description_fr="Les taquineries continuent.",
                ai_dialogue="*raises eyebrow with a smirk* Oh really? *leans back confidently* Well, two can play at this game... *deliberately drops napkin and bends to pick it up slowly* Oops...",
                ai_dialogue_fr="*leve un sourcil avec un sourire* Ah vraiment? *se penche en arriere avec confiance* Eh bien, on peut jouer a deux... *fait tomber deliberement sa serviette et se penche lentement pour la ramasser* Oups...",
                nsfw_level=1,
                choices=[
                    StoryChoice("enjoy", "Enjoy the view", "Profiter de la vue", "dinner_flirty", 1, "sexual"),
                    StoryChoice("call_out", "Call her out on it", "La confronter", "dinner_playful", 0, "playful")
                ]
            )
        }
    ),

    "beach_day": Scenario(
        id="beach_day",
        title="Beach Day Paradise",
        title_fr="Journee Paradis a la Plage",
        description="A sunny day at a secluded beach...",
        description_fr="Une journee ensoleeillee sur une plage isolee...",
        setting="beautiful secluded beach, warm sun, crystal clear water",
        mood="playful",
        nsfw_max_level=3,
        starting_beat="beach_arrival",
        beats={
            "beach_arrival": StoryBeat(
                id="beach_arrival",
                stage=StoryStage.INTRO,
                description="You arrive at the beach. She's setting up.",
                description_fr="Tu arrives a la plage. Elle installe les affaires.",
                ai_dialogue="*waves excitedly* Over here! *adjusts bikini* The water looks amazing! *twirls to show off her bikini* Like it? I bought it just for today... *grins* Want to go for a swim first or help me with the sunscreen?",
                ai_dialogue_fr="*fait signe avec excitation* Par ici! *ajuste son bikini* L'eau a l'air incroyable! *tourne sur elle-meme pour montrer son bikini* Tu aimes? Je l'ai achete juste pour aujourd'hui... *sourit* Tu veux nager d'abord ou m'aider avec la creme solaire?",
                image_prompt="beautiful woman in bikini at beach, setting up towel, sunny day, crystal clear water, waving happily, tropical paradise",
                choices=[
                    StoryChoice("sunscreen", "Help with sunscreen", "Aider avec la creme solaire", "beach_sunscreen", 1, "romantic"),
                    StoryChoice("swim", "Go for a swim", "Aller nager", "beach_swim", 0, "playful"),
                    StoryChoice("admire", "Admire her bikini", "Admirer son bikini", "beach_admire", 1, "sexual")
                ]
            ),
            "beach_sunscreen": StoryBeat(
                id="beach_sunscreen",
                stage=StoryStage.RISING,
                description="You help her apply sunscreen.",
                description_fr="Tu l'aides a appliquer la creme solaire.",
                ai_dialogue="*lies down on towel* *hands you the bottle* Don't miss any spots... *looks back at you* Especially my back... *unties bikini string* Don't want tan lines...",
                ai_dialogue_fr="*s'allonge sur la serviette* *te donne la bouteille* Ne rate aucun endroit... *te regarde* Surtout mon dos... *defait le lien de son bikini* Je ne veux pas de marques de bronzage...",
                nsfw_level=1,
                image_prompt="woman lying on beach towel, back exposed, bikini untied, waiting for sunscreen, sunny beach setting, sensual pose",
                choices=[
                    StoryChoice("thorough", "Be very thorough", "Etre tres applique", "beach_massage", 2, "sexual"),
                    StoryChoice("quick", "Quick application", "Application rapide", "beach_swim", 0, "neutral"),
                    StoryChoice("tease", "Tease her while applying", "La taquiner en appliquant", "beach_tease", 2, "sexual")
                ]
            ),
            "beach_swim": StoryBeat(
                id="beach_swim",
                stage=StoryStage.RISING,
                description="You go swimming together.",
                description_fr="Vous allez nager ensemble.",
                ai_dialogue="*splashes you playfully* *swims closer* *wraps arms around your neck in the water* It's so warm... *legs wrap around your waist under water* Much better than being at work, huh? *giggles*",
                ai_dialogue_fr="*t'eclabousse de maniere joueuse* *nage plus pres* *enroule ses bras autour de ton cou dans l'eau* C'est si chaud... *ses jambes entourent ta taille sous l'eau* C'est tellement mieux que le travail, non? *rigole*",
                choices=[
                    StoryChoice("hold", "Hold her close", "La tenir proche", "beach_intimate_water", 1, "romantic"),
                    StoryChoice("dunk", "Playfully dunk her", "La couler de maniere joueuse", "beach_play", 0, "playful"),
                    StoryChoice("kiss", "Kiss her in the water", "L'embrasser dans l'eau", "beach_water_kiss", 2, "romantic")
                ]
            ),
            "beach_admire": StoryBeat(
                id="beach_admire",
                stage=StoryStage.RISING,
                description="You admire her bikini.",
                description_fr="Tu admires son bikini.",
                ai_dialogue="*poses with hands on hips* *spins slowly* You like? *pulls at string* It's pretty small... *bites lip* Maybe too small for public... good thing we're alone out here...",
                ai_dialogue_fr="*pose les mains sur les hanches* *tourne lentement* Tu aimes? *tire sur le lien* C'est assez petit... *se mord la levre* Peut-etre trop petit pour le public... heureusement qu'on est seuls ici...",
                nsfw_level=1,
                choices=[
                    StoryChoice("perfect", "Tell her it's perfect", "Lui dire que c'est parfait", "beach_sunscreen", 1, "romantic"),
                    StoryChoice("less", "Suggest wearing less", "Suggerer d'en porter moins", "beach_topless", 2, "sexual"),
                    StoryChoice("closer", "Get closer to inspect", "S'approcher pour inspecter", "beach_close", 2, "sexual")
                ]
            ),
            "beach_massage": StoryBeat(
                id="beach_massage",
                stage=StoryStage.CLIMAX,
                description="The sunscreen application becomes a massage.",
                description_fr="L'application de creme solaire devient un massage.",
                ai_dialogue="*moans softly* Mmm... that feels amazing... *arches back* Your hands... *breathes heavily* Maybe we should... find somewhere more private...",
                ai_dialogue_fr="*gemit doucement* Mmm... c'est incroyable... *cambre le dos* Tes mains... *respire fort* Peut-etre qu'on devrait... trouver un endroit plus prive...",
                nsfw_level=2,
                choices=[
                    StoryChoice("private", "Find a private spot", "Trouver un endroit prive", "beach_private", 3, "sexual"),
                    StoryChoice("here", "Stay right here", "Rester ici", "beach_risky", 3, "sexual"),
                    StoryChoice("slow", "Take it slow", "Ralentir", "beach_swim", 0, "romantic")
                ]
            ),
            "beach_private": StoryBeat(
                id="beach_private",
                stage=StoryStage.RESOLUTION,
                description="You find a secluded spot behind some rocks.",
                description_fr="Vous trouvez un endroit isole derriere des rochers.",
                ai_dialogue="*pulls you behind large rocks* *kisses hungrily* No one can see us here... *removes bikini top* I've wanted this all day... *pulls you down onto the sand*",
                ai_dialogue_fr="*te tire derriere de gros rochers* *embrasse avidement* Personne ne peut nous voir ici... *retire le haut de son bikini* J'ai voulu ca toute la journee... *te tire sur le sable*",
                nsfw_level=3,
                image_prompt="secluded beach behind rocks, woman removing bikini, passionate embrace, private moment, tropical setting",
                is_ending=True,
                ending_type="sexual",
                choices=[]
            ),
            "beach_tease": StoryBeat(
                id="beach_tease",
                stage=StoryStage.RISING,
                description="You tease her while applying sunscreen.",
                description_fr="Tu la taquines en appliquant la creme.",
                ai_dialogue="*squirms* Hey! *giggles* Those are... sensitive areas... *blushes* You're doing that on purpose! *looks back with desire* Don't start something you can't finish...",
                ai_dialogue_fr="*se tortille* Hey! *rigole* Ce sont des... zones sensibles... *rougit* Tu fais expres! *te regarde avec desir* Ne commence pas quelque chose que tu ne peux pas finir...",
                nsfw_level=2,
                choices=[
                    StoryChoice("continue", "Continue teasing", "Continuer a taquiner", "beach_massage", 2, "sexual"),
                    StoryChoice("stop", "Stop and swim", "Arreter et nager", "beach_swim", 0, "playful")
                ]
            ),
            "beach_water_kiss": StoryBeat(
                id="beach_water_kiss",
                stage=StoryStage.CLIMAX,
                description="A passionate kiss in the water.",
                description_fr="Un baiser passionne dans l'eau.",
                ai_dialogue="*melts into kiss* *legs tighten around you* *whispers against lips* The water is making this so hot... *grinds against you* Can you feel how much I want you?",
                ai_dialogue_fr="*fond dans le baiser* *resserre ses jambes autour de toi* *murmure contre tes levres* L'eau rend ca tellement excitant... *se frotte contre toi* Tu sens a quel point je te veux?",
                nsfw_level=2,
                image_prompt="couple kissing in ocean water, wrapped around each other, passionate embrace, sunset beach, romantic",
                choices=[
                    StoryChoice("beach", "Take it to the beach", "Aller sur la plage", "beach_private", 3, "sexual"),
                    StoryChoice("here", "Stay in the water", "Rester dans l'eau", "beach_water_ending", 3, "sexual"),
                    StoryChoice("romantic", "Keep it romantic", "Rester romantique", "beach_romantic_end", 1, "romantic")
                ]
            ),
            "beach_intimate_water": StoryBeat(
                id="beach_intimate_water",
                stage=StoryStage.CLIMAX,
                description="An intimate moment in the water.",
                description_fr="Un moment intime dans l'eau.",
                ai_dialogue="*rests head on your shoulder* *sighs contentedly* This is perfect... just us, the ocean... *looks up at you* I could stay like this forever... *kisses your neck softly*",
                ai_dialogue_fr="*pose sa tete sur ton epaule* *soupire de contentement* C'est parfait... juste nous, l'ocean... *te regarde* Je pourrais rester comme ca pour toujours... *embrasse ton cou doucement*",
                choices=[
                    StoryChoice("kiss", "Kiss her", "L'embrasser", "beach_water_kiss", 2, "romantic"),
                    StoryChoice("stay", "Stay and enjoy", "Rester et profiter", "beach_romantic_end", 0, "romantic")
                ]
            ),
            "beach_play": StoryBeat(
                id="beach_play",
                stage=StoryStage.RISING,
                description="Playful splashing continues.",
                description_fr="Les eclaboussures continuent.",
                ai_dialogue="*surfaces sputtering* *laughs* Oh you're gonna pay for that! *tackles you into the water* *ends up on top of you in shallow water* Gotcha! *grins down at you* Now what are you gonna do?",
                ai_dialogue_fr="*remonte en crachotant* *rit* Oh tu vas payer pour ca! *te plaque dans l'eau* *finit sur toi dans l'eau peu profonde* Je t'ai eu! *sourit* Maintenant tu vas faire quoi?",
                choices=[
                    StoryChoice("flip", "Flip her over", "La retourner", "beach_intimate_water", 1, "playful"),
                    StoryChoice("kiss", "Pull her into a kiss", "L'attirer dans un baiser", "beach_water_kiss", 2, "romantic")
                ]
            ),
            "beach_romantic_end": StoryBeat(
                id="beach_romantic_end",
                stage=StoryStage.ENDING,
                description="A beautiful sunset ending.",
                description_fr="Une belle fin au coucher de soleil.",
                ai_dialogue="*sits between your legs watching sunset* *leans back against your chest* This was the perfect day... *turns head to kiss you softly* Thank you for this... for everything... I love being with you.",
                ai_dialogue_fr="*assise entre tes jambes regardant le coucher de soleil* *se penche contre ta poitrine* C'etait la journee parfaite... *tourne la tete pour t'embrasser doucement* Merci pour ca... pour tout... j'adore etre avec toi.",
                image_prompt="couple sitting on beach watching sunset, woman leaning against man, romantic silhouette, golden hour, peaceful",
                is_ending=True,
                ending_type="romantic",
                choices=[]
            ),
            "beach_water_ending": StoryBeat(
                id="beach_water_ending",
                stage=StoryStage.ENDING,
                description="Passion in the ocean.",
                description_fr="Passion dans l'ocean.",
                ai_dialogue="*moans into your ear* Yes... right here... *wraps tighter around you* The waves... so good... *cries out* Don't stop... I'm so close...",
                ai_dialogue_fr="*gemit dans ton oreille* Oui... ici... *s'accroche plus fort a toi* Les vagues... c'est si bon... *crie* N'arrete pas... je suis si proche...",
                nsfw_level=3,
                is_ending=True,
                ending_type="sexual",
                choices=[]
            ),
            "beach_topless": StoryBeat(
                id="beach_topless",
                stage=StoryStage.RISING,
                description="She considers going topless.",
                description_fr="Elle considere aller topless.",
                ai_dialogue="*looks around* Well... we are alone... *slowly unties top* *lets it fall* *stands proudly* Like what you see? *smirks* Your turn to be underdressed...",
                ai_dialogue_fr="*regarde autour* Eh bien... on est seuls... *defait lentement le haut* *le laisse tomber* *se tient fierement* Tu aimes ce que tu vois? *sourit* A ton tour d'etre deshabille...",
                nsfw_level=2,
                image_prompt="woman at secluded beach, topless, confident pose, sunny day, seductive smile",
                choices=[
                    StoryChoice("join", "Join her", "La rejoindre", "beach_private", 3, "sexual"),
                    StoryChoice("tease", "Tease her first", "La taquiner d'abord", "beach_tease", 2, "sexual")
                ]
            ),
            "beach_close": StoryBeat(
                id="beach_close",
                stage=StoryStage.RISING,
                description="You get closer to inspect.",
                description_fr="Tu t'approches pour inspecter.",
                ai_dialogue="*giggles as you approach* *puts hands on your chest* See something you like? *traces her fingers down* Maybe you should help me... adjust it... *bites lip*",
                ai_dialogue_fr="*rigole quand tu t'approches* *met ses mains sur ta poitrine* Tu vois quelque chose qui te plait? *trace ses doigts* Peut-etre que tu devrais m'aider... a l'ajuster... *se mord la levre*",
                nsfw_level=2,
                choices=[
                    StoryChoice("adjust", "Help her adjust", "L'aider a ajuster", "beach_topless", 2, "sexual"),
                    StoryChoice("sunscreen", "Suggest sunscreen instead", "Suggerer la creme solaire", "beach_sunscreen", 1, "romantic")
                ]
            ),
            "beach_risky": StoryBeat(
                id="beach_risky",
                stage=StoryStage.RESOLUTION,
                description="Taking a risk right on the beach.",
                description_fr="Prendre un risque sur la plage.",
                ai_dialogue="*pulls you down onto towel* I don't care if someone sees... *removes bikini bottom* I need you now... *pulls you on top* Take me...",
                ai_dialogue_fr="*te tire sur la serviette* Je m'en fiche si quelqu'un voit... *enleve le bas du bikini* J'ai besoin de toi maintenant... *te tire sur elle* Prends-moi...",
                nsfw_level=3,
                is_ending=True,
                ending_type="sexual",
                choices=[]
            )
        }
    )
}


class StoryModeService:
    """Service for managing story mode interactions"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.scenarios = SCENARIOS
        self.active_sessions: Dict[str, StorySession] = {}

        # Try Redis for persistence
        self.redis_client = None
        try:
            import redis
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            print("[StoryMode] Redis connected")
        except Exception as e:
            print(f"[StoryMode] Redis not available: {e}")

        print(f"[StoryMode] Initialized with {len(self.scenarios)} scenarios")

    def get_available_scenarios(self, language: str = "en") -> List[Dict]:
        """Get list of available scenarios"""
        scenarios = []
        for scenario in self.scenarios.values():
            scenarios.append({
                "id": scenario.id,
                "title": scenario.title_fr if language == "fr" else scenario.title,
                "description": scenario.description_fr if language == "fr" else scenario.description,
                "mood": scenario.mood,
                "nsfw_max_level": scenario.nsfw_max_level
            })
        return scenarios

    def start_scenario(
        self,
        scenario_id: str,
        character_id: int,
        session_id: Optional[str] = None
    ) -> Optional[Dict]:
        """Start a new story session"""
        scenario = self.scenarios.get(scenario_id)
        if not scenario:
            return None

        # Generate session ID
        if not session_id:
            session_id = f"story_{character_id}_{scenario_id}_{int(datetime.now().timestamp())}"

        # Create session
        session = StorySession(
            session_id=session_id,
            scenario_id=scenario_id,
            character_id=character_id,
            current_beat_id=scenario.starting_beat,
            history=[scenario.starting_beat],
            choices_made=[],
            current_nsfw_level=0,
            started_at=datetime.now().isoformat(),
            images_generated=[]
        )

        # Store session
        self.active_sessions[session_id] = session
        self._save_session(session)

        # Get first beat
        first_beat = scenario.beats[scenario.starting_beat]

        return self._format_beat_response(scenario, first_beat, session)

    def make_choice(
        self,
        session_id: str,
        choice_id: str,
        language: str = "en"
    ) -> Optional[Dict]:
        """Process a player's choice"""
        session = self._get_session(session_id)
        if not session:
            return None

        scenario = self.scenarios.get(session.scenario_id)
        if not scenario:
            return None

        current_beat = scenario.beats.get(session.current_beat_id)
        if not current_beat:
            return None

        # Find the chosen choice
        chosen = None
        for choice in current_beat.choices:
            if choice.id == choice_id:
                chosen = choice
                break

        if not chosen:
            return None

        # Record choice
        session.choices_made.append((session.current_beat_id, choice_id))

        # Update NSFW level
        session.current_nsfw_level = max(session.current_nsfw_level, chosen.nsfw_level)

        # Move to next beat
        next_beat = scenario.beats.get(chosen.leads_to)
        if not next_beat:
            return None

        session.current_beat_id = chosen.leads_to
        session.history.append(chosen.leads_to)

        # Save session
        self._save_session(session)

        return self._format_beat_response(scenario, next_beat, session, language)

    def _format_beat_response(
        self,
        scenario: Scenario,
        beat: StoryBeat,
        session: StorySession,
        language: str = "en"
    ) -> Dict:
        """Format a beat for API response"""
        is_french = language == "fr"

        response = {
            "session_id": session.session_id,
            "scenario": {
                "id": scenario.id,
                "title": scenario.title_fr if is_french else scenario.title,
                "setting": scenario.setting
            },
            "beat": {
                "id": beat.id,
                "stage": beat.stage.value,
                "description": beat.description_fr if is_french else beat.description,
                "dialogue": beat.ai_dialogue_fr if is_french else beat.ai_dialogue,
                "nsfw_level": beat.nsfw_level,
                "is_ending": beat.is_ending,
                "ending_type": beat.ending_type
            },
            "choices": [
                {
                    "id": c.id,
                    "text": c.text_fr if is_french else c.text,
                    "nsfw_level": c.nsfw_level
                }
                for c in beat.choices
            ],
            "image_prompt": beat.image_prompt,
            "session_nsfw_level": session.current_nsfw_level,
            "history_length": len(session.history)
        }

        return response

    def get_session_state(self, session_id: str) -> Optional[Dict]:
        """Get current session state"""
        session = self._get_session(session_id)
        if not session:
            return None

        scenario = self.scenarios.get(session.scenario_id)
        if not scenario:
            return None

        current_beat = scenario.beats.get(session.current_beat_id)
        if not current_beat:
            return None

        return self._format_beat_response(scenario, current_beat, session)

    def _get_session(self, session_id: str) -> Optional[StorySession]:
        """Get session from cache or Redis"""
        # Check memory cache
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]

        # Check Redis
        if self.redis_client:
            try:
                key = f"casdy:story:{session_id}"
                data = self.redis_client.get(key)
                if data:
                    session_dict = json.loads(data)
                    session = StorySession(**session_dict)
                    self.active_sessions[session_id] = session
                    return session
            except Exception as e:
                print(f"[StoryMode] Redis load error: {e}")

        return None

    def _save_session(self, session: StorySession):
        """Save session to Redis"""
        if self.redis_client:
            try:
                key = f"casdy:story:{session.session_id}"
                self.redis_client.set(key, json.dumps(session.to_dict()), ex=86400)  # 24h TTL
            except Exception as e:
                print(f"[StoryMode] Redis save error: {e}")

    def end_session(self, session_id: str) -> bool:
        """End and clean up a session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

        if self.redis_client:
            try:
                self.redis_client.delete(f"casdy:story:{session_id}")
            except Exception:
                pass

        return True

    def get_scenario_summary(self, scenario_id: str, language: str = "en") -> Optional[Dict]:
        """Get detailed scenario info for preview"""
        scenario = self.scenarios.get(scenario_id)
        if not scenario:
            return None

        is_french = language == "fr"

        # Count endings
        endings = [b for b in scenario.beats.values() if b.is_ending]
        ending_types = set(b.ending_type for b in endings if b.ending_type)

        return {
            "id": scenario.id,
            "title": scenario.title_fr if is_french else scenario.title,
            "description": scenario.description_fr if is_french else scenario.description,
            "setting": scenario.setting,
            "mood": scenario.mood,
            "nsfw_max_level": scenario.nsfw_max_level,
            "total_beats": len(scenario.beats),
            "total_endings": len(endings),
            "ending_types": list(ending_types)
        }


# Global instance
story_mode = StoryModeService()
