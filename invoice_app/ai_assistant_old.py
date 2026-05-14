"""AI assistant helpers for the invoice application.

The assistant uses a fast local fallback by default and can optionally call an
OpenAI-compatible API when `AI_PROVIDER` and `AI_API_KEY` are configured.
"""

from __future__ import annotations

import json
import re
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
    normalized = _normalize(message)

    if not normalized:
        return (
            "Je suis prêt. Pose-moi une question sur les factures, les devis, les clients, "
            "les paiements, les notifications ou la configuration du projet."
        )

    if any(word in normalized for word in ["bonjour", "salut", "hello", "coucou"]):
        return (
            "Bonjour. Je peux t’aider rapidement sur les factures, devis, emails, notifications et le projet. "
            "Dis-moi exactement ce que tu veux faire."
        )

    if any(word in normalized for word in ["facture", "invoice"]):
        return (
            "Pour une facture, tu peux déjà la créer, ajouter les lignes, exporter en PDF, l’envoyer par email "
            "et enregistrer les paiements. Si tu veux, je peux te guider étape par étape."
        )

    if any(word in normalized for word in ["devis", "quote"]):
        return (
            "Pour un devis, le projet permet déjà la création, l’édition, l’envoi par email et la conversion en facture. "
            "Je peux aussi t’expliquer comment l’utiliser proprement."
        )

    if any(word in normalized for word in ["email", "mail", "smtp"]):
        return (
            "L’email est prêt côté projet: en local il passe en console, et en production tu peux brancher un vrai SMTP "
            "via les variables d’environnement."
        )

    if any(word in normalized for word in ["notification", "alert"]):
        return (
            "Les notifications temps réel sont déjà branchées dans le projet. Tu peux les consulter, les marquer comme lues "
            "ou les rejeter depuis l’interface."
        )

    if any(word in normalized for word in ["logo", "branding"]):
        return (
            "Le logo de l’application peut être affiché dans la barre du haut, l’admin et l’écran de connexion. "
            "Je peux aussi te proposer une version encore plus personnalisée si tu veux."
        )

    if any(word in normalized for word in ["stock", "inventory"]):
        return (
            "La gestion de stock n’est pas encore finalisée dans le projet actuel. Je peux l’ajouter avec des produits "
            "stockés, des niveaux d’inventaire et des alertes de rupture."
        )

    if any(word in normalized for word in ["client portal", "portail client", "espace client"]):
        return (
            "Le portail client n’est pas encore complet. On peut le créer pour permettre à un client de consulter ses "
            "factures, devis et paiements avec une connexion dédiée."
        )

    if any(word in normalized for word in ["payment", "paiement", "stripe", "paypal"]):
        return (
            "Le suivi des paiements existe déjà, mais le paiement en ligne n’est pas encore branché. On peut l’ajouter ensuite "
            "avec Stripe ou PayPal."
        )

    return (
        "Je peux t’aider sur la facturation, les devis, les emails, les notifications, le tableau de bord, le logo et la configuration. "
        "Si tu veux une réponse précise, donne-moi la tâche exacte."
    )


def _remote_reply(message: str, history: Iterable[dict] | None = None) -> str:
    payload = {
        "model": settings.AI_MODEL,
        "temperature": settings.AI_TEMPERATURE,
        "max_tokens": settings.AI_MAX_TOKENS,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Tu es l'assistant de l'application de facturation. Réponds en français, avec des réponses courtes, utiles, rapides et naturelles."
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
    """Return a quick assistant reply, optionally using a remote AI provider."""

    if settings.AI_CHAT_ENABLED and settings.AI_PROVIDER != 'local' and settings.AI_API_KEY:
        try:
            reply = _remote_reply(message, history=history)
            return {"reply": reply, "mode": settings.AI_PROVIDER}
        except (HTTPError, URLError, TimeoutError, ValueError, OSError):
            pass

    return {"reply": _local_reply(message), "mode": "local"}