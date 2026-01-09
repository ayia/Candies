# 🔑 Comment Obtenir une Clé API Together.ai GRATUITE

## Étapes Rapides (2 minutes)

### 1. Créer un Compte
👉 **Lien** : https://api.together.xyz/signup

- Utiliser votre email
- Ou connecter avec Google/GitHub

### 2. Récupérer votre Clé API
Après connexion :
1. Aller sur : https://api.together.xyz/settings/api-keys
2. Cliquer sur **"Create API Key"**
3. Copier la clé (commence par `together-...`)

### 3. Ajouter dans `.env`
Ouvrir le fichier `.env` à la racine du projet et ajouter :

```env
TOGETHER_API_KEY=together-votre_cle_ici
```

### 4. Tester FLUX Schnell
```bash
cd backend
python image_service_flux.py
```

---

## ✅ Avantages du Compte Gratuit

| Avantage | Détail |
|----------|--------|
| **Durée** | 3 mois gratuits |
| **Crédits** | Crédits initiaux offerts |
| **Rate Limit** | 6 images/minute |
| **Qualité** | ⭐⭐⭐⭐⭐ Midjourney-level |
| **NSFW** | ✅ Supporté |
| **Modèles** | FLUX.1 Schnell, Pro, Dev |

---

## 🎨 Pourquoi FLUX Schnell ?

**FLUX.1 [schnell]** est créé par **Black Forest Labs** - l'équipe qui a créé Stable Diffusion. C'est le **meilleur modèle photoréaliste gratuit** en 2026.

### Comparaison Visuelle

| Service | Photoréalisme | Exemple |
|---------|---------------|---------|
| **Pollinations** | ⭐⭐⭐⭐ | On voit que c'est de l'IA |
| **FLUX Schnell** | ⭐⭐⭐⭐⭐ | **Impossible de distinguer d'une vraie photo** |

---

## 🚀 Après Configuration

Une fois la clé ajoutée, le service sera automatiquement utilisé pour :
- ✅ Génération d'images de personnages
- ✅ Images photoréalistes indiscernables du réel
- ✅ NSFW haute qualité
- ✅ Génération rapide (5-10 secondes)

---

## 📞 Besoin d'Aide ?

Si vous avez des problèmes :
1. Vérifier que la clé commence bien par `together-`
2. Vérifier qu'il n'y a pas d'espaces avant/après dans `.env`
3. Relancer le backend : `python -m uvicorn main:app --reload`

---

**Liens Utiles** :
- Créer compte : https://api.together.xyz/signup
- API Keys : https://api.together.xyz/settings/api-keys
- Documentation : https://docs.together.ai/docs/image-models
- Modèles disponibles : https://www.together.ai/models
