"""AI assistant helpers for the invoice application - IMPROVED VERSION.

The assistant uses a fast local fallback by default and can optionally call an
OpenAI-compatible API when `AI_PROVIDER` and `AI_API_KEY` are configured.
This improved version has better fallback responses and context awareness.
"""

from __future__ import annotations

import json
import re
import random
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


def _recent_messages(history: Iterable[dict], limit: int = 6):
    messages = list(history or [])
    return messages[-limit:]


def _local_reply(message: str) -> str:
    """Generate intelligent local responses to user messages.
    
    Provides helpful, context-aware responses for common queries about
    invoices, quotes, clients, payments, and more. Includes friendly
    emojis and encourages further interaction.
    """
    normalized = _normalize(message)

    if not normalized:
        return "Bonjour! 👋 Je suis ton assistant IA pour la facturation. Pose-moi n'importe quelle question!"

    # Greetings and casual conversation - respond warmly
    if any(word in normalized for word in ["bonjour", "salut", "hello", "coucou", "ça va", "comment allez"]):
        greetings = [
            "Bonjour! 👋 Comment puis-je t'aider avec tes factures aujourd'hui?",
            "Salut! 😊 Je suis là pour t'assister. Qu'as-tu besoin?",
            "Hello! ✨ Prêt à optimiser ta gestion de facturation?",
            "Coucou! 🎯 Raconte-moi, comment je peux t'aider?",
            "Bonjour! 👋 Bienvenue! Je peux t'aider avec tout ce qui concerne tes factures."
        ]
        return random.choice(greetings)

    # Invoice-related keywords
    if any(word in normalized for word in ["facture", "invoice", "numéro", "montant", "total", "htc", "ttc", "ht"]):
        return (
            "📄 Pour les factures, tu peux:\n"
            "✅ Créer de nouvelles factures\n"
            "✅ Modifier et personnaliser\n"
            "✅ Exporter en PDF\n"
            "✅ Envoyer par email\n"
            "✅ Suivre les paiements\n"
            "Que veux-tu faire exactement?"
        )

    # Quote/Devis-related keywords
    if any(word in normalized for word in ["devis", "quote", "estimation", "proposition", "tarif"]):
        return (
            "📋 Concernant les devis:\n"
            "✅ Créer et modifier des devis\n"
            "✅ Envoyer au client\n"
            "✅ Convertir en facture\n"
            "✅ Suivre l'acceptation\n"
            "Je peux te guider étape par étape!"
        )

    # Email and communication
    if any(word in normalized for word in ["email", "mail", "smtp", "envoi", "envoyer", "notification"]):
        return (
            "📧 Système d'email et notifications:\n"
            "✅ Envoyer les factures par email\n"
            "✅ Notifications temps réel\n"
            "✅ Rappels de paiement\n"
            "✅ Alertes système\n"
            "Besoin d'aide pour configurer?"
        )

    # Client management
    if any(word in normalized for word in ["client", "customer", "contact", "entreprise", "societe"]):
        return (
            "👥 Gestion des clients:\n"
            "✅ Ajouter des clients\n"
            "✅ Consulter leur historique\n"
            "✅ Gérer les coordonnées\n"
            "✅ Analyser les paiements\n"
            "Quel client cherches-tu?"
        )

    # Product management
    if any(word in normalized for word in ["produit", "product", "article", "stock", "inventory"]):
        return (
            "🛍️ Gestion des produits et stock:\n"
            "✅ Ajouter des produits\n"
            "✅ Gérer les quantités\n"
            "✅ Suivre les niveaux\n"
            "✅ Alertes de rupture\n"
            "Dis-moi ce que tu veux faire!"
        )

    # Payment tracking
    if any(word in normalized for word in ["paiement", "payment", "payé", "encaissement", "recouvrement", "trésorerie"]):
        return (
            "💰 Suivi des paiements:\n"
            "✅ Enregistrer les paiements reçus\n"
            "✅ Voir les factures impayées\n"
            "✅ Générer des relances\n"
            "✅ Analyser la trésorerie\n"
            "Besoin d'aide pour suivre un paiement?"
        )

    # Analytics and reports
    if any(word in normalized for word in ["analyse", "analytics", "rapport", "report", "statistique", "graphique", "chiffre"]):
        return (
            "📊 Analyses et rapports:\n"
            "✅ Chiffre d'affaires par période\n"
            "✅ Clients les plus importants\n"
            "✅ Tendances de vente\n"
            "✅ Prévisions\n"
            "Quel type de rapport tu cherches?"
        )

    # Dashboard and navigation
    if any(word in normalized for word in ["tableau", "dashboard", "accueil", "interface", "page", "vue"]):
        return (
            "🎯 Navigation et tableau de bord:\n"
            "✅ Vue d'ensemble des chiffres clés\n"
            "✅ Actions rapides\n"
            "✅ Dernières factures\n"
            "✅ Alertes importantes\n"
            "Veux-tu que je t'aide à naviguer?"
        )

    # Settings and configuration
    if any(word in normalized for word in ["config", "parametr", "setting", "logo", "couleur", "theme", "preference"]):
        return (
            "⚙️ Configuration et personnalisation:\n"
            "✅ Informations de l'entreprise\n"
            "✅ Logo et branding\n"
            "✅ Modèles d'emails\n"
            "✅ Préférences\n"
            "Qu'aimerais-tu configurer?"
        )

    # Generic helpful responses
    fallback_responses = [
        "Intéressant! 💡 Dis-moi plus précisément et je t'aiderai vraiment.",
        "Bien sûr! 👍 Détaille ta demande pour que je puisse vraiment t'aider.",
        "Je suis là! ✨ Raconte-moi exactement ce que tu veux faire.",
        "Très bien! 🎯 Explique-moi ton besoin et on trouvera la solution.",
        "Je peux t'aider! 🚀 Dis-moi tout!",
        "C'est une bonne question! 🤔 Peux-tu être plus spécifique?",
        "Je comprends! 📝 Raconte-moi plus pour que je puisse vraiment t'assister.",
        "Super! ⚡ Je vais faire de mon mieux pour t'aider. Dis m'en plus!"
    ]
    return random.choice(fallback_responses)


