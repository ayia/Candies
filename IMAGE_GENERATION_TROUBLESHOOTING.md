# 🔧 Guide de Dépannage - Génération d'Images

## 🚨 Problème Actuel

**Erreur** : `_ssl.c:983: The handshake operation timed out`

Tous les espaces Hugging Face (Heartsync/Adult, Heartsync/NSFW-Uncensored-photo, Heartsync/NSFW-image) rencontrent des timeouts SSL lors de la connexion via `gradio_client`.

### Diagnostic Effectué

```bash
python backend/test_image_spaces.py
```

**Résultats** :
- ✅ Les espaces sont **RUNNING** (actifs)
- ✅ L'API HuggingFace répond correctement
- ❌ Les connexions `GradioClient` timeout après 10-30 secondes
- ❌ Erreur d'encodage sur Windows : `'charmap' codec can't encode character '\u2714'`

## 🔍 Causes Possibles

### 1. **Problème Réseau**
- Firewall bloquant les connexions sortantes
- Proxy d'entreprise/école
- VPN interférant avec les connexions SSL
- FAI limitant les connexions à Hugging Face

### 2. **Limite de Quota Hugging Face**
- Les espaces gratuits ont des quotas
- Trop de requêtes en peu de temps
- Besoin d'un compte Pro HF

### 3. **Gradio Client Version**
- Version du client incompatible
- Bug connu avec SSL sur certains OS

## ✅ Solutions

### Solution 1 : Utiliser Novita AI (RECOMMANDÉ)

Novita AI offre une API stable sans les problèmes de timeout :

**1. Créer un compte gratuit** : https://novita.ai

**2. Obtenir une clé API** :
- Dashboard → API Keys → Create New Key
- Note: 100 crédits gratuits à l'inscription

**3. Configurer** :
```bash
# Dans .env
NOVITA_API_KEY=your_api_key_here
IMAGE_PROVIDER=novita
```

**4. Installer le SDK** :
```bash
pip install novita-client
```

**5. Créer un nouveau service d'images** (`backend/image_service_novita.py`) :
```python
import novita_client
from novita_client import NovitaClient, Txt2ImgRequest

class NovitaImageService:
    def __init__(self):
        self.client = NovitaClient(api_key=settings.NOVITA_API_KEY)

    async def generate(self, prompt, negative_prompt="", nsfw_level=0):
        request = Txt2ImgRequest(
            model_name="dreamshaperXL10_alpha2.safetensors",  # NSFW-friendly
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=1024,
            height=1024,
            steps=20,
            seed=-1,
            sampler_name="DPM++ 2M Karras"
        )

        response = await self.client.txt2img(request)
        return response.images[0]
```

**Avantages** :
- ✅ Pas de timeout
- ✅ Génération rapide (5-15 secondes)
- ✅ Plusieurs modèles NSFW disponibles
- ✅ API stable et documentée

**Coût** : ~0.02€ par image (100 crédits gratuits = ~5000 images)

---

### Solution 2 : Stable Diffusion Local (MEILLEUR pour production)

Installer Stable Diffusion en local pour un contrôle total :

**1. Installer AUTOMATIC1111 WebUI** :
```bash
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
cd stable-diffusion-webui
# Windows
webui-user.bat --api

# Linux/Mac
./webui.sh --api
```

**2. Télécharger un modèle NSFW** :
- https://civitai.com/models/4384/dreamshaper
- Placer le fichier `.safetensors` dans `models/Stable-diffusion/`

**3. Créer le service** (`backend/image_service_local.py`) :
```python
import requests
import base64

class LocalSD ImageService:
    def __init__(self):
        self.url = "http://localhost:7860"

    async def generate(self, prompt, negative_prompt=""):
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "steps": 20,
            "width": 1024,
            "height": 1024,
            "sampler_name": "DPM++ 2M Karras"
        }

        response = requests.post(f"{self.url}/sdapi/v1/txt2img", json=payload)
        r = response.json()

        # Décoder l'image base64
        image_data = base64.b64decode(r['images'][0])
        return image_data
```

**Avantages** :
- ✅ GRATUIT et illimité
- ✅ Aucune censure
- ✅ Vie privée totale
- ✅ Contrôle complet

**Inconvénients** :
- ❌ Nécessite GPU NVIDIA (GTX 1060 6GB minimum, RTX 3060 12GB recommandé)
- ❌ ~10GB d'espace disque
- ❌ Configuration initiale

---

### Solution 3 : Augmenter les Timeouts (Temporaire)

Si vous voulez continuer avec Hugging Face, augmentez les timeouts :

**1. Modifier `image_service.py`** :
```python
# Ligne ~220
client = GradioClient(space_name, hf_token=hf_token)
# Changer en :
client = GradioClient(space_name, hf_token=hf_token, max_workers=1, download_files=False)
client.timeout = 120  # 2 minutes au lieu de 30 secondes
```

**2. Utiliser un VPN** :
- Certains ISP limitent les connexions à HF
- Essayer avec un VPN (ProtonVPN gratuit)

**3. Visiter les espaces avant d'utiliser** :
```bash
# Ouvrir dans le navigateur pour les "réveiller"
start https://huggingface.co/spaces/Heartsync/Adult
start https://huggingface.co/spaces/Heartsync/NSFW-Uncensored-photo
start https://huggingface.co/spaces/Heartsync/NSFW-image

# Attendre 2-3 minutes puis réessayer
```

---

### Solution 4 : Stability AI API (Officiel)

**1. Créer un compte** : https://platform.stability.ai

**2. Obtenir clé API** : Dashboard → API Keys

**3. Installer** :
```bash
pip install stability-sdk
```

**4. Utiliser** :
```python
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation

stability_api = client.StabilityInference(
    key=os.environ['STABILITY_KEY'],
    verbose=True,
)

answers = stability_api.generate(
    prompt=prompt,
    steps=30,
    cfg_scale=7.0,
    width=1024,
    height=1024,
    samples=1,
)
```

**Coût** : ~$0.01 par image

---

## 🎯 Recommandation Finale

**Pour développement/tests** : Novita AI (Solution 1)
- Rapide à mettre en place
- Crédits gratuits
- Pas de GPU nécessaire

**Pour production** : Stable Diffusion Local (Solution 2)
- Zéro coût à long terme
- Contrôle total
- Meilleure performance avec bon GPU

**Pour MVP rapide** : Stability AI (Solution 4)
- API officielle
- Qualité garantie
- Pay-as-you-go

## 🔄 Migration Rapide vers Novita AI

Voici comment migrer en 10 minutes :

```bash
# 1. Installer
pip install novita-client

# 2. Ajouter dans .env
NOVITA_API_KEY=your_key_here

# 3. Créer backend/image_service_novita.py
# (voir code ci-dessus)

# 4. Modifier main.py
from image_service_novita import NovitaImageService
image_service = NovitaImageService()

# 5. Tester
python backend/test_novita.py
```

## 📞 Support

Si aucune solution ne fonctionne :
1. Vérifiez votre connexion internet
2. Désactivez firewall/antivirus temporairement
3. Essayez depuis un autre réseau
4. Contactez votre FAI pour vérifier les restrictions

---

**Dernière mise à jour** : 09/01/2026
**Status** : HuggingFace Spaces - SSL Timeout confirmé
