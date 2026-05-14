# 🚀 Guide de Configuration Rapide - Assistant IA FactureApp

## 📱 Statut Actuel

L'application a **deux modes de fonctionnement**:

### ✅ Mode Local (Actuellement Actif)
- ✓ Fonctionne sans API externe
- ✓ Réponses pré-programmées rapides
- ✓ Pas de coûts
- ✗ Réponses limitées aux cas pré-définis

### 🚀 Mode OpenAI (À Configurer)
- ✓ Vrai modèle d'IA (GPT-4o-mini)
- ✓ Réponses intelligentes et personnalisées
- ✓ Peut répondre à n'importe quelle question
- ✗ Nécessite une clé API (gratuit pour essais)
- ✗ Coûts minimes en production

---

## 🔧 Configuration en 3 Étapes

### Étape 1️⃣ : Obtenir une Clé API OpenAI

1. **Aller sur**: https://platform.openai.com/api-keys
2. **Se connecter** (créer compte si nécessaire)
3. **Créer une nouvelle clé**: "Create new secret key"
4. **Copier la clé** (format: `sk-...`)
5. **Ne pas fermer la page** - elle ne s'affichera qu'une fois!

### Étape 2️⃣ : Exécuter le Script de Configuration

**Option A - Script Python (Recommandé)**:
```bash
python setup_ai.py
```
Puis entrer votre clé API quand demandé.

**Option B - Script Windows Batch**:
```bash
setup-ai.bat
```
Puis entrer votre clé API quand demandé.

**Option C - Manuel (Utilisateurs Avancés)**:
```powershell
# PowerShell (en tant qu'administrateur)
setx AI_PROVIDER openai
setx AI_API_KEY "sk-YOUR-KEY-HERE"
setx AI_MODEL gpt-4o-mini
```

### Étape 3️⃣ : Redémarrer le Serveur

```bash
# 1. Arrêter le serveur (Ctrl+C dans PowerShell)
# 2. Redémarrer PowerShell/CMD
# 3. Relancer le serveur:
python manage.py runserver
```

---

## ✨ Vérifier la Configuration

1. **Ouvrir**: http://127.0.0.1:8000/assistant/
2. **Observer la barre d'en-tête**:
   - 🟢 Badge **vert** "⚡ OpenAI GPT" = Configuration réussie
   - 🟡 Badge **jaune** "💡 Mode Local" = Pas d'API configurée

3. **Envoyer un message** dans le chat:
   - Chaque message affichera: `Mode: openai` ou `Mode: local`
   - Si réponse vient d'OpenAI = Configuration fonctionnelle ✅

---

## 📊 Modèles Disponibles

### OpenAI (Recommandé)
- **gpt-4o-mini** - Rapide, bon qualité, ~$0.15 par 1M tokens
- **gpt-4o** - Plus puissant, ~$5 par 1M tokens
- **gpt-3.5-turbo** - Plus ancien, ~$0.50 par 1M tokens

### Ollama (Gratuit, Local, Sans API)
```bash
# Installer: https://ollama.ai
# Configurer:
AI_PROVIDER=ollama
AI_API_BASE=http://localhost:11434/v1/chat/completions
AI_MODEL=llama2
AI_API_KEY=ollama
```

---

## 💰 Coûts Estimés

**Pour 1000 messages** avec `gpt-4o-mini`:
- Environ **$0.30 à $0.50**
- C'est **gratuit les 3 premiers mois** avec crédit OpenAI
- Après: **Pay-as-you-go**

---

## 🔐 Sécurité

⚠️ **IMPORTANT**:
- ❌ Ne jamais commiter votre clé dans Git
- ❌ Ne pas la partager
- ✅ Ajouter `.env` à `.gitignore`
- ✅ Utiliser des variables d'environnement système

Vérifier `.gitignore`:
```bash
cat .gitignore  # Doit contenir: .env
```

---

## 🐛 Dépannage

### Badge reste "Mode Local"
→ Redémarrer le serveur Django (`Ctrl+C` puis `python manage.py runserver`)
→ Vérifier les variables d'environnement: `echo %AI_PROVIDER%`

### Messages d'erreur API
→ Vérifier la clé (commence par `sk-`)
→ Vérifier la connexion Internet
→ Consulter: https://status.openai.com

### Pas de réponse
→ Attendre 12 secondes (timeout par défaut)
→ Vérifier les logs serveur pour erreurs

---

## 📚 Fichiers Utiles

- **`AI_SETUP.md`** - Guide détaillé de configuration
- **`setup_ai.py`** - Script Python de configuration
- **`setup-ai.bat`** - Script Windows de configuration
- **`.env.example`** - Exemple de configuration
- **`invoice_app/ai_assistant.py`** - Logique IA backend
- **`invoice_app/templates/invoice_app/ai_assistant.html`** - Interface chat

---

## 🎯 Prochaines Étapes

Après configuration:
1. ✅ Tester le chat avec des questions
2. ✅ Vérifier les réponses intelligentes
3. ✅ Paramétrer le modèle selon vos besoins
4. ✅ Déployer en production

---

## 📞 Ressources

- **OpenAI Docs**: https://platform.openai.com/docs
- **Pricing**: https://openai.com/api/pricing
- **Status**: https://status.openai.com
- **Models**: https://platform.openai.com/docs/models

---

**Besoin d'aide?** Consultez `AI_SETUP.md` pour plus de détails! 🚀
