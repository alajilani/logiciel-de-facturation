@echo off
REM Configuration d'Assistant IA pour FactureApp
REM Ce script configure les variables d'environnement OpenAI

echo.
echo =========================================
echo  Configuration de l'Assistant IA
echo =========================================
echo.

REM Demander la clé API
echo Vous avez besoin d'une clé API OpenAI
echo Allez sur: https://platform.openai.com/api-keys
echo.
set /p API_KEY="Entrez votre clé API (sk-...): "

if "%API_KEY%"=="" (
    echo Erreur: Clé API vide!
    pause
    exit /b 1
)

REM Valider le format
if not "%API_KEY:~0,3%"=="sk-" (
    echo Attention: La clé devrait commencer par "sk-"
    set /p CONFIRM="Continuer quand même? (O/N): "
    if /i not "%CONFIRM%"=="O" (
        echo Configuration annulée.
        pause
        exit /b 1
    )
)

echo.
echo Configuration des variables d'environnement...

REM Définir les variables d'environnement utilisateur (persistent)
setx AI_PROVIDER openai
setx AI_API_KEY %API_KEY%
setx AI_MODEL gpt-4o-mini
setx AI_TEMPERATURE 0.4
setx AI_MAX_TOKENS 300
setx AI_CHAT_ENABLED True

echo.
echo =========================================
echo  ✅ Configuration réussie!
echo =========================================
echo.
echo Variables d'environnement définies:
echo   - AI_PROVIDER: openai
echo   - AI_API_KEY: [caché pour sécurité]
echo   - AI_MODEL: gpt-4o-mini
echo   - AI_TEMPERATURE: 0.4
echo   - AI_MAX_TOKENS: 300
echo   - AI_CHAT_ENABLED: True
echo.
echo Redémarrez le serveur Django pour appliquer les changements:
echo   1. Arrêter le serveur (Ctrl+C)
echo   2. Exécuter: python manage.py runserver
echo   3. Aller à: http://127.0.0.1:8000/assistant/
echo.
echo ⚠️  IMPORTANT: Redémarrez PowerShell/CMD pour que les changements s'appliquent!
echo.
pause