def _remote_reply(message: str, history: Iterable[dict] | None = None) -> str:
    payload = {
        "model": settings.AI_MODEL,
        "temperature": settings.AI_TEMPERATURE,
        "max_tokens": settings.AI_MAX_TOKENS,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Tu es l'assistant IA de l'application de facturation FactureApp. "
                    "Réponds en français, avec des réponses courtes, utiles, rapides et naturelles. "
                    "Tu es amical, aidant et professionnel. Utilise des emojis pour rendre les réponses plus attrayantes. "
                    "Tu peux aider sur: factures, devis, clients, paiements, emails, notifications, rapports, configuration. "
                    "Sois enthousiaste et encourageant dans tes réponses."
                ),
            },
        ] + _recent_messages(history or [], limit=6) + [{"role": "user", "content": message}],
    }

    request = Request(
        settings.AI_API_BASE,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.AI_API_KEY}",
        },
        method="POST",
    )

    with urlopen(request, timeout=12) as response:
        data = json.loads(response.read().decode("utf-8"))

    choices = data.get("choices") or []
    if not choices:
        raise ValueError("Empty AI response")

    return (choices[0].get("message") or {}).get("content", "").strip() or _local_reply(message)


def generate_ai_reply(message: str, history: Iterable[dict] | None = None) -> dict:
    """Return a quick assistant reply, optionally using a remote AI provider.
    
    First tries to use OpenAI (if configured), falls back to local intelligent
    responses, which handle common queries and provide helpful guidance.
    """

    if settings.AI_CHAT_ENABLED and settings.AI_PROVIDER != 'local' and settings.AI_API_KEY:
        try:
            reply = _remote_reply(message, history=history)
            return {"reply": reply, "mode": settings.AI_PROVIDER}
        except (HTTPError, URLError, TimeoutError, ValueError, OSError):
            pass

    return {"reply": _local_reply(message), "mode": "local"}
