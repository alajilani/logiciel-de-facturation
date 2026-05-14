# Configuration de l'Assistant IA avec OpenAI

## 📋 Prérequis

Vous avez besoin d'une **clé API OpenAI** pour utiliser un vrai modèle d'IA au lieu des réponses locales.

### Obtenir une clé API OpenAI (gratuit pour les essais)

1. **Aller sur** https://platform.openai.com/api-keys
2. **Se connecter** avec un compte OpenAI (créer un compte si nécessaire)
3. **Créer une nouvelle clé**:
   - Cliquer sur "Create new secret key"
   - Copier la clé (elle ne s'affichera qu'une fois!)
   - Format: `sk-...`

## 🔧 Configuration sur Windows (PowerShell)

### Option 1: Variables d'environnement système (PERMANENT)

```powershell
# 1. Ouvrir PowerShell en tant que administrateur
# 2. Exécuter ces commandes:

[Environment]::SetEnvironmentVariable("AI_PROVIDER", "openai", "User")
[Environment]::SetEnvironmentVariable("AI_API_KEY", "sk-YOUR-KEY-HERE", "User")
[Environment]::SetEnvironmentVariable("AI_MODEL", "gpt-4o-mini", "User")

# Vérifier la configuration:
$env:AI_PROVIDER
$env:AI_API_KEY
$env:AI_MODEL
```

### Option 2: Fichier .env (RECOMMANDÉ pour développement)

Créer un fichier `.env` à la racine du projet:

```bash
# .env
AI_PROVIDER=openai
AI_API_KEY=sk-YOUR-KEY-HERE
AI_MODEL=gpt-4o-mini
AI_TEMPERATURE=0.4
AI_MAX_TOKENS=300
AI_CHAT_ENABLED=True
```

### Option 3: Variables d'environnement temporaires (SESSION COURANTE)

```powershell
$env:AI_PROVIDER = "openai"
$env:AI_API_KEY = "sk-YOUR-KEY-HERE"
$env:AI_MODEL = "gpt-4o-mini"

# Vérifier:
python manage.py shell
>>> from django.conf import settings
>>> print(settings.AI_API_KEY)
>>> print(settings.AI_PROVIDER)
```

## ✅ Vérifier la Configuration

```powershell
cd "C:\Users\slima\Downloads\Projet Soutenance\logiciel-de-facturation-main\logiciel-de-facturation-main"

python manage.py shell
```

```python
>>> from django.conf import settings
>>> print(f"AI_PROVIDER: {settings.AI_PROVIDER}")
>>> print(f"AI_MODEL: {settings.AI_MODEL}")
>>> print(f"AI_API_KEY set: {bool(settings.AI_API_KEY)}")
>>> print(f"AI_CHAT_ENABLED: {settings.AI_CHAT_ENABLED}")
```

## 🚀 Tester le Chat IA

1. **Redémarrer le serveur Django**:
```powershell
python manage.py runserver
```

2. **Ouvrir** http://127.0.0.1:8000/assistant/
3. **Envoyer un message**
4. Le chat devrait maintenant utiliser l'IA réelle au lieu des réponses locales

## 📊 Modèles Disponibles

### Modèles OpenAI économiques:
- `gpt-4o-mini` ✅ **RECOMMANDÉ** - Rapide, bon qualité, bon marché
- `gpt-4o` - Très puissant, plus coûteux
- `gpt-3.5-turbo` - Plus ancien, moins cher

### Autres Providers (compatible OpenAI API):

Pour utiliser d'autres fournisseurs (Ollama, LM Studio, Together AI, etc.):

```bash
# Exemple: Ollama local
AI_PROVIDER=ollama
AI_API_BASE=http://localhost:11434/v1/chat/completions
AI_API_KEY=ollama  # valeur quelconque
AI_MODEL=llama2
```

## 🔐 Sécurité

⚠️ **NE JAMAIS** commiter votre clé API dans Git!

1. Ajouter `.env` à `.gitignore`:
```bash
echo ".env" >> .gitignore
```

2. Utiliser des variables d'environnement système pour la production

## 💡 Astuce

Pour développement local **sans** API key (mode local rapide):
```bash
# Les réponses viennent de la fonction _local_reply()
AI_PROVIDER=local
AI_API_KEY=
```

Le chat fonctionne en mode hybride:
- ✅ Si `AI_API_KEY` est configuré → Utilise OpenAI
- ❌ Si erreur API → Retombe en mode local automatiquement
- ❌ Si pas de clé → Mode local uniquement

## 📞 Support

- **OpenAI Documentation**: https://platform.openai.com/docs/api-reference
- **OpenAI Pricing**: https://openai.com/api/pricing
- **Status**: https://status.openai.com
