#!/usr/bin/env python3
"""
Script de configuration de l'Assistant IA pour FactureApp
Exécutez ce script pour configurer votre clé API OpenAI
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Afficher un titre formaté"""
    print("\n" + "=" * 50)
    print(f"  {text}")
    print("=" * 50 + "\n")


def setup_env_file():
    """Créer un fichier .env avec la configuration"""
    print_header("Configuration du fichier .env")
    
    print("Option 1: Créer un fichier .env (recommandé)")
    print("Option 2: Utiliser des variables d'environnement Windows")
    choice = input("\nChoisir (1 ou 2): ").strip()
    
    if choice != "1" and choice != "2":
        print("❌ Choix invalide!")
        return False
    
    # Obtenir la clé API
    print("\n📋 Vous avez besoin d'une clé API OpenAI")
    print("Allez sur: https://platform.openai.com/api-keys")
    print("Cliquez sur 'Create new secret key' et copiez-la (format: sk-...)\n")
    
    api_key = input("Entrez votre clé API (sk-...): ").strip()
    
    if not api_key:
        print("❌ Clé API vide!")
        return False
    
    if not api_key.startswith("sk-"):
        print("⚠️  La clé ne commence pas par 'sk-'")
        confirm = input("Continuer quand même? (o/n): ").strip().lower()
        if confirm != "o":
            print("❌ Configuration annulée.")
            return False
    
    if choice == "1":
        return setup_env_file_method(api_key)
    else:
        return setup_windows_env(api_key)


def setup_env_file_method(api_key):
    """Créer un fichier .env"""
    env_content = f"""# Configuration de l'Assistant IA pour FactureApp
# Ce fichier contient les paramètres de l'API OpenAI

# Fournisseur d'IA (openai, ollama, local, etc.)
AI_PROVIDER=openai

# Clé API d'authentification
AI_API_KEY={api_key}

# Modèle à utiliser
AI_MODEL=gpt-4o-mini

# Température (0.0 = déterministe, 1.0 = créatif)
AI_TEMPERATURE=0.4

# Nombre maximum de tokens par réponse
AI_MAX_TOKENS=300

# Activer le chat IA
AI_CHAT_ENABLED=True

# (Optionnel) URL personnalisée de l'API
# AI_API_BASE=https://api.openai.com/v1/chat/completions
"""
    
    env_path = Path(".env")
    
    if env_path.exists():
        print(f"\n⚠️  Le fichier .env existe déjà!")
        overwrite = input("Le remplacer? (o/n): ").strip().lower()
        if overwrite != "o":
            print("❌ Fichier .env conservé.")
            return False
    
    env_path.write_text(env_content)
    print(f"\n✅ Fichier .env créé avec succès!")
    print(f"   Chemin: {env_path.absolute()}\n")
    
    # Ajouter .env à .gitignore
    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        content = gitignore_path.read_text()
        if ".env" not in content:
            gitignore_path.write_text(content + "\n.env\n")
            print("✅ Ajouté .env à .gitignore")
    else:
        gitignore_path.write_text(".env\n")
        print("✅ Créé .gitignore avec .env")
    
    return True


def setup_windows_env(api_key):
    """Configurer les variables d'environnement Windows"""
    print_header("Configuration des variables d'environnement Windows")
    
    env_vars = {
        "AI_PROVIDER": "openai",
        "AI_API_KEY": api_key,
        "AI_MODEL": "gpt-4o-mini",
        "AI_TEMPERATURE": "0.4",
        "AI_MAX_TOKENS": "300",
        "AI_CHAT_ENABLED": "True",
    }
    
    print("Configuration des variables d'environnement Windows...\n")
    
    for key, value in env_vars.items():
        try:
            # Utiliser setx pour définir les variables de façon persistente
            if key == "AI_API_KEY":
                # Masquer la clé dans les logs
                print(f"  ✓ {key} = [***caché pour sécurité***]")
            else:
                print(f"  ✓ {key} = {value}")
            
            # Définir la variable d'environnement
            subprocess.run(
                ["setx", key, value],
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors de la configuration de {key}")
            print(f"   {e}")
            return False
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    print("\n✅ Variables d'environnement configurées!")
    return True


def verify_setup():
    """Vérifier que la configuration est correcte"""
    print_header("Vérification de la configuration")
    
    try:
        from django.conf import settings
        
        print(f"AI_PROVIDER: {settings.AI_PROVIDER}")
        print(f"AI_MODEL: {settings.AI_MODEL}")
        print(f"AI_TEMPERATURE: {settings.AI_TEMPERATURE}")
        print(f"AI_MAX_TOKENS: {settings.AI_MAX_TOKENS}")
        print(f"AI_CHAT_ENABLED: {settings.AI_CHAT_ENABLED}")
        print(f"AI_API_KEY configurée: {bool(settings.AI_API_KEY)}")
        
        if settings.AI_API_KEY and settings.AI_PROVIDER != "local":
            print("\n✅ Configuration prête pour l'IA réelle!")
            return True
        else:
            print("\n⚠️  Mode local (pas de clé API configurée)")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False


def show_next_steps():
    """Afficher les prochaines étapes"""
    print_header("Prochaines étapes")
    
    print("""
1. 🔄 REDÉMARRER le serveur Django:
   - Arrêter le serveur actuel (Ctrl+C)
   - Exécuter: python manage.py runserver

2. 🌐 Ouvrir l'interface du chat:
   - http://127.0.0.1:8000/assistant/

3. 💬 Tester le chat:
   - Envoyer un message
   - L'IA réelle devrait répondre au lieu des réponses locales

4. ⚠️  Important sur Windows:
   - Redémarrer PowerShell/CMD après setx
   - Ou redémarrer l'ordinateur pour appliquer les changements système

📚 Documentation:
   - OpenAI API: https://platform.openai.com/docs
   - Pricing: https://openai.com/api/pricing
   - Models: https://platform.openai.com/docs/models
    """)


def main():
    """Fonction principale"""
    print_header("Configuration de l'Assistant IA FactureApp")
    
    print("""
Bienvenue! Ce script configure votre assistant IA pour utiliser OpenAI.

Le chat fonctionne actuellement en MODE LOCAL (réponses pré-programmées).
Avec votre clé API, il utilisera un vrai modèle d'IA pour des réponses plus intelligentes.
    """)
    
    # Configuration
    if not setup_env_file():
        print("\n❌ Configuration annulée.")
        sys.exit(1)
    
    # Vérification
    print("\n⏳ Vérification de la configuration...")
    verify_setup()
    
    # Prochaines étapes
    show_next_steps()
    
    print("\n✨ Configuration terminée! Bonne utilisation! 🚀\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Configuration annulée par l'utilisateur.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        sys.exit(1)
